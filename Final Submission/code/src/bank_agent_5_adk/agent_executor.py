import asyncio
import logging
from collections.abc import AsyncGenerator
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    FilePart,
    FileWithBytes,
    FileWithUri,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.adk.events import Event
from google.genai import types
import hashlib
import json
import base64
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_bank_crypto_manager = None

def get_bank_crypto_manager():
    """Get or create crypto manager for bank agent 5"""
    global _bank_crypto_manager
    if _bank_crypto_manager is None:
        _bank_crypto_manager = CryptoManager("bank_agent_5")
    return _bank_crypto_manager

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
    crypto_manager = get_bank_crypto_manager()
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

class TachyonAgentExecutor(AgentExecutor):
    """A Tachyon-compatible AgentExecutor for Byte Bank's ADK-based Agent."""

    def __init__(self, runner: Runner):
        self.runner = runner
        self._running_sessions = {}

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
    ) -> None:
        logger.info(f"Processing request for session {session_id}")
        logger.info(f"Message content: {new_message}")
        
        session_obj = await self._upsert_session(session_id)
        session_id = session_obj.id
        logger.info(f"Session created/retrieved: {session_id}")
        
        # Initialize response variable to avoid uninitialized access
        response = None
        response_parts = []
        
        try:
            async for event in self.runner.run_async(
                user_id="byte_bank_agent",
                session_id=session_id,
                new_message=new_message
            ):
                if event.is_final_response():
                    response_text = ""
                    if event.content and event.content.parts and event.content.parts[0].text:
                        response_text = event.content.parts[0].text
                        logger.info("\n<------------------------ Message ---------------------->\n")
                        logger.info(response_text)
                        logger.info("\n<------------------------------------------------------->\n")

                        try:
                            response = sign_json_rsa({"message": response_text})
                            logger.info("Response signed successfully")
                        except Exception as sign_error:
                            logger.error(f"Failed to sign response: {str(sign_error)}")
                            response = {"message": response_text, "signature_error": str(sign_error)}
                        
                        logger.info("\n<------------------------ Message ---------------------->\n")
                        logger.info(response)
                        logger.info("\n<------------------------------------------------------->\n")
                        
                    response_parts = convert_genai_parts_to_a2a([
                        types.Part(text=json.dumps(response))
                    ])
                    logger.info("\n<------------------------ response_parts ---------------------->\n")
                    logger.info(f"Yielding response: {response_parts}")
                    logger.info("\n<------------------------ response_parts ---------------------->\n")
                    await task_updater.add_artifact(response_parts)
                    await task_updater.complete()
                    break
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            # Create error response if response wasn't initialized
            if response is None:
                response = {"error": f"Processing failed: {str(e)}"}
            
            error_parts = convert_genai_parts_to_a2a([
                types.Part(text=json.dumps(response))
            ])
            await task_updater.add_artifact(error_parts)
            await task_updater.complete()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        
        logger.info(f"Execute called with context: task_id={context.task_id}, context_id={context.context_id}")
        logger.info(f"Message: {context.message}")
        
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            logger.info("Submitting new task")
            await updater.submit()
        logger.info("Starting work")
        await updater.start_work()

        logger.info("\n<------------------------ Message ---------------------->\n")
        logger.info(context.message.parts[0])
        logger.info("\n<------------------------------------------------------->\n")

        logger.info("\n<------------------------ Message ---------------------->\n")
        application_data = context.message.parts[0].root.text
        logger.info(application_data)
        logger.info(type(application_data))
        logger.info("\n<------------------------------------------------------->\n")

        logger.info("\n<------------------------ Message ---------------------->\n")
        try:
            isValid, application_data = verify_json_rsa(application_data)
            if isValid:
                logger.info("Signature verification successful")
                logger.info(application_data)
                logger.info(type(application_data))
                context.message.parts[0].root.text = json.dumps(application_data)
            else:
                logger.warning("Signature verification failed, but continuing with unsigned data")
                logger.info("Invalid signature data:", application_data)
        except Exception as e:
            logger.error(f"Error during signature verification: {str(e)}")
            logger.info("Continuing with original data due to verification error")
        logger.info("\n<------------------------------------------------------->\n")

        
        converted_parts = convert_a2a_parts_to_genai(context.message.parts)
        logger.info(f"Converted parts: {converted_parts}")
        
        user_content = types.UserContent(parts=converted_parts)
        logger.info(f"User content: {user_content}")
        
        await self._process_request(
            user_content,
            context.context_id,
            updater,
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str):
        session = await self.runner.session_service.get_session(
            app_name=self.runner.app_name, user_id="byte_bank_agent", session_id=session_id
        )
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id="byte_bank_agent",
                session_id=session_id,
            )
        if session is None:
            raise RuntimeError(f"Failed to get or create session: {session_id}")
        return session


def convert_a2a_parts_to_genai(parts: list[Part]) -> list[types.Part]:
    """Convert a list of A2A Part types into a list of Google Gen AI Part types."""
    result = []
    for part in parts:
        root = part.root
        if isinstance(root, TextPart):
            result.append(types.Part(text=root.text))
        elif isinstance(root, FilePart):
            if isinstance(root.file, FileWithUri):
                result.append(types.Part(
                    file_data=types.FileData(
                        file_uri=root.file.uri, mime_type=root.file.mimeType
                    )
                ))
            elif isinstance(root.file, FileWithBytes):
                result.append(types.Part(
                    inline_data=types.Blob(
                        data=root.file.bytes.encode("utf-8"),
                        mime_type=root.file.mimeType or "application/octet-stream",
                    )
                ))
            else:
                raise ValueError(f"Unsupported file type: {type(root.file)}")
        else:
            raise ValueError(f"Unsupported part type: {type(part)}")
    return result

def convert_genai_parts_to_a2a(parts: list[types.Part]) -> list[Part]:
    """Convert a list of Google Gen AI Part types into a list of A2A Part types."""
    result = []
    for part in parts:
        if part.text:
            result.append(Part(root=TextPart(text=part.text)))
        elif part.file_data:
            if not part.file_data.file_uri:
                raise ValueError("File URI is missing")
            result.append(Part(
                root=FilePart(
                    file=FileWithUri(
                        uri=part.file_data.file_uri,
                        mimeType=part.file_data.mime_type,
                    )
                )
            ))
        elif part.inline_data:
            if not part.inline_data.data:
                raise ValueError("Inline data is missing")
            result.append(Part(
                root=FilePart(
                    file=FileWithBytes(
                        bytes=part.inline_data.data.decode("utf-8"),
                        mimeType=part.inline_data.mime_type,
                    )
                )
            ))
    return result
