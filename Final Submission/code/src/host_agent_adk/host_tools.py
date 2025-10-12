from datetime import datetime
import json
import uuid
import asyncio
import logging
from a2a.types import (
    SendMessageRequest,
    MessageSendParams
)
from typing import Dict, Any
from datetime import datetime
import re, json
from host_agent_adk.company_config import CorporateConfig
import asyncio
import uuid
from host_agent_adk.loan_offer_analyzer_tool import LoanOfferAnalyzer
from .remote_agent_connection import RemoteAgentConnections
import hashlib
import base64
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

# Configure logging
logger = logging.getLogger(__name__)


PER_AGENT_TIMEOUT = int(os.getenv('PER_AGENT_TIMEOUT', '300'))
GLOBAL_TIMEOUT = int(os.getenv('GLOBAL_TIMEOUT', '300'))        
HTTPX_CONNECT_TIMEOUT = int(os.getenv('HTTPX_CONNECT_TIMEOUT', '300'))  
HTTPX_READ_TIMEOUT = int(os.getenv('HTTPX_READ_TIMEOUT', '300'))      
BANK_AGENT_EXECUTION_TIMEOUT = int(os.getenv('BANK_AGENT_EXECUTION_TIMEOUT', '300'))  
WEB_SERVER_ASYNC_TIMEOUT = int(os.getenv('WEB_SERVER_ASYNC_TIMEOUT', '300'))        

# Log configuration
logger.info(f"Timeout Configuration - PER_AGENT: {PER_AGENT_TIMEOUT}s, GLOBAL: {GLOBAL_TIMEOUT}s")  

_host_crypto_manager = None

def get_host_crypto_manager():
    """Get or create crypto manager for host agent"""
    global _host_crypto_manager
    if _host_crypto_manager is None:
        _host_crypto_manager = CryptoManager("host_agent")
    return _host_crypto_manager

class CryptoManager:
    """Manages RSA key pairs and digital signatures for A2A communication"""
    
    def __init__(self, agent_name: str, keys_dir: str = "keys"):
        self.agent_name = agent_name
        self.keys_dir = keys_dir
        self.private_key = None
        self.public_key = None
        self.public_keys_cache = {}  # agent_name -> public_key_pem
        
        # Ensure keys directory exists
        os.makedirs(keys_dir, exist_ok=True)
        
        # Load or generate keys
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones"""
        private_key_path = os.path.join(self.keys_dir, f"{self.agent_name}_private.pem")
        public_key_path = os.path.join(self.keys_dir, f"{self.agent_name}_public.pem")
        
        try:
            # Try to load existing keys
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                with open(private_key_path, 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(), password=None, backend=default_backend()
                    )
                with open(public_key_path, 'rb') as f:
                    self.public_key = serialization.load_pem_public_key(
                        f.read(), backend=default_backend()
                    )
                logger.info(f"Loaded existing keys for {self.agent_name}")
            else:
                # Generate new keys
                self._generate_new_keys()
                self._save_keys(private_key_path, public_key_path)
                logger.info(f"Generated new keys for {self.agent_name}")
        except Exception as e:
            logger.error(f"Error loading keys for {self.agent_name}: {e}")
            # Generate new keys as fallback
            self._generate_new_keys()
            self._save_keys(private_key_path, public_key_path)
    
    def _generate_new_keys(self):
        """Generate new RSA key pair"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def _save_keys(self, private_key_path: str, public_key_path: str):
        """Save keys to files"""
        try:
            # Save private key
            with open(private_key_path, 'wb') as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save public key
            with open(public_key_path, 'wb') as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
        except Exception as e:
            logger.error(f"Error saving keys: {e}")
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        if not self.public_key:
            raise ValueError("Public key not available")
        
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    def add_public_key(self, agent_name: str, public_key_pem: str):
        """Add another agent's public key to cache"""
        self.public_keys_cache[agent_name] = public_key_pem
        logger.info(f"Added public key for {agent_name}")
    
    def sign_data(self, data: dict) -> dict:
        """Sign data with private key"""
        if not self.private_key:
            raise ValueError("Private key not available")
        
        try:
            # Convert to string with sorted keys for consistent signing
            json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            
            # Hash the data
            data_hash = hashlib.sha256(json_str.encode('utf-8')).digest()
            
            # Sign with private key
            signature = self.private_key.sign(
                data_hash,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Base64 encode signature
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            
            # Create signed data
            signed_data = data.copy()
            signed_data["signature"] = signature_b64
            signed_data["public_key"] = self.get_public_key_pem()
            signed_data["signer"] = self.agent_name
            
            return signed_data
            
        except Exception as e:
            logger.error(f"Error signing data: {e}")
            raise

def sign_json_rsa(data):
    """
    Sign JSON data with RSA private key using persistent key management
    """
    crypto_manager = get_host_crypto_manager()
    return crypto_manager.sign_data(data)


def verify_json_rsa(signed_data_str):
    """
    Verify the signature in the signed JSON data and return the original data
    """
    try:
        # Parse the JSON string
        if isinstance(signed_data_str, str):
            signed_data = json.loads(signed_data_str)
        else:
            signed_data = signed_data_str
        
        # Check if signature and public key exist
        if "signature" not in signed_data or "public_key" not in signed_data:
            return False, "Missing signature or public key in data"
        
        # Extract signature and public key
        signature_b64 = signed_data.pop("signature")
        public_key_pem = signed_data.pop("public_key")
        signer = signed_data.pop("signer", "unknown")
        
        # Create a copy of the original data
        original_data = signed_data.copy()
        
        # Convert to string with sorted keys (same as signing)
        json_str = json.dumps(original_data, sort_keys=True, separators=(',', ':'))
        
        # Hash the data
        data_hash = hashlib.sha256(json_str.encode('utf-8')).digest()
        
        # Decode signature from base64
        signature = base64.b64decode(signature_b64)
        
        # Load the public key
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'), backend=default_backend()
        )
        
        # Verify the signature
        public_key.verify(
            signature,
            data_hash,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        logger.info(f"Signature verified successfully from {signer}")
        # If verification succeeds, return the original data
        return True, original_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parse Error: {str(e)}")
        return False, f"Invalid JSON format: {str(e)}"
    except KeyError as e:
        logger.error(f"Missing Key Error: {str(e)}")
        return False, f"Missing required field: {str(e)}"
    except Exception as e:
        logger.error(f"Verification Failed: {str(e)}")
        return False, f"Signature verification failed: {str(e)}"

async def send_credit_request(
    remote_agent_connections: dict,
    received_offers: dict,
    application_data: dict,
    tool_context=None,
    session_ids=None,
):
    """
    Sends a structured credit request (built by build_and_send_credit_request) to all remote loan agents.
    Generates a unique request_id for tracking and stores all responses under that ID.
    Waits for all responses or until a global timeout is reached.
    """
    request_id = str(uuid.uuid4())
    responses = []
    tasks = []
    agent_names = list(remote_agent_connections.keys())  

    async def send_to_agent(agent_name, connection):
        try:
            message_id = str(uuid.uuid4())
            context_id = None
            if session_ids is not None:
                context_id = session_ids.get(agent_name)
                if not context_id:
                    context_id = str(uuid.uuid4())
                    session_ids[agent_name] = context_id
            else:
                context_id = str(uuid.uuid4())

            # sign the intent
            application_data1 = sign_json_rsa(application_data)
            print("\n<------------------------ signed data --------------------------->\n")
            print(application_data1)
            print("\n<----------------------------------------------------------------->\n")
            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": json.dumps(application_data1)}],
                    "messageId": message_id,
                    "contextId": context_id,
                },
            }
            message_request = SendMessageRequest(
                id=message_id, params=MessageSendParams.model_validate(payload)
            )
            print(f"[{datetime.now()}] Sending message to agent: {agent_name}")

            send_start = datetime.now()
            send_response = await asyncio.wait_for(connection.send_message(message_request), timeout=PER_AGENT_TIMEOUT)
            send_end = datetime.now()
            print("<==================Send Response =====================>")
            print(send_response)
            print("<=====================================================>")

            print(f"[{send_end}] Received response from {agent_name} in {(send_end - send_start).total_seconds()} seconds")

            # verify signature
            response = send_response.root.result.artifacts[0].parts[0].root.text
            print("================================================")
            print(response)
            print("================================================")
            
            isValid = False
            offer = None
            
            try:
                isValid, offer = verify_json_rsa(response)
                if isValid:
                    print("Signature Verified Successfully")
                else:
                    print("Invalid Signature - continuing with unsigned response")
            except Exception as sig_error:
                print(f"Signature verification error: {str(sig_error)}")
                try:
                    offer = json.loads(response)
                    isValid = False  # Mark as unsigned but usable
                except:
                    offer = None

            response_content = None
            if hasattr(send_response, 'root') and send_response.root:
                if hasattr(send_response.root, 'model_dump_json'):
                    response_content = send_response.root.model_dump_json(exclude_none=True)
                else:
                    response_content = json.dumps(send_response.root)
            else:
                response_content = json.dumps(send_response)
            
            try:
                # Use the verified offer if signature verification passed
                if isValid and offer:
                    return {"bank": agent_name, "response": json.dumps(offer), "signature_verified": True}
                elif offer:
                    # Use unsigned but parsed offer
                    return {"bank": agent_name, "response": json.dumps(offer), "signature_verified": False}
                else:
                    json_content = json.loads(response_content)
                    return {"bank": agent_name, "response": json_content, "signature_verified": False}
            except Exception as parse_error:
                print(f"Failed to parse response from {agent_name}: {str(parse_error)}")
                print(f"Response content: {response_content[:500]}...")
                try:
                    raw_response = json.loads(response)
                    return {"bank": agent_name, "response": raw_response, "signature_verified": False}
                except:
                    return {"bank": agent_name, "error": f"Failed to parse response: {str(parse_error)}"}
        except asyncio.TimeoutError:
            print(f"Timeout sending message to {agent_name}")
            return {
                "bank": agent_name, 
                "error": f"Timeout: No response in {PER_AGENT_TIMEOUT}s",
                "error_type": "timeout",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error sending message to {agent_name}: {str(e)}")
            return {
                "bank": agent_name, 
                "error": f"Communication Error: {str(e)}",
                "error_type": "communication_error",
                "timestamp": datetime.now().isoformat()
            }



    print(f"LOOPING.............. {remote_agent_connections}")
    for agent_name, connection in remote_agent_connections.items():
        tasks.append(send_to_agent(agent_name, connection))

    try:
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=GLOBAL_TIMEOUT)
        
        for i, (agent_name, result) in enumerate(zip(agent_names, results)):
            if isinstance(result, Exception):
                print(f"Exception from {agent_name}: {result}")
                responses.append({
                    "bank": agent_name, 
                    "error": f"Agent Error: {str(result)}",
                    "error_type": "agent_exception",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                responses.append(result)
                
    except asyncio.TimeoutError:
        print(f"[{datetime.now()}] GLOBAL TIMEOUT: Not all agents responded in {GLOBAL_TIMEOUT} seconds")
        for i, agent_name in enumerate(agent_names):
            if i >= len(responses):
                responses.append({
                    "bank": agent_name, 
                    "error": f"Global Timeout: No response in {GLOBAL_TIMEOUT}s",
                    "error_type": "global_timeout",
                    "timestamp": datetime.now().isoformat()
                })
    except Exception as e:
        print(f"[{datetime.now()}] Error in asyncio.gather: {e}")
        for i, agent_name in enumerate(agent_names):
            if i >= len(responses):
                responses.append({
                    "bank": agent_name, 
                    "error": f"Gather Error: {str(e)}",
                    "error_type": "gather_error",
                    "timestamp": datetime.now().isoformat()
                })

    received_offers[request_id] = responses
    
    return (
        f"Credit request {request_id} sent to {len(remote_agent_connections)} bank agents. "
        f"Received {len([r for r in responses if 'error' not in r])} responses.\n"
        f"Responses: {json.dumps(responses, indent=2)}"
        f"\nRequest ID: {request_id}"
    )

async def build_and_send_credit_request(user_input: dict, remote_agent_connections: dict, received_offers: dict, tool_context=None, session_ids=None):
    """
    Build a complete credit request by merging user input with all fields from CorporateConfig,
    then send it using send_credit_request. Ensures all config values are mapped to the correct structure.
    """
    config = CorporateConfig()
    config_dict = config.to_dict()
    print("CorporateConfig:", config_dict)
    loc_data = {**config_dict, **user_input}
    print(f"BILD.............. {remote_agent_connections}")
    return await send_credit_request(
        remote_agent_connections=remote_agent_connections,
        received_offers=received_offers,
        application_data=loc_data,
        tool_context=tool_context,
        session_ids=session_ids
    )

async def select_best_loan_offer(loan_request_json: str, bank_offers_json: str) -> str:

    try:
        loan_request = json.loads(loan_request_json)
        bank_offers = json.loads(bank_offers_json)
        
        analyzer = LoanOfferAnalyzer()
        result = analyzer.analyze_loan_offers(loan_request, bank_offers)
        
        return json.dumps(result, indent=2)
    
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON input: {str(e)}", "bankid": None})
    except Exception as e:
        return json.dumps({"error": f"Analysis failed: {str(e)}", "bankid": None})

async def send_user_message(user_input: str, bank_name : str , remote_agent_connections: dict, received_offers: dict, tool_context=None, session_ids=None) -> str:
    responses = []
    tasks = []
    agent_names = list(remote_agent_connections.keys())

    async def send_to_agent(agent_name, connection):
        try:
            message_id = str(uuid.uuid4())
            context_id = None
            if session_ids is not None:
                context_id = session_ids.get(agent_name)
                if not context_id:
                    context_id = str(uuid.uuid4())
                    session_ids[agent_name] = context_id
            else:
                context_id = str(uuid.uuid4())
            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": json.dumps(user_input)}],
                    "messageId": message_id,
                    "contextId": context_id,
                },
            }
            message_request = SendMessageRequest(
                id=message_id, params=MessageSendParams.model_validate(payload)
            )
            print(f"[{datetime.now()}] Sending message to agent: {agent_name}")

            send_start = datetime.now()
            send_response = await asyncio.wait_for(connection.send_message(message_request), timeout=PER_AGENT_TIMEOUT)
            send_end = datetime.now()

            print(f"[{send_end}] Received response from {agent_name} in {(send_end - send_start).total_seconds()} seconds")

            response_content = None
            if hasattr(send_response, 'root') and send_response.root:
                if hasattr(send_response.root, 'model_dump_json'):
                    response_content = send_response.root.model_dump_json(exclude_none=True)
                else:
                    response_content = json.dumps(send_response.root)
            else:
                response_content = json.dumps(send_response)
            try:
                json_content = json.loads(response_content)
                return {"bank": agent_name, "response": json_content}
            except Exception as parse_error:
                return {"bank": agent_name, "error": f"Failed to parse response: {str(parse_error)}"}
        except Exception as e:
            return {"bank": agent_name, "error": str(e)}

    print(f"Negotiation.............. {remote_agent_connections}")

    for agent_name, connection in remote_agent_connections.items():
        print(f"{agent_name}...............")
        if bank_name == agent_name :
            print(f"Selected Agent: {agent_name}")
            tasks.append(send_to_agent(agent_name, connection))

    try:
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=GLOBAL_TIMEOUT)
        responses.extend(results)
    except asyncio.TimeoutError:
        print(f"[{datetime.now()}] GLOBAL TIMEOUT: Not all agents responded in {GLOBAL_TIMEOUT} seconds")
        for i, agent_name in enumerate(agent_names):
            if i >= len(responses):
                responses.append({"bank": agent_name, "error": f"Global Timeout: No response in {GLOBAL_TIMEOUT}s"})
    except Exception as e:
        print(f"[{datetime.now()}] Error in asyncio.gather: {e}")
        for i, agent_name in enumerate(agent_names):
            if i >= len(responses):
                responses.append({"bank": agent_name, "error": f"Gather Error: {str(e)}"})

    request_id = str(uuid.uuid4())
    received_offers[request_id] = responses

    return (
        f"Negotiation request {request_id} sent to {len(remote_agent_connections)} bank agents. "
        f"Received {len([r for r in responses if 'error' not in r])} responses.\n"
        f"Responses: {json.dumps(responses, indent=2)}"
        f"\nRequest ID: {request_id}"
    )

async def display_offers(received_offers: list, tool_context=None) -> list:
    return received_offers