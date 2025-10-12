import asyncio
import json
import logging
import uuid
import atexit
import signal
import threading
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, AsyncGenerator

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import nest_asyncio
import sys
import os
from .agent import ConsumerAgent
from .company_config import CorporateConfig

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables to store the consumer agent and sessions
consumer_agent: ConsumerAgent = None
active_sessions: Dict[str, Dict[str, Any]] = {}

# Initialize company configuration
company_config = CorporateConfig()

# Global event loop for async operations
_global_loop = None
_loop_thread = None

def initialize_global_loop():
    """Initialize a global event loop in a separate thread."""
    global _global_loop, _loop_thread
    
    def run_loop():
        global _global_loop
        _global_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_global_loop)
        _global_loop.run_forever()
    
    _loop_thread = threading.Thread(target=run_loop, daemon=True)
    _loop_thread.start()
    
    import time
    while _global_loop is None:
        time.sleep(0.01)

def cleanup_async_tasks():
    """Clean up any remaining async tasks and close the global loop."""
    global _global_loop, _loop_thread
    
    try:
        if _global_loop and not _global_loop.is_closed():
            # Cancel all pending tasks
            pending = asyncio.all_tasks(_global_loop)
            for task in pending:
                task.cancel()
            
            if pending:
                _global_loop.call_soon_threadsafe(_global_loop.stop)
                
            _global_loop.call_soon_threadsafe(_global_loop.stop)
            
            if _loop_thread and _loop_thread.is_alive():
                _loop_thread.join(timeout=2.0)
                
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

initialize_global_loop()

# Register cleanup function
atexit.register(cleanup_async_tasks)

# Handle signals for proper shutdown
def signal_handler(signum, frame):
    cleanup_async_tasks()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def initialize_consumer_agent():
    """Initialize the consumer agent with bank connections."""
    global consumer_agent
    
    try:
        logger.info("Initializing consumer agent...")
        
        # Bank agent URLs
        bank_agent_urls = [
            "http://localhost:10002",  # CloudTrust Financial Agent
            "http://localhost:10003",  # Finovate Bank Agent  
            "http://localhost:10004",   # Zentra Bank Agent
            "http://localhost:10005",  # Byte Bank Agent
            "http://localhost:10006"   # NexVault Bank Agent
        ]
        
        consumer_agent = await ConsumerAgent.create(
            remote_agent_addresses=bank_agent_urls
        )
        logger.info("Consumer agent initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize consumer agent: {e}")
        return False

def run_async_in_thread(coro):
    """Run async function using the global event loop."""
    global _global_loop
    
    if _global_loop is None or _global_loop.is_closed():
        logger.error("Global event loop is not available")
        return None
    
    try:
        future = concurrent.futures.Future()
        
        def run_coro():
            try:
                task = asyncio.ensure_future(coro, loop=_global_loop)
                
                def on_done(t):
                    if t.exception():
                        future.set_exception(t.exception())
                    else:
                        future.set_result(t.result())
                
                task.add_done_callback(on_done)
                
            except Exception as e:
                future.set_exception(e)
        
        _global_loop.call_soon_threadsafe(run_coro)
        return future.result(timeout=300.0)
        
    except concurrent.futures.TimeoutError:
        logger.error("Async operation timed out after 300 seconds")
        return None
    except Exception as e:
        logger.error(f"Error running async function: {e}")
        return None

@app.route('/')
def serve_index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)."""
    return send_from_directory('.', filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'agent_initialized': consumer_agent is not None,
        'active_sessions': len(active_sessions)
    })

@app.route('/api/agent-status', methods=['GET'])
def get_agent_status():
    """Get the status of bank agent connections."""
    if not consumer_agent:
        return jsonify({'error': 'Consumer agent not initialized'}), 500
    
    try:
        bank_status = {}
        for bank_name, connection in consumer_agent.remote_agent_connections.items():
            bank_status[bank_name] = {
                'connected': True,
                'url': connection.agent_client.url if hasattr(connection.agent_client, 'url') else 'unknown',
                'description': connection.card.description if connection.card else 'No description'
            }
        
        return jsonify({
            'consumer_agent_ready': True,
            'bank_agents': bank_status,
            'total_banks': len(bank_status)
        })
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new chat session."""
    try:
        session_id = f"session_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        active_sessions[session_id] = {
            'created_at': datetime.now().isoformat(),
            'message_count': 0,
            'last_activity': datetime.now().isoformat()
        }
        
        logger.info(f"Created new session: {session_id}")
        
        return jsonify({
            'session_id': session_id,
            'created_at': active_sessions[session_id]['created_at']
        })
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_info(session_id):
    """Get information about a specific session."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'session_id': session_id,
        **active_sessions[session_id]
    })

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Stream chat responses from the consumer agent."""
    if not consumer_agent:
        return jsonify({'error': 'Consumer agent not initialized'}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query', '').strip()
        session_id = data.get('session_id')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Update session info
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                'created_at': datetime.now().isoformat(),
                'message_count': 0,
                'last_activity': datetime.now().isoformat()
            }
        
        active_sessions[session_id]['message_count'] += 1
        active_sessions[session_id]['last_activity'] = datetime.now().isoformat()
        
        logger.info(f"Processing chat request for session {session_id}: {query[:100]}...")
        
        def generate_response():
            """Generator function for streaming response directly from ADK runner."""
            try:
                if not consumer_agent:
                    error_event = {
                        'is_task_complete': True,
                        'content': 'Consumer agent not available'
                    }
                    yield f"data: {json.dumps(error_event)}\n\n"
                    return

                async def stream_from_runner():
                    session = await consumer_agent._runner.session_service.get_session(
                        app_name=consumer_agent._agent.name,
                        user_id=consumer_agent._user_id,
                        session_id=session_id,
                    )
                    
                    if session is None:
                        session = await consumer_agent._runner.session_service.create_session(
                            app_name=consumer_agent._agent.name,
                            user_id=consumer_agent._user_id,
                            state={},
                            session_id=session_id,
                        )
                    
                    from google.genai import types
                    content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
                    
                    # Stream through the ADK runner directly
                    async for event in consumer_agent._runner.run_async(
                        user_id=consumer_agent._user_id, 
                        session_id=session.id, 
                        new_message=content
                    ):
                        if event.is_final_response():
                            response = ""
                            if event.content and event.content.parts and event.content.parts[0].text:
                                response = "\n".join([p.text for p in event.content.parts if p.text])
                            
                            yield {
                                "is_task_complete": True,
                                "content": response,
                            }
                        else:
                            yield {
                                "is_task_complete": False,
                                "updates": "The host agent is thinking...",
                            }
                
                def run_async_generator():
                    async_gen = stream_from_runner()
                    events = []
                    
                    async def collect_events():
                        try:
                            async for event in async_gen:
                                events.append(event)
                                await asyncio.sleep(0.1)
                        except Exception as e:
                            logger.error(f"Error in collect_events: {e}")
                            events.append({
                                'is_task_complete': True,
                                'content': f'Error: {str(e)}'
                            })
                    
                    result = run_async_in_thread(collect_events())
                    return result, events
                
                result, events = run_async_generator()
                
                if not events:
                    events.append({
                        'is_task_complete': True,
                        'content': 'No response received from agent. Please try again.'
                    })
                
                for event in events:
                    yield f"data: {json.dumps(event)}\n\n"
                        
            except Exception as e:
                logger.error(f"Error in generate_response: {e}")
                error_event = {
                    'is_task_complete': True,
                    'content': f'Error: {str(e)}'
                }
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return Response(
            generate_response(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat_stream: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_simple():
    """Simple chat endpoint that returns immediate response."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query', '').strip()
        session_id = data.get('session_id')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Update session info
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                'created_at': datetime.now().isoformat(),
                'message_count': 0,
                'last_activity': datetime.now().isoformat()
            }
        
        active_sessions[session_id]['message_count'] += 1
        active_sessions[session_id]['last_activity'] = datetime.now().isoformat()
        
        logger.info(f"Processing simple chat request for session {session_id}: {query[:100]}...")
        
        try:
            if not consumer_agent:
                response_content = "Consumer agent not available. Please restart the server."
            else:
                async def get_direct_response():
                    session = await consumer_agent._runner.session_service.get_session(
                        app_name=consumer_agent._agent.name,
                        user_id=consumer_agent._user_id,
                        session_id=session_id,
                    )
                    
                    if session is None:
                        session = await consumer_agent._runner.session_service.create_session(
                            app_name=consumer_agent._agent.name,
                            user_id=consumer_agent._user_id,
                            state={},
                            session_id=session_id,
                        )
                    
                    from google.genai import types
                    content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
                    
                    # Run through the ADK runner directly
                    response_parts = []
                    final_response_received = False
                    
                    async for event in consumer_agent._runner.run_async(
                        user_id=consumer_agent._user_id, 
                        session_id=session.id, 
                        new_message=content
                    ):
                        if event.is_final_response():
                            final_response_received = True
                            if event.content and event.content.parts and event.content.parts[0].text:
                                response_parts.append(event.content.parts[0].text)
                    
                    if not final_response_received:
                        logger.warning("No final response received from agent")
                        return "No response received from agent. The agent may be processing your request. Please try again in a moment."
                    
                    return "\n".join(response_parts) if response_parts else "No response content from agent"
                
                response_content = run_async_in_thread(get_direct_response())
                if response_content is None:
                    response_content = "Error: Failed to get response from agent"
                    
        except Exception as e:
            logger.error(f"Error communicating directly with ADK runner: {e}")
            response_content = f"Error: {str(e)}"
        
        return jsonify({
            'response': response_content,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat_simple: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/company-config', methods=['GET'])
def get_company_config():
    """Endpoint to get company configuration data."""
    try:
        config_data = company_config.to_dict()
        return jsonify(config_data)
    except Exception as e:
        logger.error(f"Error fetching company configuration: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting web server...")
    
    try:
        success = run_async_in_thread(initialize_consumer_agent())
        
        if success:
            logger.info("Consumer agent initialized successfully")
        else:
            logger.warning("Consumer agent initialization failed, running in fallback mode")
            
    except Exception as e:
        logger.error(f"Failed to initialize consumer agent: {e}")
        logger.warning("Running in fallback mode without consumer agent")
    
    # Start the Flask server
    logger.info("Starting Flask server on http://localhost:8000")
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False,
        threaded=True
    )