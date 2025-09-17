import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterable, List

import httpx
import nest_asyncio
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
)
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .wfap_protocol import (
    Intent,
    Consumer,
    CreditRequest,
    ESGRequirements,
    Offer,
    verify_signature,
)
from .remote_agent_connection import RemoteAgentConnections

load_dotenv()
nest_asyncio.apply()


class ConsumerAgent:
    """The Consumer Agent for credit requests."""

    def __init__(
        self,
    ):
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ""
        self.received_offers: dict[str, list] = {}  # request_id -> list of offers
        self._agent = self.create_agent()
        self._user_id = "consumer_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def _async_init_components(self, remote_agent_addresses: List[str]):
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                try:
                    # Try the new agent-card.json endpoint first
                    agent_card_url = f"{address}/.well-known/agent-card.json"
                    print(f"Attempting to fetch agent card from: {agent_card_url}")
                    response = await client.get(agent_card_url)
                    response.raise_for_status()
                    card_data = response.json()
                    card = AgentCard.model_validate(card_data)
                    
                    remote_connection = RemoteAgentConnections(
                        agent_card=card, agent_url=address
                    )
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                    print(f"Successfully connected to {card.name} at {address}")
                except httpx.ConnectError as e:
                    print(f"ERROR: Failed to get agent card from {address}: {e}")
                except Exception as e:
                    print(f"ERROR: Failed to initialize connection for {address}: {e}")
                    # Fallback to original A2ACardResolver for backward compatibility
                    try:
                        print(f"Falling back to default agent.json endpoint for {address}")
                        card_resolver = A2ACardResolver(client, address)
                        card = await card_resolver.get_agent_card()
                        remote_connection = RemoteAgentConnections(
                            agent_card=card, agent_url=address
                        )
                        self.remote_agent_connections[card.name] = remote_connection
                        self.cards[card.name] = card
                        print(f"Successfully connected to {card.name} at {address} using fallback")
                    except Exception as fallback_error:
                        print(f"ERROR: Fallback also failed for {address}: {fallback_error}")

        agent_info = [
            json.dumps({"name": card.name, "description": card.description})
            for card in self.cards.values()
        ]
        print("agent_info:", agent_info)
        self.agents = "\n".join(agent_info) if agent_info else "No bank agents found"

    @classmethod
    async def create(
        cls,
        remote_agent_addresses: List[str],
    ):
        instance = cls()
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def create_agent(self) -> Agent:
        return Agent(
            model="gemini-2.5-flash",
            name="Consumer_Agent",
            instruction=self.root_instruction,
            description="This Consumer agent requests credit lines from bank agents.",
            tools=[
                self.send_credit_request,
                self.compare_offers,
                self.select_best_offer,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return f"""
        **Role:** You are the Consumer Agent, an expert financial assistant for companies seeking credit lines. Your primary function is to coordinate with bank agents to find the best credit offers based on financial terms and ESG criteria.

        **Core Directives:**

        *   **Credit Request Creation:** When asked to request a credit line, gather the following information from the user:
            - Company details (name, industry, annual revenue, years in business)
            - Credit requirements (amount, duration, purpose)
            - ESG preferences (weight given to environmental/social factors)
        *   **Send Requests:** Use the `send_credit_request` tool to send structured credit requests to all available bank agents.
        *   **Collect Offers:** Wait for and collect offers from bank agents.
        *   **Compare Offers:** Use the `compare_offers` tool to analyze all received offers based on:
            - Interest rates and fees
            - ESG scores and carbon-adjusted rates
            - Regulatory compliance
            - Risk assessment
        *   **Select Best Offer:** Use the `select_best_offer` tool to choose the optimal offer based on the company's criteria.
        *   **Transparent Communication:** Provide clear explanations of the selection process and reasoning.
        *   **Tool Reliance:** Strictly rely on available tools to address user requests. Do not generate responses based on assumptions.
        *   **Readability:** Make sure to respond in a concise and easy to read format (bullet points are good).

        **Today's Date (YYYY-MM-DD):** {datetime.now().strftime("%Y-%m-%d")}

        <Available Bank Agents>
        {self.agents}
        </Available Bank Agents>
        """

    async def stream(
        self, query: str, session_id: str
    ) -> AsyncIterable[dict[str, Any]]:
        """
        Streams the agent's response to a given query.
        """
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "The host agent is thinking...",
                }

    async def send_credit_request(
        self,
        company_name: str,
        company_industry: str,
        annual_revenue: float,
        years_in_business: int,
        credit_amount: float,
        duration_months: int,
        purpose: str,
        esg_weight: float = 0.3,
        tool_context: ToolContext = None,
    ):
        """Sends a credit request to all available bank agents."""
        request_id = str(uuid.uuid4())
        
        # Create consumer profile
        consumer = Consumer(
            company_id=f"COMP_{company_name.upper().replace(' ', '_')}",
            company_name=company_name,
            credit_score=750,  # Default good credit score
            annual_revenue=annual_revenue,
            years_in_business=years_in_business,
            industry=company_industry,
        )
        
        # Create credit request
        credit_request = CreditRequest(
            amount=credit_amount,
            duration=duration_months,
            purpose=purpose,
            preferred_interest_rate=8.0,  # Default preferred rate
        )
        
        # Create ESG requirements
        esg_requirements = ESGRequirements(
            esg_weight=esg_weight,
            carbon_footprint_threshold=100.0,
            social_impact_focus=["renewable_energy", "community_development"],
        )
        
        # Create intent
        intent = Intent(
            request_id=request_id,
            timestamp=datetime.now(),
            consumer=consumer,
            credit_request=credit_request,
            esg_requirements=esg_requirements,
        )
        
        # Create digital signature
        intent.create_signature(f"consumer_key_{company_name}")
        
        # Send to all bank agents
        responses = []
        for agent_name, connection in self.remote_agent_connections.items():
            try:
                # Simplified task and context ID management
                state = tool_context.state if tool_context else {}
                task_id = state.get("task_id", str(uuid.uuid4()))
                context_id = state.get("context_id", str(uuid.uuid4()))
                message_id = str(uuid.uuid4())

                payload = {
                    "message": {
                        "role": "user",
                        "parts": [{"type": "text", "text": intent.to_json()}],
                        "messageId": message_id
                    },
                }

                message_request = SendMessageRequest(
                    id=message_id, params=MessageSendParams.model_validate(payload)
                )
                send_response: SendMessageResponse = await connection.send_message(message_request)
                print(f"Response from {agent_name}:", send_response)

                # Handle different response formats
                response_content = None
                
                # Try A2A protocol format first
                if isinstance(send_response.root, SendMessageSuccessResponse) and isinstance(send_response.root.result, Task):
                    response_content = send_response.root.model_dump_json(exclude_none=True)
                    json_content = json.loads(response_content)
                    responses.append({
                        "bank": agent_name,
                        "response": json_content
                    })
                else:
                    # Handle other response formats (like Wells Fargo direct responses)
                    try:
                        # Try to extract response content from different possible structures
                        if hasattr(send_response, 'root') and send_response.root:
                            if hasattr(send_response.root, 'model_dump_json'):
                                response_content = send_response.root.model_dump_json(exclude_none=True)
                            else:
                                response_content = json.dumps(send_response.root)
                        else:
                            response_content = json.dumps(send_response)
                        
                        json_content = json.loads(response_content)
                        responses.append({
                            "bank": agent_name,
                            "response": json_content
                        })
                        print(f"DEBUG: Stored response from {agent_name} in alternative format")
                    except Exception as parse_error:
                        print(f"DEBUG: Failed to parse response from {agent_name}: {parse_error}")
                        responses.append({
                            "bank": agent_name,
                            "error": f"Failed to parse response: {str(parse_error)}"
                        })
                    
            except Exception as e:
                print(f"Error sending request to {agent_name}: {e}")
                responses.append({
                    "bank": agent_name,
                    "error": str(e)
                })
        
        # Store responses for later comparison
        self.received_offers[request_id] = responses
        
        return f"Credit request {request_id} sent to {len(self.remote_agent_connections)} bank agents. Received {len([r for r in responses if 'error' not in r])} responses."

    async def compare_offers(self, request_id: str, tool_context: ToolContext = None):
        """Present the loan agent's offer directly as the best offer (no comparison needed)."""
        if request_id not in self.received_offers:
            return "No offers found for this request ID."
        
        offers = self.received_offers[request_id]
        
        # Since we only have one loan agent, directly present their offer as the best offer
        for offer_data in offers:
            if 'error' in offer_data:
                continue
                
            try:
                # Parse the offer response
                response = offer_data['response']
                print(f"DEBUG: Processing response from {offer_data['bank']}")
                
                # Get the raw text response
                response_text = ""
                
                # Try Wells Fargo specific format first (process_credit_request_response.result)
                if 'process_credit_request_response' in response and 'result' in response['process_credit_request_response']:
                    print(f"DEBUG: Found Wells Fargo response format")
                    response_text = response['process_credit_request_response']['result']
                
                # Try A2A protocol format (with result.artifacts)
                elif 'result' in response and 'artifacts' in response['result']:
                    for artifact in response['result']['artifacts']:
                        if artifact.get('parts'):
                            for part in artifact['parts']:
                                if part.get('text'):
                                    print(f"DEBUG: Found A2A text part")
                                    response_text = part['text']
                                    break
                        if response_text:
                            break
                
                # If no structured format found, try direct response
                if not response_text:
                    response_text = json.dumps(response)
                
                if response_text:
                    # Extract approved_amount and interest_rate directly from text using regex
                    import re
                    
                    # Look for approved_amount pattern - handle multiple levels of escaping
                    # Pattern matches: "approved_amount": 24128.959098947747 or \"approved_amount\": 24128.959098947747
                    amount_match = re.search(r'["\\]*approved_amount["\\]*:\s*([0-9.]+)', response_text)
                    # Look for interest_rate pattern - handle multiple levels of escaping  
                    # Pattern matches: "interest_rate": 4.7 or \"interest_rate\": 4.7
                    rate_match = re.search(r'["\\]*interest_rate["\\]*:\s*([0-9.]+)', response_text)
                    
                    if amount_match and rate_match:
                        amount = float(amount_match.group(1))
                        rate = float(rate_match.group(1))
                        return f"BEST OFFER: Approved Amount: ${amount:,.2f}, Interest Rate: {rate:.2f}%"
                    else:
                        print(f"DEBUG: Could not extract amount and rate from response text")
                        print(f"DEBUG: Response text sample: {response_text[:500]}...")
                        continue
                    
            except Exception as e:
                print(f"DEBUG: Error processing response from {offer_data['bank']}: {e}")
                continue
        
        return "No valid offers available from any bank agents."

    async def select_best_offer(self, request_id: str, tool_context: ToolContext = None):
        """Present the loan agent's offer directly as the best offer (no selection needed)."""
        if request_id not in self.received_offers:
            return "No offers found for this request ID."
        
        offers = self.received_offers[request_id]
        
        # Since we only have one loan agent, directly present their offer as the best offer
        for offer_data in offers:
            if 'error' in offer_data:
                continue
                
            try:
                # Parse the offer response
                response = offer_data['response']
                print(f"DEBUG: Processing response from {offer_data['bank']}")
                
                # Get the raw text response
                response_text = ""
                
                # Try Wells Fargo specific format first (process_credit_request_response.result)
                if 'process_credit_request_response' in response and 'result' in response['process_credit_request_response']:
                    print(f"DEBUG: Found Wells Fargo response format")
                    response_text = response['process_credit_request_response']['result']
                
                # Try A2A protocol format (with result.artifacts)
                elif 'result' in response and 'artifacts' in response['result']:
                    for artifact in response['result']['artifacts']:
                        if artifact.get('parts'):
                            for part in artifact['parts']:
                                if part.get('text'):
                                    print(f"DEBUG: Found A2A text part")
                                    response_text = part['text']
                                    break
                        if response_text:
                            break
                
                # If no structured format found, try direct response
                if not response_text:
                    response_text = json.dumps(response)
                
                if response_text:
                    # Extract approved_amount and interest_rate directly from text using regex
                    import re
                    
                    # Look for approved_amount pattern - handle multiple levels of escaping
                    # Pattern matches: "approved_amount": 24128.959098947747 or \"approved_amount\": 24128.959098947747
                    amount_match = re.search(r'["\\]*approved_amount["\\]*:\s*([0-9.]+)', response_text)
                    # Look for interest_rate pattern - handle multiple levels of escaping  
                    # Pattern matches: "interest_rate": 4.7 or \"interest_rate\": 4.7
                    rate_match = re.search(r'["\\]*interest_rate["\\]*:\s*([0-9.]+)', response_text)
                    
                    if amount_match and rate_match:
                        amount = float(amount_match.group(1))
                        rate = float(rate_match.group(1))
                        return f"BEST OFFER: Approved Amount: ${amount:,.2f}, Interest Rate: {rate:.2f}%"
                    else:
                        print(f"DEBUG: Could not extract amount and rate from response text")
                        print(f"DEBUG: Response text sample: {response_text[:500]}...")
                        continue
                    
            except Exception as e:
                print(f"DEBUG: Error processing response from {offer_data['bank']}: {e}")
                continue
        
        return "No valid offers available from any bank agents. Please try again or contact the banks directly."


def _get_initialized_consumer_agent_sync():
    """Synchronously creates and initializes the ConsumerAgent."""

    async def _async_main():
        # Hardcoded URLs for the bank agents
        bank_agent_urls = [
            "http://localhost:10002",  # Wells Fargo Bank Agent
        ]

        print("initializing consumer agent")
        consumer_agent_instance = await ConsumerAgent.create(
            remote_agent_addresses=bank_agent_urls
        )
        print("ConsumerAgent initialized")
        return consumer_agent_instance.create_agent()

    try:
        return asyncio.run(_async_main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            print(
                f"Warning: Could not initialize ConsumerAgent with asyncio.run(): {e}. "
                "This can happen if an event loop is already running (e.g., in Jupyter). "
                "Consider initializing ConsumerAgent within an async function in your application."
            )
        else:
            raise


root_agent = _get_initialized_consumer_agent_sync()
