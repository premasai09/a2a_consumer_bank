import logging
from starlette.responses import JSONResponse
import json
import uuid
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import Part, TextPart
from google.genai import types
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from .agent import create_agent
from .agent_executor import TachyonAgentExecutor
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Starts the Tachyon-compatible agent server."""
    host = "localhost"
    port = 10002
    try:
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="cloudtrust_credit_request", 
            name="Cloud Trust Financial Credit Processing",
            description="CloudTrust Financial's conservative lending approch with strict ESG requirements and premium client focus",
            tags=["banking", "credit", "esg", "finance"],
            examples=["Process a credit request for $500,000 for 24 months"],
        )
        agent_card = AgentCard(
            name="CloudTrust Financial Agent",
            description="CloudTrust Financial's agent for processing credit line requests with ESG integration.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=capabilities,
            skills=[skill], 
        )

        adk_agent = create_agent()

        runner = Runner(
            app_name=agent_card.name,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        agent_executor = TachyonAgentExecutor(runner)

        task_store = InMemoryTaskStore()
        
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=task_store,
        )

        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )      
        app = server.build(agent_card_url='/.well-known/agent-card.json')
        print("Built app with agent-card.json")
        
        async def handle_jsonrpc(request):
            """Custom JSON-RPC handler for send_message method"""
            try:
                body = await request.body()
                data = json.loads(body)
                
                if data.get('method') == 'send_message':
                    params = data.get('params', {})
                    message = params.get('message', {})
                    
                    print(f"📨 Processing send_message: {message}")
                    
                    try:
                        task_id = message.get('taskId', str(uuid.uuid4()))
                        context_id = message.get('contextId', str(uuid.uuid4()))
                        
                        message_parts = []
                        if 'parts' in message:
                            for part in message['parts']:
                                if part.get('type') == 'text':
                                    message_parts.append(Part(root=TextPart(text=part['text'])))
                        
                        request_context = RequestContext(
                            task_id=task_id,
                            context_id=context_id,
                            message=types.UserContent(parts=message_parts) if message_parts else None
                        )

                        event_queue = EventQueue()

                        import asyncio
                        await asyncio.wait_for(
                            agent_executor.execute(request_context, event_queue),
                            timeout=300.0 
                        )

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
                        print(f"Agent execution timed out")
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
                        print(f"Agent execution error: {exec_error}")
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
                print(f"JSON-RPC handler error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": data.get('id') if 'data' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                return JSONResponse(error_response)
        
        app.add_route("/", handle_jsonrpc, methods=["POST"])

        print("Starting CloudTrust Financial Agent (Tachyon A2A Server)")
        print(f"Agent Card: {agent_card.name}")
        uvicorn.run(app, host=host, port=port, log_level="info")

    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
