"""
LangChain-based agents for automated task execution.
"""

import logging
import re
from typing import Optional, Any, Dict
from app.core.config import settings
from app.services import gemini_service, web_search_service
from app.services.tracing_service import traceable

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

    # System prompt for the AI assistant
    SYSTEM_PROMPT = """You are AgentCoolie, an intelligent personal AI assistant designed to help users manage tasks, communicate effectively, search the web, remember useful context, and automate workflows.

## Your Core Purpose
- Help users create, organize, and track tasks
- Provide intelligent responses to user queries
- Extract actionable tasks from natural language
- Analyze sentiment and intent from messages
- Assist with productivity and organization

## Your Capabilities
1. **Task Management**: Create tasks with due dates, priorities, and descriptions
2. **Natural Language Understanding**: Extract intent and entities from user messages
3. **Sentiment Analysis**: Understand emotional tone and context
4. **Information Retrieval**: Answer questions and provide helpful information
5. **Workflow Automation**: Suggest actions based on user input

## How to Respond
- Be concise and actionable
- Focus on helping the user accomplish their goals
- When a user mentions a task, offer to create it
- Ask clarifying questions if needed
- Provide specific, helpful suggestions
- Use a friendly but professional tone

## Important Guidelines
- Always prioritize user productivity
- Be honest about limitations
- Don't make up information
- Suggest relevant features when appropriate
- Help users stay organized and on track

## Response Format
- Keep responses brief and focused
- Use bullet points for lists
- Highlight action items
- Provide clear next steps when applicable

Remember: You're here to make the user's life easier and more productive."""

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
                    model=settings.OPENAI_MODEL,
                    temperature=0.7,
                )
            except Exception as e:
                logger.warning(f"ChatOpenAI initialization failed: {e}")

        logger.info(f"Chat agent initialized for user {user_id}")

    def _format_short_memory(self, context: Optional[list[dict[str, str]]]) -> str:
        if not context:
            return "No recent conversation context."

        lines = []
        for item in context[-10:]:
            role = str(item.get("role") or "user").strip().title()
            content = str(item.get("content") or "").strip()
            if content:
                lines.append(f"{role}: {content}")

        return "\n".join(lines) if lines else "No recent conversation context."

    def _format_long_term_memory(self, memories: Optional[list[dict[str, Any]]]) -> str:
        if not memories:
            return "No long-term memory available."

        lines = []
        for item in memories:
            content = str(item.get("content") or "").strip()
            if content:
                lines.append(f"- {content}")

        return "\n".join(lines) if lines else "No long-term memory available."

    def _format_web_results(self, web_results: Optional[list[dict[str, Any]]], web_search_attempted: bool) -> str:
        return web_search_service.format_for_prompt(web_results or [], attempted=web_search_attempted)

    def _is_memory_question(self, user_message: str) -> bool:
        text = user_message.lower().strip()
        return bool(
            re.search(r"\bwhat\b.*\b(know|remember)\b.*\b(me|about me)\b", text)
            or re.search(r"\b(do you|u)\s+(know|remember)\s+(about\s+)?me\b", text)
            or re.search(r"\bwhat.*my.*(profile|details|context)\b", text)
        )

    def _direct_memory_answer(
        self,
        context: Optional[list[dict[str, str]]],
        long_term_memories: Optional[list[dict[str, Any]]],
    ) -> str | None:
        memories = []
        for item in long_term_memories or []:
            content = str(item.get("content") or "").strip()
            if content and content not in memories:
                memories.append(content)

        recent_user_messages = []
        for item in context or []:
            if str(item.get("role") or "").lower() == "user":
                content = str(item.get("content") or "").strip()
                if content:
                    recent_user_messages.append(content)

        if memories:
            lines = ["Here's what I currently know from saved memory:"]
            lines.extend(f"- {memory}" for memory in memories[:8])
            if recent_user_messages:
                lines.append(f"\nFrom this chat, your last question was: \"{recent_user_messages[-1]}\"")
            return "\n".join(lines)

        if recent_user_messages:
            return (
                "I do not have saved long-term facts for this account yet. "
                f"From this current chat, your last question was: \"{recent_user_messages[-1]}\""
            )

        return "I do not have saved long-term facts for this account yet. Share stable details or preferences, and I can remember the important ones."

    def _format_preferences(self, preferences: Optional[dict[str, Any]]) -> str:
        if not preferences:
            return "No explicit personalization settings saved."

        tone = str(preferences.get("tone") or "friendly").strip()
        response_length = str(preferences.get("response_length") or "moderate").strip()
        formality = str(preferences.get("formality") or "medium").strip()
        include_emojis = bool(preferences.get("include_emojis", False))

        emoji_instruction = "Use emojis naturally when they add warmth." if include_emojis else "Avoid emojis unless the user explicitly asks for them."
        return (
            f"- Tone: {tone}\n"
            f"- Response length: {response_length}\n"
            f"- Formality: {formality}\n"
            f"- Emoji preference: {emoji_instruction}\n"
            "Follow these personalization settings unless they conflict with safety, accuracy, or the user's latest instruction."
        )

    @traceable(name="agent.chat", run_type="chain")
    async def chat(
        self,
        user_message: str,
        context: Optional[list[dict[str, str]]] = None,
        long_term_memories: Optional[list[dict[str, Any]]] = None,
        preferences: Optional[dict[str, Any]] = None,
        web_results: Optional[list[dict[str, Any]]] = None,
        web_search_attempted: bool = False,
    ) -> str:
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

            if self._is_memory_question(user_message):
                direct = self._direct_memory_answer(context, long_term_memories)
                if direct:
                    return direct
            
            short_memory = self._format_short_memory(context)
            durable_memory = self._format_long_term_memory(long_term_memories)
            personalization = self._format_preferences(preferences)
            search_context = self._format_web_results(web_results, web_search_attempted)

            # Create prompt with system context and Redis short memory.
            full_prompt = f"""{self.SYSTEM_PROMPT}

Personalization settings:
{personalization}

Long-term user memory:
{durable_memory}

Recent conversation context from short memory (last 5 exchanges):
{short_memory}

Web search results when relevant:
{search_context}

Current User Message: {user_message}

Respond as AgentCoolie, keeping the guidelines above in mind. You have web search only when results are provided above. When using web search results, mention the source URLs briefly. If web search was attempted but no results are available, say the live search failed and ask the user to retry; do not say you have no web search capability."""
            
            response = await gemini_service.analyze_text(user_message, prompt=full_prompt)
            
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

    SYSTEM_PROMPT = """You are AgentCoolie's WhatsApp handler. Your role is to:
1. Understand user intent from WhatsApp messages
2. Extract actionable tasks from natural language
3. Respond appropriately to user requests
4. Create reminders and tasks when requested

Be concise in WhatsApp responses (keep under 160 characters when possible).
Focus on understanding what the user wants to accomplish."""

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

    SYSTEM_PROMPT = """You are AgentCoolie's Gmail handler. Your role is to:
1. Analyze email content and extract key information
2. Determine email priority and category
3. Suggest task creation from important emails
4. Summarize email content when needed

Focus on understanding the email's purpose and extracting actionable items."""

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

    SYSTEM_PROMPT = """You are AgentCoolie's Task Manager. Your role is to:
1. Extract task details from natural language
2. Identify due dates, priorities, and descriptions
3. Suggest task creation when appropriate
4. Help organize and structure tasks

When extracting tasks, identify:
- Task title (what needs to be done)
- Due date (when it needs to be done)
- Priority (low/medium/high/urgent)
- Description (additional details)"""

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
