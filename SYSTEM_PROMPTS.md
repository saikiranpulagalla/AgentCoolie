# CoolieAssistant - System Prompts Documentation

This document explains the system prompts used by each AI agent in CoolieAssistant.

---

## 📋 Overview

System prompts are instructions given to the AI model to define its behavior, role, and guidelines. They ensure consistent, focused, and relevant responses.

**Location:** `backend/app/agents/base_agents.py`

---

## 🤖 ChatAgent System Prompt

**Role:** Main conversational AI assistant

**Purpose:** Handle general chat interactions and provide intelligent responses

**Key Guidelines:**
- Help users manage tasks and stay organized
- Extract actionable tasks from conversations
- Analyze sentiment and understand context
- Provide concise, actionable responses
- Suggest relevant features when appropriate

**Example Behavior:**
```
User: "I need to call my mom tomorrow at 3 PM"
ChatAgent: "I can help with that! I'll create a task 'Call mom' for tomorrow at 3 PM. 
Would you like me to set a reminder?"
```

---

## 📱 WhatsappAgent System Prompt

**Role:** Handle WhatsApp message processing

**Purpose:** Understand intent and create tasks from WhatsApp messages

**Key Guidelines:**
- Keep responses concise (under 160 characters when possible)
- Extract actionable tasks from messages
- Understand user intent (task, reminder, question, etc.)
- Respond appropriately to different message types

**Example Behavior:**
```
User (WhatsApp): "Remind me to buy groceries"
WhatsappAgent: "✓ Reminder set: Buy groceries"
```

---

## 📧 GmailAgent System Prompt

**Role:** Process and analyze email content

**Purpose:** Extract key information and suggest actions from emails

**Key Guidelines:**
- Analyze email content and extract key information
- Determine email priority and category
- Suggest task creation from important emails
- Summarize email content when needed

**Example Behavior:**
```
Email Subject: "Project deadline: Friday"
GmailAgent: "Priority: High | Category: Work | 
Suggested Task: Complete project by Friday"
```

---

## ✅ TaskAgent System Prompt

**Role:** Extract and create tasks from natural language

**Purpose:** Convert user input into structured task data

**Key Guidelines:**
- Extract task title (what needs to be done)
- Identify due date (when it needs to be done)
- Determine priority (low/medium/high/urgent)
- Parse description (additional details)

**Example Behavior:**
```
User Input: "Meeting with John next Monday at 2 PM - discuss budget"
TaskAgent Output:
{
  "title": "Meeting with John",
  "due_date": "next Monday 2 PM",
  "priority": "medium",
  "description": "discuss budget"
}
```

---

## 🔧 How System Prompts Work

### 1. **Initialization**
Each agent has a `SYSTEM_PROMPT` class variable defined at the top of the class.

```python
class ChatAgent:
    SYSTEM_PROMPT = """You are CoolieAssistant..."""
```

### 2. **Usage**
When processing user input, the system prompt is combined with the user message:

```python
full_prompt = f"""{self.SYSTEM_PROMPT}

User Message: {user_message}

Respond as CoolieAssistant..."""

response = await gemini_service.analyze_text(user_message, prompt=full_prompt)
```

### 3. **AI Model Behavior**
The AI model receives both the system prompt and user message, ensuring consistent behavior.

---

## 📝 Customizing System Prompts

### To Modify a System Prompt:

1. **Open the file:**
   ```bash
   backend/app/agents/base_agents.py
   ```

2. **Find the agent class:**
   ```python
   class ChatAgent:
       SYSTEM_PROMPT = """..."""
   ```

3. **Edit the prompt:**
   - Keep it clear and concise
   - Define the agent's role
   - List key guidelines
   - Provide examples if helpful

4. **Test the changes:**
   - Restart the backend
   - Test the agent's responses
   - Verify behavior matches expectations

### Example Modification:

```python
# Before
SYSTEM_PROMPT = """You are CoolieAssistant..."""

# After
SYSTEM_PROMPT = """You are CoolieAssistant, an intelligent personal AI assistant.

## Your Role
- Help users manage tasks
- Provide intelligent responses
- Extract actionable items

## Guidelines
- Be concise and actionable
- Focus on user productivity
- Ask clarifying questions when needed"""
```

---

## 🎯 Best Practices

### 1. **Be Specific**
- Clearly define the agent's role
- List specific responsibilities
- Provide concrete guidelines

### 2. **Keep It Concise**
- Avoid unnecessary verbosity
- Focus on key points
- Use bullet points for clarity

### 3. **Provide Examples**
- Show expected behavior
- Include sample interactions
- Demonstrate desired output format

### 4. **Test Thoroughly**
- Test with various inputs
- Verify consistency
- Check for edge cases

### 5. **Document Changes**
- Update this file when modifying prompts
- Explain why changes were made
- Track version history

---

## 🔍 Monitoring Agent Behavior

### Check Backend Logs:
```bash
# Look for agent initialization messages
2026-04-28 12:33:44,519 - app.agents.base_agents - INFO - Chat agent initialized for user x3smgDN6nhZsn0ePGlFp6K11Ja92
```

### Test Responses:
1. Open http://localhost:8000/docs
2. Try the `/api/chat/message` endpoint
3. Check the response quality
4. Verify it matches the system prompt guidelines

### Monitor Errors:
```bash
# Check for errors in backend terminal
ERROR - Chat agent failed: ...
```

---

## 📊 System Prompt Effectiveness

### Good Indicators:
- ✅ Responses are focused and relevant
- ✅ Agent stays within its defined role
- ✅ Responses are concise and actionable
- ✅ Behavior is consistent across interactions

### Warning Signs:
- ❌ Responses are off-topic
- ❌ Agent ignores its role
- ❌ Responses are too verbose
- ❌ Behavior is inconsistent

---

## 🚀 Advanced Customization

### Adding Context Variables:
```python
SYSTEM_PROMPT = f"""You are CoolieAssistant...
User ID: {user_id}
Timezone: {user_timezone}
Language: {user_language}"""
```

### Dynamic Prompts:
```python
def get_system_prompt(self, context):
    if context.get("is_urgent"):
        return self.URGENT_PROMPT
    else:
        return self.STANDARD_PROMPT
```

### Multi-Language Support:
```python
SYSTEM_PROMPTS = {
    "en": "You are CoolieAssistant...",
    "es": "Eres CoolieAssistant...",
    "fr": "Vous êtes CoolieAssistant..."
}
```

---

## 📚 Related Documentation

- **DEVELOPMENT_GUIDE.md** - Development workflow
- **KNOWN_ISSUES.md** - Known issues and TODOs
- **PROJECT_ANALYSIS.md** - Project assessment
- **backend/app/agents/base_agents.py** - Agent implementation

---

## 🆘 Troubleshooting

### Issue: Agent responses are generic
**Solution:** Check if system prompt is being used in the `chat()` method

### Issue: Agent ignores guidelines
**Solution:** Verify the system prompt is clear and specific

### Issue: Responses are too long
**Solution:** Add "Keep responses concise" to the system prompt

### Issue: Agent behavior is inconsistent
**Solution:** Ensure system prompt is loaded correctly on initialization

---

## 📞 Support

For questions about system prompts:
1. Check this documentation
2. Review the agent implementation
3. Check backend logs for errors
4. Test with different inputs

---

**Last Updated:** April 28, 2026  
**Version:** 2.0.0
