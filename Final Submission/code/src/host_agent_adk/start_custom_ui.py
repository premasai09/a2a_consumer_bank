try:
    from .web_server import app, initialize_consumer_agent
except ImportError:
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent.absolute()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from web_server import app, initialize_consumer_agent
import asyncio
import nest_asyncio
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
import flask
import flask_cors
import httpx
import threading

def check_dependencies():
    try:
        return True
    except ImportError:
        return False

def check_bank_agents(): 
    bank_agents = [
        ("CloudTrust Financial", "http://localhost:10002"),
        ("Finovate Bank", "http://localhost:10003"),
        ("Zentra Bank", "http://localhost:10004"),
        ("Byte Bank", "http://localhost:10005"),
        ("NexVault Bank", "http://localhost:10006")
    ]   
    print("\nChecking bank agent connections...")
    async def check_agent(name, url):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{url}/.well-known/agent-card.json")
                if response.status_code == 200:
                    print(f"{name} is running at {url}")
                    return True
                else:
                    print(f"{name} at {url} returned status {response.status_code}")
                    return False
        except Exception as e:
            print(f"{name} at {url} is not accessible: {str(e)}")
            return False
    
    
    
    async def check_all():
        tasks = [check_agent(name, url) for name, url in bank_agents]
        results = await asyncio.gather(*tasks)
        return sum(results)
    
    try:
        connected_count = asyncio.run(check_all())
        print(f"\n{connected_count}/5 bank agents are running")   
        return connected_count > 0
        
    except Exception as e:
        return False

def main():
    print("A2A Consumer Bank - Custom Chat Interface")
    print("=" * 50)

    script_dir = Path(__file__).parent.absolute()
    web_server_path = script_dir / "web_server.py"
    
    if not check_dependencies():
        sys.exit(1)
    check_bank_agents()
    
    print("Server will be available at: http://localhost:8000")
    
    try:
        current_dir = Path(__file__).parent.absolute()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        nest_asyncio.apply()
        
        print("Initializing consumer agent...")
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(initialize_consumer_agent())
            
            if success:
                print("Consumer agent initialized successfully")
            else:
                print("Consumer agent initialization failed, running in fallback mode")
        except Exception as e:
            print(f"Consumer agent error: {e}")
        
        print("\n" + "=" * 50)
        print("Open your browser to: http://localhost:8000")
        print("=" * 50)       
        
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open("http://localhost:8000")
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        app.run(
            host='0.0.0.0',
            port=8000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("Shutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
