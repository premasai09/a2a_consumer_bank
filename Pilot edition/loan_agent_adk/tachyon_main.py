import logging
import os
import uuid

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import create_agent
from tachyon_agent_executor import TachyonWellsFargoAgentExecutor
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


def main():
    """Starts the Tachyon-compatible agent server."""
    host = "localhost"
    port = 10002
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError(
                    "GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
                )

        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="process_credit_request",
            name="Process Credit Line Request",
            description="Processes credit line requests and generates competitive offers with ESG assessments.",
            tags=["banking", "credit", "esg", "finance"],
            examples=["Process a credit request for $500,000 for 24 months"],
        )
        agent_card = AgentCard(
            name="Wells Fargo Bank Agent",
            description="Wells Fargo Bank's AI agent for processing credit line requests with ESG integration.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=capabilities,
            skills=[skill],
        )

        adk_agent = create_agent()
        print(f"DEBUG: Created agent: {adk_agent}")
        runner = Runner(
            app_name=agent_card.name,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        print(f"DEBUG: Created runner: {runner}")
        agent_executor = TachyonWellsFargoAgentExecutor(runner)
        print(f"DEBUG: Created Tachyon agent executor: {agent_executor}")

        # Create task store
        task_store = InMemoryTaskStore()
        print(f"DEBUG: Created task store: {task_store}")
        
        # Create request handler with proper configuration
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=task_store,
        )
        print(f"DEBUG: Created request handler: {request_handler}")
        
        # Create A2A server with proper JSON-RPC configuration
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )
        print(f"DEBUG: Created A2A server with DefaultRequestHandler")
        
        # Build the application with proper configuration
        app = server.build(agent_card_url='/.well-known/agent-card.json')
        print("DEBUG: Built app with agent-card.json")
        
        # Add custom JSON-RPC handler for send_message method
        from starlette.responses import JSONResponse
        import json
        
        async def handle_jsonrpc(request):
            """Custom JSON-RPC handler for send_message method"""
            try:
                body = await request.body()
                data = json.loads(body)
                
                print(f"🎯 TACHYON JSON-RPC HANDLER: {data}")
                
                if data.get('method') == 'send_message':
                    # Extract message from params
                    params = data.get('params', {})
                    message = params.get('message', {})
                    
                    print(f"📨 Processing send_message: {message}")
                    
                    # Use the actual A2A request handler
                    try:
                        # Create a mock request context for the A2A handler
                        from a2a.server.agent_execution.context import RequestContext
                        from a2a.server.events.event_queue import EventQueue
                        from a2a.types import Part, TextPart
                        from google.genai import types
                        
                        # Extract task and context IDs
                        task_id = message.get('taskId', str(uuid.uuid4()))
                        context_id = message.get('contextId', str(uuid.uuid4()))
                        
                        # Create message parts
                        message_parts = []
                        if 'parts' in message:
                            for part in message['parts']:
                                if part.get('type') == 'text':
                                    message_parts.append(Part(root=TextPart(text=part['text'])))
                        
                        # Create request context
                        request_context = RequestContext(
                            task_id=task_id,
                            context_id=context_id,
                            message=types.UserContent(parts=message_parts) if message_parts else None
                        )
                        
                        # Create event queue
                        event_queue = EventQueue()
                        
                        # Execute the agent with timeout
                        import asyncio
                        await asyncio.wait_for(
                            agent_executor.execute(request_context, event_queue),
                            timeout=30.0  # 30 second timeout
                        )
                        
                        # Return success response
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": data.get('id'),
                            "result": {
                                "taskId": task_id,
                                "contextId": context_id,
                                "status": "completed"
                            }
                        }
                        
                        return JSONResponse(response_data)
                        
                    except asyncio.TimeoutError:
                        print(f"❌ Agent execution timed out")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": data.get('id'),
                            "error": {
                                "code": -32603,
                                "message": "Agent execution timed out"
                            }
                        }
                        return JSONResponse(error_response)
                        
                    except Exception as exec_error:
                        print(f"❌ Agent execution error: {exec_error}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": data.get('id'),
                            "error": {
                                "code": -32603,
                                "message": f"Agent execution error: {str(exec_error)}"
                            }
                        }
                        return JSONResponse(error_response)
                        
                else:
                    # Method not found
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": data.get('id'),
                        "error": {
                            "code": -32601,
                            "message": "Method not found"
                        }
                    }
                    return JSONResponse(error_response)
                    
            except Exception as e:
                print(f"❌ JSON-RPC handler error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": data.get('id') if 'data' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                return JSONResponse(error_response)
        
        # Add the custom JSON-RPC route
        app.add_route("/", handle_jsonrpc, methods=["POST"])
        print("DEBUG: Added Tachyon-compatible JSON-RPC handler for send_message")
        
        # Add request logging middleware
        @app.middleware("http")
        async def log_requests(request, call_next):
            print(f"\n{'='*80}")
            print(f"TACHYON INCOMING REQUEST: {request.method} {request.url}")
            print(f"Headers: {dict(request.headers)}")
            
            # Read request body
            body = await request.body()
            print(f"Body length: {len(body)} bytes")
            
            if body:
                try:
                    body_text = body.decode('utf-8')
                    print(f"Body content: {body_text}")
                    
                    # Try to parse as JSON
                    try:
                        body_json = json.loads(body_text)
                        print(f"Body JSON: {json.dumps(body_json, indent=2)}")
                        
                        # Check if this is a send_message request
                        if 'method' in body_json and body_json['method'] == 'send_message':
                            print("🎯 TACHYON SEND_MESSAGE REQUEST DETECTED!")
                            
                    except json.JSONDecodeError:
                        print("Body is not valid JSON")
                except UnicodeDecodeError:
                    print("Body is not valid UTF-8")
            else:
                print("Body is empty")
            
            print(f"{'='*80}\n")
            
            # Process the request
            response = await call_next(request)
            
            print(f"TACHYON RESPONSE: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            return response
        
        print(f"DEBUG: Starting Tachyon-compatible server on {host}:{port}")
        print("🚀 Starting Wells Fargo Bank Agent (Tachyon A2A Server)")
        print("=" * 60)
        print(f"✅ Agent Card: {agent_card.name}")
        print(f"   URL: {agent_card.url}")
        print(f"   Skills: {[skill.name for skill in agent_card.skills]}")
        print(f"🌐 Server URL: http://{host}:{port}")
        print(f"🔗 Agent Card URL: http://{host}:{port}/.well-known/agent-card.json")
        print("📡 Ready for Tachyon agent-to-agent communication!")
        print("=" * 60)
        
        uvicorn.run(app, host=host, port=port, log_level="info")
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
