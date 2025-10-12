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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TachyonWellsFargoAgentExecutor(AgentExecutor):
    """A Tachyon-compatible AgentExecutor for Wells Fargo Bank's ADK-based Agent."""

    def __init__(self, runner: Runner):
        self.runner = runner
        self._running_sessions = {}

    def _run_agent(
        self, session_id, new_message: types.Content
    ) -> AsyncGenerator[Event, None]:
        return self.runner.run_async(
            session_id=session_id, user_id="wells_fargo_agent", new_message=new_message
        )

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

        # Simplified processing for Tachyon compatibility
        try:
            # Process the message directly with the agent
            response_text = await self._process_message_directly(new_message)
            
            # Convert to A2A format
            response_parts = convert_genai_parts_to_a2a([
                types.Part(text=response_text)
            ])
            
            logger.info(f"Yielding response: {response_parts}")
            await task_updater.add_artifact(response_parts)
            await task_updater.complete()
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            # Send error response
            error_parts = convert_genai_parts_to_a2a([
                types.Part(text=f"Error processing request: {str(e)}")
            ])
            await task_updater.add_artifact(error_parts)
            await task_updater.complete()

    async def _process_message_directly(self, new_message: types.Content) -> str:
        """Process message directly without complex event handling."""
        try:
            # Extract text from message
            message_text = ""
            if new_message and new_message.parts:
                for part in new_message.parts:
                    if part.text:
                        message_text += part.text
            
            logger.info(f"Processing message text: {message_text}")
            
            # Import the credit processing function
            from agent import process_credit_request
            
            # Call the credit processing function directly
            result = process_credit_request(message_text)
            
            # Parse the result to extract the actual response
            import json
            try:
                result_data = json.loads(result)
                if "process_credit_request_response" in result_data:
                    response_data = result_data["process_credit_request_response"]
                    if "result" in response_data:
                        return response_data["result"]
                return result
            except json.JSONDecodeError:
                return result
                
        except Exception as e:
            logger.error(f"Error in direct message processing: {e}")
            return f"Error processing credit request: {str(e)}"

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        print(f"\n{'='*60}")
        print(f"TACHYON AGENT EXECUTOR EXECUTE CALLED!")
        print(f"Task ID: {context.task_id}")
        print(f"Context ID: {context.context_id}")
        print(f"Message: {context.message}")
        print(f"{'='*60}\n")
        
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
            app_name=self.runner.app_name, user_id="wells_fargo_agent", session_id=session_id
        )
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id="wells_fargo_agent",
                session_id=session_id,
            )
        if session is None:
            raise RuntimeError(f"Failed to get or create session: {session_id}")
        return session


def convert_a2a_parts_to_genai(parts: list[Part]) -> list[types.Part]:
    """Convert a list of A2A Part types into a list of Google Gen AI Part types."""
    return [convert_a2a_part_to_genai(part) for part in parts]


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """Convert a single A2A Part type into a Google Gen AI Part type."""
    root = part.root
    if isinstance(root, TextPart):
        return types.Part(text=root.text)
    if isinstance(root, FilePart):
        if isinstance(root.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=root.file.uri, mime_type=root.file.mimeType
                )
            )
        if isinstance(root.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=root.file.bytes.encode("utf-8"),
                    mime_type=root.file.mimeType or "application/octet-stream",
                )
            )
        raise ValueError(f"Unsupported file type: {type(root.file)}")
    raise ValueError(f"Unsupported part type: {type(part)}")


def convert_genai_parts_to_a2a(parts: list[types.Part]) -> list[Part]:
    """Convert a list of Google Gen AI Part types into a list of A2A Part types."""
    return [
        convert_genai_part_to_a2a(part)
        for part in parts
        if (part.text or part.file_data or part.inline_data)
    ]


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """Convert a single Google Gen AI Part type into an A2A Part type."""
    if part.text:
        return Part(root=TextPart(text=part.text))
    if part.file_data:
        if not part.file_data.file_uri:
            raise ValueError("File URI is missing")
        return Part(
            root=FilePart(
                file=FileWithUri(
                    uri=part.file_data.file_uri,
                    mimeType=part.file_data.mime_type,
                )
            )
        )
    if part.inline_data:
        if not part.inline_data.data:
            raise ValueError("Inline data is missing")
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=part.inline_data.data.decode("utf-8"),
                    mimeType=part.inline_data.mime_type,
                )
            )
        )
    raise ValueError(f"Unsupported part type: {part}")
