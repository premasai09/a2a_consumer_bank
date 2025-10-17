from typing import Callable
import asyncio
import httpx
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    SendMessageRequest,
    SendMessageResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)
from dotenv import load_dotenv

load_dotenv()

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard, agent_url: str):
        print(f"agent_card: {agent_card}")
        print(f"agent_url: {agent_url}")
        self._httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=60.0))
        self.agent_client = A2AClient(self._httpx_client, agent_card, url=agent_url)
        self.card = agent_card
        self.conversation_name = None
        self.conversation = None
        self.pending_tasks = set()
        self._closed = False
    
    async def close(self):
        """Close the HTTP client and cleanup resources"""
        if not self._closed and self._httpx_client:
            try:
                await self._httpx_client.aclose()
                print(f"Closed HTTP client for {self.card.name}")
            except Exception as e:
                print(f"Error closing HTTP client for {self.card.name}: {e}")
            finally:
                self._closed = True
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if not self._closed:
            print(f"Warning: RemoteAgentConnections for {self.card.name} was not properly closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(
        self, message_request: SendMessageRequest
    ) -> SendMessageResponse:
        try:
            return await asyncio.wait_for(
                self.agent_client.send_message(message_request), timeout=300.0 
            )
        except asyncio.TimeoutError:
            print(f"Timeout sending message to {self.card.name}")
            raise
        except Exception as e:
            print(f"Error sending message to {self.card.name}: {e}")
            raise
