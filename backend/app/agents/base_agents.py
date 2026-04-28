"""
LangChain-based agents for automated task execution.
"""

import logging
from typing import Optional, Any, Dict
from app.core.config import settings
from app.services import gemini_service

logger = logging.getLogger(__name__)

# Try to import LangChain components - make optional for development
try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    ConversationBufferMemory = None
    logger.warning("LangChain not fully installed - agent memory will not work")

try:
    from langchain.chat_models import ChatOpenAI
except ImportError:
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        ChatOpenAI = None


class ChatAgent:
    """Main conversational AI agent."""

    def __init__(self, user_id: str):
        """
        Initialize chat agent.

        Args:
            user_id: Firebase user ID
        """
        self.user_id = user_id
        
        # Initialize memory if LangChain is available
        if ConversationBufferMemory:
            self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        else:
            self.memory = None

        # Initialize LLM (use OpenAI if available and installed, otherwise use Gemini service)
        self.llm = None
        if settings.OPENAI_API_KEY and ChatOpenAI:
            try:
                self.llm = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model="gpt-4",
                    temperature=0.7,
                )
            except Exception as e:
                logger.warning(f"ChatOpenAI initialization failed: {e}")

        logger.info(f"Chat agent initialized for user {user_id}")

    async def chat(self, user_message: str) -> str:
        """
        Process user message and generate response.

        Args:
            user_message: User's input message

        Returns:
            Assistant's response
        """
        try:
            # Use Gemini service for response generation
            if not gemini_service:
                return "Gemini service not available. Please configure Google AI API key."
            
            response = await gemini_service.analyze_text(user_message)
            
            # Add to memory if available
            if self.memory:
                self.memory.save_context({"input": user_message}, {"output": response})
            
            return response
        except Exception as e:
            # Gracefully handle Gemini API errors
            error_msg = str(e).lower()
            if "api_key" in error_msg or "api key" in error_msg:
                logger.warning(f"Gemini API key error: {e}")
                return "I'm having trouble reaching my AI service. Please check your API configuration."
            elif "timeout" in error_msg:
                logger.warning(f"Gemini timeout: {e}")
                return "Sorry, the response took too long. Please try again."
            else:
                logger.error(f"Chat agent failed: {e}")
                return f"Sorry, I encountered an error: {str(e)[:100]}"

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result
        """
        try:
            if not gemini_service:
                return {"sentiment": "unknown", "score": 0.5, "explanation": "Gemini service not available"}
            
            prompt = f"""Analyze the sentiment of this text and respond with JSON format:
{{"sentiment": "positive/negative/neutral", "score": 0.0-1.0, "explanation": "brief explanation"}}

Text: {text}"""
            response = await gemini_service.analyze_text(text, prompt=prompt)
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"sentiment": "unknown", "score": 0.5, "explanation": "Failed to analyze"}


class WhatsappAgent:
    """Agent for handling WhatsApp messages and actions."""

    def __init__(self, user_id: str):
        """
        Initialize WhatsApp agent.

        Args:
            user_id: Firebase user ID
        """
        self.user_id = user_id
        logger.info(f"WhatsApp agent initialized for user {user_id}")

    async def process_message(self, message: str, sender: str) -> Dict[str, Any]:
        """
        Process incoming WhatsApp message.

        Args:
            message: Message content
            sender: Sender's phone number

        Returns:
            Processing result with actions
        """
        try:
            # Analyze message intent
            intent_analysis = await self._analyze_intent(message)

            # Determine action based on intent
            action = await self._determine_action(intent_analysis)

            # Execute action
            result = await self._execute_action(action, message, sender)

            return {
                "status": "success",
                "intent": intent_analysis,
                "action": action,
                "result": result,
            }
        except Exception as e:
            logger.error(f"WhatsApp message processing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze message intent using Gemini."""
        try:
            if not gemini_service:
                return {"intent": "other", "keywords": [], "priority": "medium"}
            
            analysis = await gemini_service.analyze_text(
                message,
                prompt="""Analyze this message intent. Respond with JSON:
{"intent": "task/reminder/question/other", "keywords": [], "priority": "low/medium/high"}""",
            )
            import json
            return json.loads(analysis)
        except Exception as e:
            logger.warning(f"Intent analysis failed: {e}")
            return {"intent": "other", "keywords": [], "priority": "medium"}

    async def _determine_action(self, intent_analysis: Dict[str, Any]) -> str:
        """Determine action based on intent."""
        intent = intent_analysis.get("intent", "other")
        if intent == "task":
            return "create_task"
        elif intent == "reminder":
            return "set_reminder"
        elif intent == "question":
            return "answer_question"
        return "acknowledge"

    async def _execute_action(self, action: str, message: str, sender: str) -> Dict[str, Any]:
        """Execute the determined action."""
        if action == "create_task":
            return {"type": "task", "message": "Task created from WhatsApp message"}
        elif action == "set_reminder":
            return {"type": "reminder", "message": "Reminder set"}
        elif action == "answer_question":
            response = await gemini_service.analyze_text(message)
            return {"type": "answer", "response": response}
        else:
            return {"type": "acknowledge", "message": "Message received"}


class GmailAgent:
    """Agent for handling Gmail operations."""

    def __init__(self, user_id: str):
        """
        Initialize Gmail agent.

        Args:
            user_id: Firebase user ID
        """
        self.user_id = user_id
        logger.info(f"Gmail agent initialized for user {user_id}")

    async def process_email(self, email_id: str, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """
        Process incoming email.

        Args:
            email_id: Email ID
            subject: Email subject
            body: Email body
            sender: Sender's email

        Returns:
            Processing result
        """
        try:
            # Analyze email content
            analysis = await self._analyze_email(subject, body)

            # Determine action
            action = await self._determine_action(analysis)

            # Execute action
            result = await self._execute_action(action, subject, body, sender)

            return {
                "status": "success",
                "analysis": analysis,
                "action": action,
                "result": result,
            }
        except Exception as e:
            logger.error(f"Email processing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _analyze_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Analyze email using Gemini."""
        try:
            analysis = await gemini_service.analyze_text(
                f"Subject: {subject}\n\n{body}",
                prompt="""Analyze this email. Respond with JSON:
{"category": "work/personal/spam/important", "sentiment": "positive/negative/neutral", "requires_action": true/false}""",
            )
            import json
            return json.loads(analysis)
        except Exception as e:
            logger.warning(f"Email analysis failed: {e}")
            return {"category": "personal", "sentiment": "neutral", "requires_action": False}

    async def _determine_action(self, analysis: Dict[str, Any]) -> str:
        """Determine action based on email analysis."""
        if analysis.get("requires_action"):
            category = analysis.get("category", "personal")
            if category == "work":
                return "create_task"
            elif category == "important":
                return "flag_important"
        return "archive"

    async def _execute_action(self, action: str, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """Execute the determined action."""
        if action == "create_task":
            return {"type": "task", "message": f"Task created from email: {subject}"}
        elif action == "flag_important":
            return {"type": "flag", "message": "Email flagged as important"}
        else:
            return {"type": "archive", "message": "Email archived"}


class TaskAgent:
    """Agent for task management and creation."""

    def __init__(self, user_id: str):
        """
        Initialize task agent.

        Args:
            user_id: Firebase user ID
        """
        self.user_id = user_id
        logger.info(f"Task agent initialized for user {user_id}")

    async def create_from_text(self, text: str, source: str = "manual") -> Dict[str, Any]:
        """
        Create task from natural language text.

        Args:
            text: Text description
            source: Source of task (manual, whatsapp, email, etc.)

        Returns:
            Created task data
        """
        try:
            # Extract task details using Gemini
            details = await self._extract_task_details(text)

            return {
                "status": "success",
                "task": details,
                "source": source,
            }
        except Exception as e:
            logger.error(f"Task creation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _extract_task_details(self, text: str) -> Dict[str, Any]:
        """Extract task details from text."""
        try:
            analysis = await gemini_service.analyze_text(
                text,
                prompt="""Extract task details from this text. Respond with JSON:
{"title": "task title", "description": "detailed description", "priority": "low/medium/high", "due_date": "YYYY-MM-DD or null", "type": "task type"}""",
            )
            import json
            return json.loads(analysis)
        except Exception as e:
            logger.warning(f"Task extraction failed: {e}")
            return {
                "title": "Untitled Task",
                "description": text,
                "priority": "medium",
                "due_date": None,
                "type": "general",
            }
