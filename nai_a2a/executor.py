"""
AgentExecutor implementation for NAI.

This executor wraps the existing ADK agent to provide A2A compatibility.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import io
import traceback

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Message,
    Role,
    TextPart,
    DataPart,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent
)
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import new_task

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai.types import Content, Part
from nai.agent import root_agent
from api.utils.gemini import gemini_extract_text_from_file
from api.utils.gemini_update_profile import gemini_enrich_profile

from nai_a2a.exceptions import (
    NAIError,
    UserNotFoundException,
    ProfileIncompleteError,
    ExternalAPIError,
    DatabaseConnectionError,
    SkillNotFoundError
)

import os
import psycopg2
import requests

logger = logging.getLogger(__name__)

# Import native skills as they become available
NATIVE_SKILLS_AVAILABLE = False
try:
    logger.info("Attempting to import native skills...")
    from nai_a2a.skills.retrieve_user_profile import RetrieveUserProfileSkill
    logger.info("✓ RetrieveUserProfileSkill imported")
    from nai_a2a.skills.save_user_profile import SaveUserProfileSkill
    logger.info("✓ SaveUserProfileSkill imported")
    from nai_a2a.skills.find_job_matches import FindJobMatchesSkill
    logger.info("✓ FindJobMatchesSkill imported")
    from nai_a2a.skills.retrieve_vacancy import RetrieveVacancySkill
    logger.info("✓ RetrieveVacancySkill imported")
    from nai_a2a.skills.update_state import UpdateStateSkill
    logger.info("✓ UpdateStateSkill imported")
    NATIVE_SKILLS_AVAILABLE = True
    logger.info("✅ All native skills imported successfully!")
except ImportError as e:
    logger.error(f"❌ Failed to import native skills: {e}")
    logger.error(f"Import traceback: ", exc_info=True)
    logger.warning("Native skills not available, using ADK fallback")
    NATIVE_SKILLS_AVAILABLE = False

logger.info(f"NATIVE_SKILLS_AVAILABLE = {NATIVE_SKILLS_AVAILABLE}")

class NAIAgentExecutor(AgentExecutor):
    """
    A2A AgentExecutor that wraps the existing ADK agent.
    
    This implementation maintains compatibility with the existing ADK-based
    system while providing A2A protocol support with robust error handling.
    """
    
    def __init__(self):
        """Initialize the executor with ADK components"""
        try:
            # Database configuration
            db_user = os.getenv("DB_USER")
            db_pass = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_port = os.getenv("DB_PORT")
            db_name = os.getenv("DB_NAME")
            
            if not all([db_user, db_pass, db_host, db_port, db_name]):
                raise DatabaseConnectionError(
                    "initialization",
                    Exception("Missing database configuration in environment variables")
                )
            
            db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            
            # Initialize ADK components
            self.session_service = DatabaseSessionService(db_url=db_url)
            self.runner = Runner(
                agent=root_agent,
                app_name="nai_app",
                session_service=self.session_service
            )
            
            logger.info("NAI Agent Executor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NAI Agent Executor: {e}")
            raise DatabaseConnectionError("executor initialization", e)
        
    async def execute(self, 
                     context: RequestContext,
                     event_queue: EventQueue) -> None:
        """
        Execute a request by delegating to the ADK agent.
        
        Args:
            context: Request context with metadata
            event_queue: Queue for publishing events back to client
        """
        try:
            # Extract user_id with better error handling
            user_id = await self._extract_user_id(context)
            logger.info(f"Processing request for user: {user_id}")
            
            # Check if this is a native skill invocation
            skill_name = self._extract_skill_name(context)
            logger.info(f"Extracted skill name: {skill_name}, NATIVE_SKILLS_AVAILABLE: {NATIVE_SKILLS_AVAILABLE}")
            
            if skill_name and NATIVE_SKILLS_AVAILABLE:
                # Try to execute native skill first
                logger.info(f"🎯 NATIVE SKILL PATH - Attempting to execute native skill: {skill_name}")
                success = await self._execute_native_skill(
                    skill_name, user_id, context, event_queue
                )
                if success:
                    logger.info(f"✅ NATIVE SKILL SUCCESS - {skill_name} handled the request successfully")
                    return  # Native skill handled the request
                else:
                    logger.info(f"❌ NATIVE SKILL FAILED - {skill_name} could not handle the request, falling back to ADK")
            
            # Fall back to ADK agent
            logger.info("🔄 ADK TOOL PATH - Using ADK agent as fallback")
            # Convert A2A message to ADK format
            adk_content = await self._convert_message_to_adk(context.message)
            
            # Map skill name to appropriate prompt if this is a skill invocation
            skill_prompt = self._map_skill_to_prompt(context.message, context)
            if skill_prompt:
                adk_content = Content(parts=[Part(text=skill_prompt)])
            
            # Create task for long-running operations
            if context.task_id:
                await self._create_task(context.task_id, user_id, event_queue)
            
            # Run the ADK agent with error handling
            response_text = await self._run_adk_agent(
                adk_content, user_id, context, event_queue
            )
            
            # Handle response
            await self._handle_response(
                response_text, context, event_queue, user_id
            )
            
        except UserNotFoundException as e:
            await self._handle_user_not_found(e, context, event_queue)
        except ProfileIncompleteError as e:
            await self._handle_profile_incomplete(e, context, event_queue)
        except ExternalAPIError as e:
            await self._handle_external_api_error(e, context, event_queue)
        except DatabaseConnectionError as e:
            await self._handle_database_error(e, context, event_queue)
        except SkillNotFoundError as e:
            await self._handle_skill_not_found(e, context, event_queue)
        except NAIError as e:
            await self._handle_nai_error(e, context, event_queue)
        except Exception as e:
            await self._handle_generic_error(e, context, event_queue)
    
    async def cancel(self, 
                    context: RequestContext,
                    event_queue: EventQueue) -> None:
        """
        Cancel a running task.
        
        Currently, ADK doesn't support cancellation, so we just update the status.
        """
        logger.info(f"Cancel requested for task {context.task_id}")
        
        try:
            if context.task_id:
                # Update task status to canceled
                status_update = TaskStatusUpdateEvent(
                    taskId=context.task_id,
                    contextId=context.context_id or context.task_id,  # Use task_id as fallback
                    final=True,
                    status=TaskStatus(
                        state=TaskState.canceled,
                        metadata={"canceled_at": datetime.utcnow().isoformat()}
                    )
                )
                await event_queue.enqueue_event(status_update)
            
            # Send cancellation message
            message = new_agent_text_message("A tarefa foi cancelada com sucesso.")
            await event_queue.enqueue_event(message)
            
        except Exception as e:
            logger.error(f"Error during task cancellation: {e}")
            error_message = new_agent_text_message(
                "Erro ao cancelar a tarefa. Por favor, tente novamente."
            )
            await event_queue.enqueue_event(error_message)
    
    # Helper methods for better organization
    
    def _extract_skill_name(self, context: RequestContext) -> Optional[str]:
        """Extract skill name from context"""
        # Debug the entire message structure
        if context.message:
            logger.debug(f"Message structure: messageId={context.message.messageId}, role={context.message.role}")
            logger.debug(f"Message metadata: {context.message.metadata}")
            logger.debug(f"Message has metadata attr: {hasattr(context.message, 'metadata')}")
            
            # Try to get skill from message metadata first
            if context.message.metadata:
                skill = context.message.metadata.get("skill")
                if skill:
                    logger.debug(f"Skill from message metadata: {skill}")
                    return skill
        else:
            logger.debug("No message in context")
        
        # Configuration doesn't have metadata in A2A protocol
        logger.debug(f"No skill found in message metadata")
        return None
    
    async def _execute_native_skill(self, skill_name: str, user_id: str,
                                   context: RequestContext, event_queue: EventQueue) -> bool:
        """
        Execute a native A2A skill if available.
        
        Returns:
            True if skill was executed successfully, False if should fall back to ADK
        """
        try:
            logger.info(f"Attempting to execute native skill: {skill_name}")
            
            if skill_name == "retrieve_user_profile":
                skill = RetrieveUserProfileSkill()
                
                # Create task if needed
                if context.task_id:
                    await self._create_task(context.task_id, user_id, event_queue)
                
                # Execute skill
                profile_data = await skill.execute(user_id)
                
                # Format response
                formatted_response = skill.format_profile_for_display(profile_data)
                
                # Send response
                message = new_agent_text_message(formatted_response)
                await event_queue.enqueue_event(message)
                
                # Update task status
                if context.task_id:
                    await self._update_task_completed(context, event_queue, user_id, {
                        "skill": skill_name,
                        "native": True,
                        "profile_exists": not profile_data.get("_metadata", {}).get("is_empty")
                    })
                
                logger.info(f"Native skill {skill_name} executed successfully")
                return True
            
            elif skill_name == "save_user_profile":
                skill = SaveUserProfileSkill()
                
                # Create task if needed
                if context.task_id:
                    await self._create_task(context.task_id, user_id, event_queue)
                
                # Extract profile data from metadata
                profile_data = {}
                if context.message and context.message.metadata:
                    profile_data = context.message.metadata.get("profile_data", {})
                
                if not profile_data:
                    raise ValidationError("Profile data is required in metadata", {"field": "profile_data"})
                
                # Execute skill
                result = await skill.execute(user_id, profile_data)
                
                # Send response
                message = new_agent_text_message(result["message"])
                await event_queue.enqueue_event(message)
                
                # Update task status
                if context.task_id:
                    await self._update_task_completed(context, event_queue, user_id, {
                        "skill": skill_name,
                        "native": True,
                        "profile_saved": result.get("profile_saved", False)
                    })
                
                logger.info(f"Native skill {skill_name} executed successfully")
                return True
            
            elif skill_name == "find_job_matches" or skill_name == "retrieve_match":
                skill = FindJobMatchesSkill()
                
                # Create task if needed
                if context.task_id:
                    await self._create_task(context.task_id, user_id, event_queue)
                
                # Extract limit from metadata
                limit = 10
                if context.message and context.message.metadata:
                    limit = context.message.metadata.get("limit", 10)
                
                # Execute skill
                result = await skill.execute(user_id, limit=limit)
                
                # Send response
                message = new_agent_text_message(result["message"])
                await event_queue.enqueue_event(message)
                
                # Update task status
                if context.task_id:
                    await self._update_task_completed(context, event_queue, user_id, {
                        "skill": skill_name,
                        "native": True,
                        "matches_found": result.get("total_found", 0),
                        "status": result["status"]
                    })
                
                logger.info(f"Native skill {skill_name} executed successfully")
                return True
            
            elif skill_name == "retrieve_vacancy":
                skill = RetrieveVacancySkill()
                
                # Create task if needed
                if context.task_id:
                    await self._create_task(context.task_id, user_id, event_queue)
                
                # Extract search term from metadata or message
                search_term = ""
                if context.message and context.message.metadata:
                    search_term = context.message.metadata.get("search_term", "")
                
                # If no search term in metadata, try to extract from message text
                if not search_term and context.message and context.message.parts:
                    for part in context.message.parts:
                        if part.get("text"):
                            # Simple extraction - take text after "buscar vagas" or similar
                            text = part["text"]
                            if "buscar vagas" in text.lower():
                                search_term = text.lower().split("buscar vagas", 1)[1].strip()
                            elif "vagas de" in text.lower():
                                search_term = text.lower().split("vagas de", 1)[1].strip()
                            elif "vagas para" in text.lower():
                                search_term = text.lower().split("vagas para", 1)[1].strip()
                            break
                
                if not search_term:
                    raise ValidationError("Search term is required for vacancy search", {"field": "search_term"})
                
                # Execute skill
                result = await skill.execute(search_term)
                
                # Format response
                formatted_response = skill.format_vacancies_for_display(result)
                
                # Send response
                message = new_agent_text_message(formatted_response)
                await event_queue.enqueue_event(message)
                
                # Update task status
                if context.task_id:
                    await self._update_task_completed(context, event_queue, user_id, {
                        "skill": skill_name,
                        "native": True,
                        "vacancies_found": result.get("count", 0),
                        "search_term": search_term
                    })
                
                logger.info(f"Native skill {skill_name} executed successfully")
                return True
            
            elif skill_name == "update_state":
                skill = UpdateStateSkill()
                
                # Create task if needed
                if context.task_id:
                    await self._create_task(context.task_id, user_id, event_queue)
                
                # Extract content and current profile from metadata
                content = ""
                current_profile = None
                
                if context.message and context.message.metadata:
                    content = context.message.metadata.get("content", "")
                    current_profile = context.message.metadata.get("current_profile")
                
                # If no content in metadata, use message text
                if not content and context.message and context.message.parts:
                    for part in context.message.parts:
                        if part.get("text"):
                            content = part["text"]
                            break
                
                if not content:
                    raise ValidationError("Content is required for profile update", {"field": "content"})
                
                # Execute skill
                result = await skill.execute(user_id, content, current_profile)
                
                # Format response
                formatted_response = skill.format_update_result(result)
                
                # Send response
                message = new_agent_text_message(formatted_response)
                await event_queue.enqueue_event(message)
                
                # Update task status
                if context.task_id:
                    await self._update_task_completed(context, event_queue, user_id, {
                        "skill": skill_name,
                        "native": True,
                        "profile_updated": True,
                        "content_length": len(content)
                    })
                
                logger.info(f"Native skill {skill_name} executed successfully")
                return True
            
            # Add other native skills here as they are implemented
            
            logger.info(f"No native implementation for skill: {skill_name}")
            return False
            
        except Exception as e:
            logger.error(f"Error executing native skill {skill_name}: {e}")
            # Re-raise to be handled by main error handlers
            raise
    
    async def _update_task_completed(self, context: RequestContext, event_queue: EventQueue,
                                   user_id: str, metadata: Dict[str, Any] = None):
        """Update task status to completed with metadata"""
        if context.task_id:
            status_update = TaskStatusUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id or context.task_id,  # Use task_id as fallback
                final=True,
                status=TaskStatus(
                    state=TaskState.completed,
                    metadata={
                        "user_id": user_id,
                        "completed_at": datetime.utcnow().isoformat(),
                        **(metadata or {})
                    }
                )
            )
            await event_queue.enqueue_event(status_update)
    
    async def _extract_user_id(self, context: RequestContext) -> str:
        """Extract user_id from context with validation"""
        user_id = None
        
        # Try to get from message metadata
        if context.message and context.message.metadata:
            user_id = context.message.metadata.get("user_id")
            if user_id:
                logger.debug(f"User ID from message metadata: {user_id}")
        
        # Generate fallback ID
        if not user_id:
            user_id = f"a2a_{context.context_id}" if context.context_id else f"a2a_{context.task_id or id(context)}"
            logger.warning(f"No user_id provided, using generated ID: {user_id}")
        
        return user_id
    
    async def _create_task(self, task_id: str, user_id: str, event_queue: EventQueue):
        """Create and publish task for long-running operations"""
        # Create a task creation event
        task_create_event = Task(
            id=task_id,
            contextId=task_id,  # Using task_id as context_id for now
            status=TaskStatus(
                state=TaskState.working,
                metadata={
                    "user_id": user_id,
                    "started_at": datetime.utcnow().isoformat()
                }
            ),
            history=[]
        )
        await event_queue.enqueue_event(task_create_event)
    
    async def _run_adk_agent(self, content: Content, user_id: str, 
                            context: RequestContext, event_queue: EventQueue) -> str:
        """Run ADK agent with proper error handling"""
        response_text = ""
        
        try:
            # Check if session exists, create if not (like main.py does)
            session = await self.session_service.get_session(
                app_name="nai_app", 
                user_id=user_id, 
                session_id=user_id
            )
            if session is None:
                logger.debug(f"Creating new session for user: {user_id}")
                await self.session_service.create_session(
                    app_name="nai_app", 
                    user_id=user_id, 
                    session_id=user_id
                )
            
            # Check if this is a streaming request
            # In A2A, the streaming is determined by the request method (message/stream vs message/send)
            # We detect this by checking if the event_queue is expecting streaming
            is_streaming = True  # For A2A, we always stream events to the queue
            
            async for event in self.runner.run_async(
                new_message=content,
                user_id=user_id,
                session_id=user_id
            ):
                logger.debug(f"ADK event type: {type(event)}, attributes: {dir(event)}")
                
                # Try different ways to get text from event
                event_text = None
                if hasattr(event, 'text') and event.text:
                    event_text = event.text
                elif hasattr(event, 'content') and hasattr(event.content, 'parts'):
                    # Extract text from content parts
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            event_text = part.text
                            break
                
                if event_text:
                    logger.debug(f"Extracted text: {event_text[:100]}...")
                    response_text = event_text
                    
                    # For streaming responses, publish intermediate messages
                    if is_streaming:
                        message = new_agent_text_message(response_text)
                        await event_queue.enqueue_event(message)
                        logger.info(f"Enqueued message: {response_text[:100]}...")
                        
        except psycopg2.Error as e:
            raise DatabaseConnectionError("agent execution", e)
        except requests.RequestException as e:
            raise ExternalAPIError("ADK backend", response_text=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in ADK agent: {e}")
            raise
            
        return response_text
    
    async def _handle_response(self, response_text: str, context: RequestContext,
                              event_queue: EventQueue, user_id: str):
        """Handle agent response with proper completion status"""
        # For A2A, messages are already sent during streaming in _run_adk_agent
        # So we only need to handle the case where no response was generated
        if not response_text:
            # No response generated
            error_message = new_agent_text_message(
                "Desculpe, não consegui gerar uma resposta. "
                "Por favor, reformule sua pergunta."
            )
            await event_queue.enqueue_event(error_message)
        
        # Update task status if applicable
        if context.task_id:
            status_update = TaskStatusUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id or context.task_id,  # Use task_id as fallback
                final=True,
                status=TaskStatus(
                    state=TaskState.completed,
                    metadata={
                        "user_id": user_id,
                        "completed_at": datetime.utcnow().isoformat(),
                        "response_length": len(response_text) if response_text else 0
                    }
                )
            )
            await event_queue.enqueue_event(status_update)
    
    # Error handlers
    
    async def _handle_user_not_found(self, error: UserNotFoundException,
                                    context: RequestContext, event_queue: EventQueue):
        """Handle user not found error with recovery suggestion"""
        logger.warning(f"User not found: {error.user_id}")
        
        message = new_agent_text_message(
            "Não encontrei seu perfil cadastrado. "
            "Vamos criar um novo perfil? Me conte sobre sua experiência profissional, "
            "formação e objetivos de carreira."
        )
        await event_queue.enqueue_event(message)
        
        # Update task status with specific error
        await self._update_task_error(context, event_queue, error, "waiting_for_profile")
    
    async def _handle_profile_incomplete(self, error: ProfileIncompleteError,
                                       context: RequestContext, event_queue: EventQueue):
        """Handle incomplete profile with specific field requests"""
        logger.info(f"Profile incomplete for {error.operation}: {error.missing_fields}")
        
        fields_text = ", ".join(error.missing_fields)
        message = new_agent_text_message(
            f"Seu perfil está incompleto para {error.operation}. "
            f"Preciso das seguintes informações: {fields_text}. "
            "Por favor, me forneça esses dados para continuar."
        )
        await event_queue.enqueue_event(message)
        
        await self._update_task_error(context, event_queue, error, "waiting_for_input")
    
    async def _handle_external_api_error(self, error: ExternalAPIError,
                                       context: RequestContext, event_queue: EventQueue):
        """Handle external API errors with retry suggestion"""
        logger.error(f"External API error: {error.service} - {error.status_code}")
        
        if error.status_code and error.status_code >= 500:
            message_text = (
                f"O serviço {error.service} está temporariamente indisponível. "
                "Por favor, tente novamente em alguns minutos."
            )
        elif error.status_code == 404:
            message_text = (
                f"Não encontrei a informação solicitada no serviço {error.service}. "
                "Verifique os dados e tente novamente."
            )
        else:
            message_text = (
                f"Erro ao acessar o serviço {error.service}. "
                "Nossa equipe foi notificada e está trabalhando na solução."
            )
        
        message = new_agent_text_message(message_text)
        await event_queue.enqueue_event(message)
        
        await self._update_task_error(context, event_queue, error, "failed")
    
    async def _handle_database_error(self, error: DatabaseConnectionError,
                                   context: RequestContext, event_queue: EventQueue):
        """Handle database errors"""
        logger.error(f"Database error during {error.operation}: {error.original_error}")
        
        message = new_agent_text_message(
            "Estamos com problemas técnicos temporários. "
            "Por favor, tente novamente em alguns instantes. "
            "Se o problema persistir, entre em contato com o suporte."
        )
        await event_queue.enqueue_event(message)
        
        await self._update_task_error(context, event_queue, error, "failed")
    
    async def _handle_skill_not_found(self, error: SkillNotFoundError,
                                    context: RequestContext, event_queue: EventQueue):
        """Handle skill not found error"""
        logger.warning(f"Skill not found: {error.skill_name}")
        
        message = new_agent_text_message(
            f"A funcionalidade '{error.skill_name}' não está disponível. "
            "Por favor, verifique o nome da função ou consulte a lista de "
            "funcionalidades disponíveis."
        )
        await event_queue.enqueue_event(message)
        
        await self._update_task_error(context, event_queue, error, "failed")
    
    async def _handle_nai_error(self, error: NAIError,
                              context: RequestContext, event_queue: EventQueue):
        """Handle generic NAI errors"""
        logger.error(f"NAI error: {error.message} - {error.details}")
        
        message = new_agent_text_message(error.message)
        await event_queue.enqueue_event(message)
        
        await self._update_task_error(context, event_queue, error, "failed")
    
    async def _handle_generic_error(self, error: Exception,
                                  context: RequestContext, event_queue: EventQueue):
        """Handle unexpected errors"""
        logger.error(f"Unexpected error in NAI executor: {error}", exc_info=True)
        
        # Log full traceback for debugging
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        message = new_agent_text_message(
            "Desculpe, ocorreu um erro inesperado. "
            "Nossa equipe foi notificada e está trabalhando para resolver. "
            "Por favor, tente novamente mais tarde."
        )
        await event_queue.enqueue_event(message)
        
        await self._update_task_error(context, event_queue, error, "failed")
    
    async def _update_task_error(self, context: RequestContext, event_queue: EventQueue,
                                error: Exception, state: str = "failed"):
        """Update task status with error information"""
        if context.task_id:
            task_state = TaskState.failed if state == "failed" else TaskState.input_required
            
            status_update = TaskStatusUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id or context.task_id,  # Use task_id as fallback
                final=True,
                status=TaskStatus(
                    state=task_state,
                    metadata={
                        "error": str(error),
                        "error_type": error.__class__.__name__,
                        "error_details": getattr(error, 'details', {}),
                        "failed_at": datetime.utcnow().isoformat()
                    }
                )
            )
            await event_queue.enqueue_event(status_update)
    
    async def _convert_message_to_adk(self, message: Optional[Message]) -> Content:
        """Convert A2A Message to ADK Content format"""
        parts = []
        
        if not message:
            return Content(parts=[Part(text="")])
        
        for part in message.parts:
            if isinstance(part, TextPart):
                parts.append(Part(text=part.text))
            elif isinstance(part, DataPart):
                # Process file data through Gemini like the original implementation
                if part.data:
                    try:
                        # Create a temporary file-like object
                        file_obj = io.BytesIO(part.data)
                        file_obj.name = getattr(part, 'filename', 'uploaded_file')
                        
                        # Extract text using Gemini
                        extracted_text = await gemini_extract_text_from_file(file_obj)
                        if extracted_text:
                            parts.append(Part(text=f"Conteúdo do arquivo {file_obj.name}:\n{extracted_text}"))
                        else:
                            parts.append(Part(text=f"Não foi possível extrair texto do arquivo {file_obj.name}"))
                    except Exception as e:
                        logger.error(f"Error processing file data: {e}")
                        parts.append(Part(text=f"Erro ao processar arquivo: {str(e)}"))
        
        # Ensure we always have at least one part
        if not parts:
            parts.append(Part(text=""))
            
        return Content(parts=parts)
    
    def _map_skill_to_prompt(self, message: Optional[Message], context: RequestContext) -> Optional[str]:
        """
        Map A2A skill invocation to appropriate prompt for ADK agent.
        
        Returns None if this is a general chat message.
        """
        # Check if this is a skill invocation through message metadata
        skill_name = None
        if message and message.metadata:
            skill_name = message.metadata.get("skill")
        
        if not skill_name or not message:
            return None
        
        # Extract text from message
        text_parts = [p.text for p in message.parts if isinstance(p, TextPart)]
        user_input = " ".join(text_parts)
        
        # Map skills to prompts
        skill_prompts = {
            "retrieve_user_profile": "mostre meu perfil completo",
            "save_user_profile": f"atualize meu perfil com: {user_input}",
            "find_job_matches": "encontre vagas compatíveis com meu perfil",
            "retrieve_vacancy": f"buscar vagas de {user_input}",
            "update_state": f"atualize meu perfil com: {user_input}",
            "analyze_skill_gaps": f"analise as lacunas de habilidades para: {user_input}",
            "recommend_courses": "recomende cursos para mim",
            "chat": user_input  # General chat uses the original input
        }
        
        prompt = skill_prompts.get(skill_name)
        if not prompt:
            raise SkillNotFoundError(skill_name)
            
        return prompt