import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterable, List
from tachyon_adk_client import TachyonAdkClient
import httpx
import nest_asyncio
from a2a.client import A2ACardResolver
from a2a.types import AgentCard
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from .remote_agent_connection import RemoteAgentConnections
from .host_tools import build_and_send_credit_request as build_and_send_credit_request_tool,select_best_loan_offer as select_best_loan_offer_tool, send_user_message as send_user_message_tool, display_offers as display_offers_tool

load_dotenv()
nest_asyncio.apply()

class SessionManager:
    """Enhanced session management for A2A communication"""
    
    def __init__(self):
        self.sessions: dict[str, dict] = {}  # session_id -> session_data
        self.agent_sessions: dict[str, str] = {}  # agent_name -> session_id
        self.session_timeout = 3600  # 1 hour
        self.max_sessions = 100
    
    def create_session(self, agent_name: str, context_id: str = None) -> str:
        """Create a new session for an agent"""
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "agent_name": agent_name,
            "context_id": context_id,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "status": "active"
        }
        
        # Clean up old sessions if needed
        self._cleanup_old_sessions()
        
        self.sessions[session_id] = session_data
        self.agent_sessions[agent_name] = session_id
        
        return session_id
    
    def get_session(self, agent_name: str) -> dict:
        """Get session data for an agent"""
        session_id = self.agent_sessions.get(agent_name)
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session["last_accessed"] = datetime.now()
            return session
        return None
    
    def update_session(self, agent_name: str, **kwargs):
        """Update session data"""
        session = self.get_session(agent_name)
        if session:
            session.update(kwargs)
            session["last_accessed"] = datetime.now()
    
    def close_session(self, agent_name: str):
        """Close a session"""
        session_id = self.agent_sessions.get(agent_name)
        if session_id and session_id in self.sessions:
            self.sessions[session_id]["status"] = "closed"
            del self.agent_sessions[agent_name]
    
    def _cleanup_old_sessions(self):
        """Clean up old and expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            # Check if session is expired
            if (current_time - session["last_accessed"]).total_seconds() > self.session_timeout:
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            session = self.sessions[session_id]
            agent_name = session["agent_name"]
            del self.sessions[session_id]
            if agent_name in self.agent_sessions:
                del self.agent_sessions[agent_name]
        
        # Remove oldest sessions if we exceed max_sessions
        if len(self.sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1]["last_accessed"]
            )
            sessions_to_remove = len(self.sessions) - self.max_sessions
            for i in range(sessions_to_remove):
                session_id, session = sorted_sessions[i]
                agent_name = session["agent_name"]
                del self.sessions[session_id]
                if agent_name in self.agent_sessions:
                    del self.agent_sessions[agent_name]

class ConsumerAgent:
    """The Consumer Agent for credit requests."""

    def __init__(
        self,
    ):
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ""
        self.received_offers: dict[str, list] = {}  # request_id -> list of offers
        self.session_ids: dict[str, str] = {}  # bank_name -> context/session id
        self.session_manager = SessionManager()
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
        async with httpx.AsyncClient(timeout=300.0) as client:
            for address in remote_agent_addresses:
                try:
                    # Try the new agent-card.json endpoint first
                    agent_card_url = f"{address}/.well-known/agent-card.json"
                    print(f"Attempting to fetch agent card from: {agent_card_url}")
                    response = await client.get(agent_card_url, timeout=300.0)
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

    async def build_and_send_credit_request(
        self,
        user_input: dict,
        tool_context: ToolContext = None,
    ):
        return await build_and_send_credit_request_tool(
            user_input = user_input,
            remote_agent_connections = self.remote_agent_connections,
            received_offers = self.received_offers,
            tool_context=tool_context,
            session_ids=self.session_ids,
        )

    async def select_best_loan_offer(self, loan_request_json: str, bank_offers_json: str):
        return await select_best_loan_offer_tool(loan_request_json, bank_offers_json)
    
    async def send_user_message(self, bank_name : str , user_input: str, tool_context: ToolContext = None):
        return await send_user_message_tool(
            user_input = user_input,
            bank_name = bank_name,
            remote_agent_connections= self.remote_agent_connections, 
            received_offers=self.received_offers,  
            tool_context=tool_context,
            session_ids=self.session_ids,
        )
    
    async def display_offers(self, received_offers: list, tool_context: ToolContext = None):
        return await display_offers_tool(
            received_offers=received_offers,
            tool_context=tool_context
        )

    def create_agent(self) -> Agent:
        return Agent(
            model=TachyonAdkClient(model_name="gemini-2.5-flash"),
            name="Consumer_Agent",
            instruction=self.root_instruction,
            description="This Consumer agent requests credit lines from bank agents.",
            tools=[
                self.build_and_send_credit_request,
                self.select_best_loan_offer,
                self.send_user_message,
                self.display_offers,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return f"""
        **Role:** You are the Consumer Agent, an expert financial assistant for companies seeking credit lines. Your primary function is to coordinate with bank agents to find the best credit offers based on financial terms and ESG criteria.

        **Core Directives:**

        *   **Send Requests:** Use the `build_and_send_credit_request` tool to send structured credit requests to all available bank agents. 

        *   **Collect Offers:** Wait for the offers from bank agents. Wait until all responses are received from the bank agents and proceed with the next step.

        *   **Display Offers:** Pass all the collected offers into 'display_offers' tool in the below format and display the offers return by the tool.
                "bankname": string,
                "bankid": string,
                "amount_approved": number,
                "created_date": string,
                "currency": string,
                "esg_impact_summary": string,
                "intent_id": string,
                "interest_rate_annual": float,
                "offer_id": string,
                "protocol_version": string,
                "repayment_duration_months": number,
                "repayment_schedule": string,
                "status": string
        ***    Use the display_offers tool to display the offers to the user. Mandotirly use this tool to display the offers to the user without fail.
                
        *   **Compare Offers:
            From the context, extract the below JSON and pass it to the tool as string:
            loan_request_json=
                "sender_contact_email": string,
                "purpose": string,
                "amount_value": number,
                "repayment_duration": number,
                "repayment_preference": string,
                "preferred_interest_rate": float,
                "drawdown_type": string,
                "collateral_description": string,
                "esg_reporting_url": string,
                "data_sharing_consent": boolean
            Also extract the below list of JSON bank offers in below format: 
                "bankname": string,
                "bankid": string,
                "amount_approved": number,
                "created_date": string,
                "currency": string,
                "esg_impact_summary": string,
                "intent_id": string,
                "interest_rate_annual": float,
                "offer_id": string,
                "protocol_version": string,
                "repayment_duration_months": number,
                "repayment_schedule": string,
                "status": string
            Pass the above 2 parameters into the select_best_loan_offer tool Use the select_best_loan_offer tool to decide the best offer.
            Return the decided best offer to the user and proceed to the next step for negotiation.

        *   **Negotiate Offers:** Ask if the user wants to negotiate and provide any counter offers to the specific banks otherwise ask consent from the user to allow you for the negotiation on behalf of the company/yourself with the banks.
        In case the user gives any input for negotiating with the banks, then call the send_user_message_tool. rephrase to a better sentence and pass user input string to this tool. Ask the user to input which banks he wants to negotiate with, look at the {self.agents}  and pass the exact bank name to the 'send_user_message_tool'.

        *   **Select Best Final Offer:** Display again all the final offers after updating the negotiated interest rates 
        Call the select_best_loan_offer tool and pass the final offers into this tool.
            From the context, extract the below JSON and pass it to the tool as Dict:
                loan_request_json=
                    "sender_contact_email": string,
                    "purpose": string,
                    "amount_value": number,
                    "repayment_duration": number,
                    "repayment_preference": string,
                    "preferred_interest_rate": float,
                    "drawdown_type": string,
                    "collateral_description": string,
                    "esg_reporting_url": string,
                    "data_sharing_consent": boolean
                Also extract the below list of JSON bank offers in below format: 
                    "bankname": string,
                    "bankid": string,
                    "amount_approved": number,
                    "created_date": string,
                    "currency": string,
                    "esg_impact_summary": string,
                    "intent_id": string,
                    "interest_rate_annual": float,//in case the negotiation happened then put the negotiated interest rate that bank has responded otherwise put the initial interest rate in loan offer from that bank
                    "offer_id": string,
                    "protocol_version": string,
                    "repayment_duration_months": number,
                    "repayment_schedule": string,
                    "status": string
                Return the decided best offer to the user stating the reasons why this offer was selected as the best among all others.

        *   **Accept Offer:** Display all the updated offers from all the agents
            Also extract the below list of JSON bank offers in below format: 
                    "bankname": string,
                    "bankid": string,
                    "amount_approved": number,
                    "created_date": string,
                    "currency": string,
                    "esg_impact_summary": string,
                    "intent_id": string,
                    "interest_rate_annual": float,//in case the negotiation happened then put the negotiated interest rate that bank has responded otherwise put the initial interest rate in loan offer from that bank
                    "offer_id": string,
                    "protocol_version": string,
                    "repayment_duration_months": number,
                    "repayment_schedule": string,
                    "status": string
            Ask user to input which bank he wants to accept the loan offer, if the user accepts the loan offer follow the below step:

            Pass the user input that we have accepted the loan offer to the send_user_message_tool.We are using the same tool to send the acceptance message. Based on the bank that user has chosen, look at the {self.agents} and pass the exact bank name to the 'send_user_message_tool'.

        The send_user_message_tool will return the final agreed upon offer. Return that offer to the user as the final response with message.
        
        ***Retry Mechanism:***
            - While calling any tools, if there are invalid arguments passed or the request is errored due to invalid inputs, please pass the parameters again properly and retry calling the same tool for the same action for 2 times. only if it fails for more than 3 times, then report the error to user.
            - Please enforce the 3 Times Retry Mechanism for any sort of error encountered by the agent.
 
        **CRITICAL**
        -Make sure to send a appropriate message everytime when the user expects, do not send "No response" or error type of messages.
        -Wherever mentioned in prompt to display or return something to the user, make sure to return the correct and required output to the user without fail. Do not interpret too much whil responding to user.
    
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

def _get_initialized_consumer_agent_sync():
    """Synchronously creates and initializes the ConsumerAgent."""

    async def _async_main():
        # Updated URLs for all 5 bank agents
        bank_agent_urls = [
            "http://localhost:10002",  # CloudTrust Financial Agent
            "http://localhost:10003",  # Finovate Bank Agent
            "http://localhost:10004",  # Zentra Bank Agent
            "http://localhost:10005",  # NexVault Bank Agent
            "http://localhost:10006"   # Byte Bank Agent
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