# Agent Tools Reference Guide

## Overview
All agents in the CoolieAssistant use an integrated toolset based on Gemini AI, Supabase, Firebase, and LangChain memory systems.

---

## Core Shared Tools

### 1. **Gemini Service** (Primary AI Tool)
**Used by:** All 4 agents  
**Purpose:** Text analysis, intent detection, sentiment analysis, content understanding  
**Methods:**
```python
async def analyze_text(text: str, task: str = "analyze") -> str:
    """Analyze text using Google Generative AI (Gemini)"""
    
async def embed_text(text: str) -> List[float]:
    """Generate embeddings for semantic search"""
```

**Examples:**
- ChatAgent: "Is this customer happy or angry?" → sentiment detection
- WhatsappAgent: "What does the user want?" → intent detection  
- EmailAgent: "Is this spam or important?" → categorization
- TaskAgent: "Extract due date from text" → NLP extraction

---

### 2. **Supabase Service** (Data Persistence Tool)
**Used by:** All 4 agents  
**Purpose:** Store and retrieve conversations, tasks, emails, user preferences  
**Main Operations:**

```python
# Message storage
async def create_message(user_id, content, role, metadata)
async def get_messages(user_id, limit=50)

# Task management
async def create_task(user_id, title, description, priority, due_date)
async def get_tasks(user_id)
async def update_task(task_id, updates)
async def delete_task(task_id)

# User preferences
async def save_preferences(user_id, preferences)
async def get_preferences(user_id)

# Credentials storage
async def save_credentials(user_id, service, credentials)
```

**Data Models:**
- `messages` table: Stores all conversations
- `tasks` table: All user tasks
- `user_preferences` table: User settings
- `user_credentials` table: Connected service credentials

---

### 3. **Firebase Service** (Authentication Tool)
**Used by:** All protected routes  
**Purpose:** Verify user identity and extract user info  
**Methods:**

```python
def verify_id_token(token: str) -> dict:
    """Verify Firebase ID token"""
    return {"uid": "user123", "email": "user@example.com"}

def get_user(uid: str) -> dict:
    """Get user info from Firebase"""

def create_user(email: str, password: str) -> str:
    """Create new user, returns UID"""

def update_user(uid: str, updates: dict):
    """Update user profile"""
```

**Usage:** Extract user identity from Authorization header token

---

### 4. **Conversation Memory** (Context Tool)
**Used by:** ChatAgent (optional, gracefully degrades)  
**Purpose:** Maintain conversation context across messages  
**Type:** ConversationBufferMemory (if LangChain available)

---

## Agent-Specific Tools

### ChatAgent
**Endpoint:** `/api/chat/`  
**Primary Tools:**

#### Tool 1: Sentiment Analysis
```python
async def analyze_sentiment(content: str) -> dict:
    """Analyze text sentiment using Gemini"""
    return {
        "sentiment": "positive|negative|neutral",
        "confidence": 0.95,
        "emotions": ["happy", "excited"]
    }
```

**What it does:**
- Detects emotional tone of user messages
- Returns sentiment score and emotion labels
- Used to personalize responses

**Example Use:**
```
User: "I'm so frustrated with this!"
→ sentiment: "negative", emotions: ["frustrated", "angry"]
→ ChatAgent: "I understand you're upset. Let me help..."
```

#### Tool 2: Message Analysis
```python
async def chat(message: str, user_id: str) -> str:
    """Send message to chat agent"""
```

**What it does:**
- Processes user messages
- Uses Gemini to understand intent
- Maintains conversation history
- Returns natural language response

#### Tool 3: History Retrieval
```python
async def get_chat_history(user_id: str, limit: int = 50) -> List[dict]:
    """Retrieve conversation history"""
    return [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "timestamp": "..."}
    ]
```

---

### TaskAgent
**Endpoint:** `/api/tasks/`  
**Primary Tools:**

#### Tool 1: NLP Task Extraction
```python
async def create_from_text(text: str, user_id: str) -> dict:
    """Extract structured task from natural language using Gemini"""
    return {
        "title": "Buy milk",
        "description": "From local store",
        "type": "shopping",
        "priority": "medium",
        "due_date": "2025-10-15",
        "estimated_duration": 30  # minutes
    }
```

**What it does:**
- Converts natural language to structured tasks
- Extracts deadline from text ("tomorrow", "next week", "in 3 days")
- Determines priority ("ASAP" = high, "whenever" = low)
- Identifies task type (shopping, work, personal, etc.)

**Example:**
```
User: "Buy groceries and milk tomorrow morning, high priority"
↓ Gemini NLP Extraction
→ title: "Buy groceries and milk"
→ due_date: "2025-10-15" (calculated as tomorrow)
→ priority: "high"
→ estimated_duration: 45
```

#### Tool 2: Task CRUD Operations
```python
async def create_task(title, description, priority, due_date)
async def get_tasks(user_id, filter_by=None)
async def update_task(task_id, updates)
async def delete_task(task_id)
async def complete_task(task_id)
```

**What it does:**
- Create, read, update, delete tasks
- Filter tasks by status, priority, due date
- Mark tasks as complete

#### Tool 3: Intent Detection
```python
async def _detect_intent(text: str) -> str:
    """Determine if text is a task, reminder, or question"""
    return "task_creation" | "reminder_set" | "task_query"
```

---

### WhatsappAgent
**Endpoint:** `/api/whatsapp/webhook`  
**Primary Tools:**

#### Tool 1: Intent Analyzer
```python
async def _analyze_intent(text: str) -> dict:
    """Analyze WhatsApp message intent using Gemini"""
    return {
        "intent": "task_creation",  # task_creation | reminder_set | question | inquiry | other
        "confidence": 0.92,
        "entities": {
            "action": "create",
            "object": "task",
            "time": "tomorrow at noon",
            "description": "reminders for meeting"
        }
    }
```

**Intent Types:**
- `task_creation`: "Create a task for me"
- `reminder_set`: "Remind me tomorrow"
- `question`: "What should I do?"
- `inquiry`: "How do I...?"
- `other`: General message

#### Tool 2: Action Router
```python
async def _determine_action(intent: str, entities: dict) -> str:
    """Map intent to executable action"""
    return "create_task" | "set_reminder" | "answer_question" | "escalate_to_human"
```

**What it does:**
- Routes messages to appropriate handlers
- Decides if message needs task creation, reminder, etc.
- Can escalate complex queries to human

#### Tool 3: Message Processor
```python
async def process_message(message_data: dict) -> dict:
    """Main WhatsApp message handler"""
    return {
        "status": "success",
        "processed": 1,
        "action_taken": "task_created",
        "result": {...}
    }
```

**What it does:**
- Receives WhatsApp webhook messages
- Analyzes intent
- Creates tasks/reminders/notifications as needed
- Sends response back to WhatsApp

#### Tool 4: Storage Integration
```python
# Automatically saves:
- User ID and phone number
- Message content
- Detected intent
- Created tasks/reminders
- Conversation thread
```

---

### EmailAgent
**Endpoint:** `/api/gmail/webhook`  
**Primary Tools:**

#### Tool 1: Content Analyzer
```python
async def _analyze_email(subject: str, body: str, sender: str) -> dict:
    """Analyze email content using Gemini"""
    return {
        "category": "work" | "personal" | "promotional" | "spam" | "urgent",
        "sentiment": "positive" | "negative" | "neutral",
        "priority": "high" | "medium" | "low",
        "requires_action": True|False,
        "suggested_action": "flag_important" | "create_task" | "archive" | "reply"
    }
```

**What it does:**
- Reads email subject, body, and sender
- Uses Gemini to understand content
- Determines email category
- Identifies if human action needed

#### Tool 2: Category Detector
```python
Category Types:
- "work": Job-related emails (meetings, projects, reviews)
- "personal": Family, friends, personal matters
- "promotional": Marketing, sales, newsletters
- "spam": Unwanted, scams
- "urgent": Requires immediate attention
```

#### Tool 3: Priority Classifier
```python
Factors for Priority:
- Sender: Known important contacts → higher priority
- Keywords: "URGENT", "ASAP", "deadline" → higher priority
- Category: Work > Personal > Promo > Spam
- Past behavior: User's interaction patterns
```

#### Tool 4: Action Router
```python
Actions Available:
- "create_task": Create task for follow-up
- "flag_important": Mark as important
- "archive": Move to archive
- "reply": Suggest auto-reply
- "escalate": Notify user immediately
```

#### Tool 5: Storage Integration
```python
# Automatically saves:
- Email metadata (subject, sender, date)
- Categorization results
- Priority assignment
- Suggested actions
- User response to suggestions
```

---

## Tool Integration Patterns

### Pattern 1: Intent Detection → Action Routing
```python
# Used by: WhatsappAgent, EmailAgent, TaskAgent
1. Analyze text with Gemini
2. Extract intent and entities
3. Determine action based on intent
4. Execute action (create task, send notification, etc.)
5. Store result in Supabase
```

### Pattern 2: NLP Extraction → Data Persistence
```python
# Used by: TaskAgent
1. Extract structured data from natural language (Gemini)
2. Validate extracted data
3. Store in Supabase
4. Return confirmation to user
```

### Pattern 3: Content Analysis → Auto-Organization
```python
# Used by: EmailAgent
1. Analyze content with Gemini
2. Categorize and prioritize
3. Suggest or execute actions
4. Store outcomes for learning
```

### Pattern 4: Conversation Context → Smart Responses
```python
# Used by: ChatAgent
1. Retrieve conversation history from memory
2. Analyze sentiment and intent of current message
3. Generate context-aware response using Gemini
4. Update memory with new exchange
5. Store in Supabase for long-term context
```

---

## How Tools Work Together

### Example: WhatsApp Message Processing
```
User WhatsApp: "Remind me to call mom tomorrow at 8pm"
                    ↓
         [WhatsappAgent.process_message()]
                    ↓
    [Intent Analyzer - Gemini]
    → intent: "reminder_set"
    → entities: {action: "remind", target: "mom", time: "tomorrow 8pm"}
                    ↓
    [Action Router]
    → action: "set_reminder"
                    ↓
    [Task Creation via TaskAgent NLP Tool]
    → Creates task: {title: "Call mom", due_date: "tomorrow", time: "08:00"}
                    ↓
    [Supabase Storage]
    → Saves: reminder record, task, user conversation
                    ↓
    Response: "✓ I'll remind you to call mom tomorrow at 8pm"
```

---

## Extending Tools - Examples

### Example 1: Add Calendar Integration
```python
# File: backend/app/tools/calendar_tool.py
class CalendarTool:
    async def get_available_slots(self, date: str) -> List[dict]:
        """Get available calendar slots"""
        
    async def check_conflicts(self, time: str) -> bool:
        """Check if time conflicts with existing events"""
        
# Usage in TaskAgent:
self.calendar_tool = CalendarTool()
conflicts = await self.calendar_tool.check_conflicts(extracted_time)
```

### Example 2: Add Weather Tool
```python
# File: backend/app/tools/weather_tool.py
class WeatherTool:
    async def get_weather(self, location: str) -> dict:
        """Get weather forecast"""
        
# Usage in ChatAgent or WhatsappAgent:
weather = await self.weather_tool.get_weather("New York")
response = f"It will be {weather['condition']} tomorrow"
```

### Example 3: Add Notification Tool
```python
# File: backend/app/tools/notification_tool.py
class NotificationTool:
    async def send_push(self, user_id: str, message: str)
    async def send_sms(self, phone: str, message: str)
    async def send_email(self, email: str, subject: str, body: str)
    
# Usage in any agent:
await self.notification_tool.send_sms(user_phone, reminder_text)
```

---

## Tool Availability & Status

| Tool | ChatAgent | TaskAgent | WhatsappAgent | EmailAgent | Status |
|------|:---------:|:---------:|:-------------:|:----------:|--------|
| **Gemini Service** | ✓ | ✓ | ✓ | ✓ | ✅ Active |
| **Supabase DB** | ✓ | ✓ | ✓ | ✓ | ✅ Active |
| **Firebase Auth** | ✓ | ✓ | ✓ | ✓ | ⚠️ Needs config |
| **Memory (LangChain)** | ✓ | ✗ | ✗ | ✗ | ⚠️ Optional |
| **Sentiment Tool** | ✓ | ✗ | ✗ | ✓ | ✅ Active |
| **NLP Extractor** | ✗ | ✓ | ✓ | ✓ | ✅ Active |
| **Intent Router** | ✗ | ✓ | ✓ | ✗ | ✅ Active |

---

## Configuration & Setup

### Environment Variables Needed
```bash
# API Keys
GOOGLE_AI_API_KEY=your_key_here
OPENAI_API_KEY=optional
COHERE_API_KEY=optional

# Database
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key
SUPABASE_SERVICE_ROLE_KEY=your_key

# Authentication
FIREBASE_PROJECT_ID=your_project
FIREBASE_PRIVATE_KEY=your_key
FIREBASE_CLIENT_EMAIL=your_email

# Services
WHATSAPP_API_TOKEN=your_token
GMAIL_SERVICE_ACCOUNT=your_account
```

### How to Test Tools Locally
```bash
# 1. Start server
python -m uvicorn backend.app.main:app --reload

# 2. Run tool demonstrations
python demo_agent_tools.py

# 3. Run comprehensive tests
python test_agents.py

# 4. Try manual API calls
curl -X POST http://localhost:8000/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"text": {"body": "test message"}}]}'
```

---

## Troubleshooting Tools

### Tool Not Working?

**1. Gemini Analysis Failing**
- Check: `GOOGLE_AI_API_KEY` in `.env`
- Verify: Key is valid and has API enabled
- Fallback: Chat still works without Gemini

**2. Supabase Not Storing Data**
- Check: Database connection in `.env`
- Verify: Tables exist (messages, tasks, preferences)
- Debug: Check Supabase logs for errors

**3. Firebase Auth Not Verifying Tokens**
- Check: Firebase credentials in `.env`
- Verify: Token format is "Bearer {token}"
- Fallback: App works with missing Firebase (logs warning)

**4. WhatsApp/Gmail Webhooks Not Triggering**
- Check: Webhook URL correctly configured in provider
- Verify: Port 8000 accessible from internet
- Debug: Check server logs for incoming requests

---

## Next: Adding Your Own Tools

See [CUSTOM_TOOLS.md](./CUSTOM_TOOLS.md) for step-by-step guide to:
- Create custom tools
- Integrate with agents
- Test and deploy
