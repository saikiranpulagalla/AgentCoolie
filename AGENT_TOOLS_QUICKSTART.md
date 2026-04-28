# Agent Tools Quick Start Guide

## TL;DR - What You Need to Know

Your 4 AI agents have integrated tools that work automatically:

```
WhatsApp Message → WhatsappAgent → Intent Analysis → Auto-create Task
Email arrives → EmailAgent → Category + Priority → Auto-organize
User types → ChatAgent → Sentiment Analysis → Smart response
User says "remind me..." → TaskAgent → NLP Extraction → Create Reminder
```

All powered by **Gemini AI** + **Supabase** database.

---

## 30-Second Feature Overview

### 1. ChatAgent - Smart Conversation
- **Input:** User chat message
- **Tools Used:** Gemini text analysis, sentiment detection
- **Output:** Intelligent response + emotion awareness
- **Endpoint:** `POST /api/chat/message`

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"content": "I love your app!"}'
```

### 2. TaskAgent - Auto Create Tasks from Text
- **Input:** "Buy milk tomorrow at 3pm, high priority"
- **Tools Used:** Gemini NLP extraction, task CRUD
- **Output:** Structured task with deadline, priority
- **Endpoint:** `POST /api/tasks/from-text`

```bash
curl -X POST http://localhost:8000/api/tasks/from-text \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"text": "Buy milk tomorrow"}'
```

### 3. WhatsappAgent - Smart Message Routing
- **Input:** WhatsApp message from user phone
- **Tools Used:** Intent analysis, action routing
- **Output:** Creates reminder, task, or answers question
- **Endpoint:** `POST /api/whatsapp/webhook`

```bash
curl -X POST http://localhost:8000/api/whatsapp/webhook \
  -d '{
    "messages": [{
      "from": "+1234567890",
      "text": {"body": "remind me to call mom tomorrow"}
    }]
  }'
```

### 4. EmailAgent - Auto Organize Inbox
- **Input:** Incoming email
- **Tools Used:** Content analysis, categorization, priority classification
- **Output:** Categorized, prioritized, suggested action
- **Endpoint:** `POST /api/gmail/webhook`

```bash
curl -X POST http://localhost:8000/api/gmail/webhook \
  -d '{"message": {"data": "email_message_id"}}'
```

---

## Understanding Tool Flow

### Example: WhatsApp "Create Task" Flow

```
┌─────────────────────────────────┐
│ User WhatsApp:                  │
│ "Buy groceries tomorrow morning"│
└─────────────┬───────────────────┘
              │
              ↓
┌─────────────────────────────────┐
│  WhatsappAgent.process_message()│
└─────────────┬───────────────────┘
              │
              ├─→ [Intent Analyzer Tool - Gemini]
              │   Analyzes text → detects "task_creation"
              │
              ├─→ [Action Router Tool]
              │   Routes to → "create_task"
              │
              ├─→ [TaskAgent NLP Tool]
              │   Extracts: title, deadline, priority
              │
              ├─→ [Supabase Storage Tool]
              │   Saves task to database
              │
              └─→ [Response to WhatsApp]
                  "✓ Created: Buy groceries - Tomorrow 8am"
```

---

## Tools Availability Matrix

| What the Agent Does | Tool Required | Status | Depends On |
|---|---|---|---|
| Chat naturally | Gemini AI | ✅ Ready | Google API key |
| Extract deadline from text | Gemini NLP | ✅ Ready | Google API key |
| Analyze sentiment | Gemini | ✅ Ready | Google API key |
| Detect WhatsApp intent | Gemini | ✅ Ready | Google API key |
| Auto-categorize email | Gemini | ✅ Ready | Google API key |
| Save conversations | Supabase DB | ✅ Ready | DB connection |
| Persist tasks | Supabase DB | ✅ Ready | DB connection |
| Store emails | Supabase DB | ✅ Ready | DB connection |
| Authenticate users | Firebase | ⚠️ Needs config | Firebase creds |

---

## How Tools Are Connected

### Service Architecture
```
┌────────────────────────────┐
│    4 Agents                │
│  (Chat, Task, WhatsApp, Email)
└────────┬───────────────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │          │          │          │
    ↓          ↓          ↓          ↓
┌────────┐ ┌─────────┐ ┌────────┐ ┌────────┐
│ Gemini │ │Supabase │ │Firebase│ │ Memory │
│  Tool  │ │  Tool   │ │  Tool  │ │ Tool   │
└────────┘ └─────────┘ └────────┘ └────────┘
   (AI)      (Storage)  (Auth)   (Context)
```

### Data Flow
```
User Input → Agent Analysis (Gemini) → Action Execution → Data Storage (Supabase) → Response
                                                                                          ↓
                                                                        Next message uses stored context
```

---

## Real Examples from Code

### ChatAgent Sentiment Tool
```python
# Tool: Analyze emotion in user message
response = await gemini_service.analyze_text(
    text="I'm so frustrated!",
    task="sentiment_analysis"
)
# Returns: {"sentiment": "negative", "emotions": ["frustrated"]}
```

### WhatsappAgent Intent Tool
```python
# Tool: Detect what user wants
intent = await gemini_service.analyze_text(
    text="Remind me to call mom tomorrow",
    task="intent_detection"
)
# Detects: "reminder_set" intent → creates reminder task
```

### TaskAgent NLP Tool
```python
# Tool: Extract structured data from natural language
extraction = await gemini_service.analyze_text(
    text="Buy milk and eggs tomorrow afternoon",
    task="nlp_extraction"
)
# Returns:
# {
#   "title": "Buy milk and eggs",
#   "due_date": "2025-10-15",
#   "time": "14:00"
# }
```

### EmailAgent Category Tool
```python
# Tool: Auto-categorize emails
analysis = await gemini_service.analyze_text(
    text="Meeting tomorrow at 2pm - Project Alpha",
    task="email_categorization"
)
# Returns:
# {
#   "category": "work",
#   "priority": "high",
#   "requires_action": True
# }
```

---

## Testing Tools Locally

### Option 1: Run All Tests
```bash
# Comprehensive test suite with all agents
python test_agents.py
```

### Option 2: Run Demo
```bash
# Shows what each tool does with live examples
python demo_agent_tools.py
```

### Option 3: Manual Testing
```bash
# Test WhatsApp intent analysis
curl -X POST http://localhost:8000/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "from": "+1234567890",
      "type": "text",
      "text": {"body": "Create reminder for tomorrow"}
    }]
  }'

# Expected response:
# {"status": "success", "processed": 1}
```

### Option 4: Check Tool Availability
```bash
curl http://localhost:8000/health
# Shows which tools are available/online
```

---

## Extending Tools - 3 Steps

### Step 1: Define the Tool
```python
# File: backend/app/tools/my_tool.py
class MyTool:
    async def do_something(self, data: str) -> dict:
        # Your tool logic here
        return result
```

### Step 2: Add to Agent
```python
# In agent's __init__
self.my_tool = MyTool()
```

### Step 3: Use in Methods
```python
# In agent's methods
result = await self.my_tool.do_something(data)
```

---

## Tool Status & Troubleshooting

### Gemini Tool Not Working?
```
Check 1: GOOGLE_AI_API_KEY in .env ✓
Check 2: API is enabled in Google Cloud ✓
Check 3: Internet connection ✓

Then: Restart server
python -m uvicorn backend.app.main:app --reload
```

### Supabase Storage Not Working?
```
Check 1: SUPABASE_URL in .env ✓
Check 2: SUPABASE_ANON_KEY in .env ✓
Check 3: Database tables exist ✓
Check 4: Row-level security policies allow operations ✓

Then: Check Supabase dashboard for errors
```

### Firebase Auth Not Working?
```
Check 1: FIREBASE_PROJECT_ID in .env ✓
Check 2: FIREBASE_PRIVATE_KEY in .env ✓
Check 3: Bearer token format: "Bearer {token}" ✓

Then: Server logs will show verification errors
```

---

## Quick Reference

### API Endpoints
| Endpoint | Method | Requires Auth | Tools Used |
|---|---|---|---|
| `/api/chat/message` | POST | ✓ | Gemini, Memory |
| `/api/chat/analyze-sentiment` | POST | ✓ | Gemini, Sentiment |
| `/api/tasks/from-text` | POST | ✓ | Gemini NLP |
| `/api/tasks` | GET/POST | ✓ | Supabase CRUD |
| `/api/whatsapp/webhook` | POST | ✗ | Gemini Intent, Router |
| `/api/gmail/webhook` | POST | ✗ | Gemini Analyzer |

### Environment Variables
```bash
# Required
GOOGLE_AI_API_KEY=        # Gemini
SUPABASE_URL=             # Database
SUPABASE_ANON_KEY=        # Database

# Recommended
FIREBASE_PROJECT_ID=      # Auth
FIREBASE_PRIVATE_KEY=     # Auth

# Optional
OPENAI_API_KEY=           # Fallback LLM
COHERE_API_KEY=           # Fallback embeddings
```

---

## Next Steps

1. **Run Demo:** `python demo_agent_tools.py`
2. **Read Reference:** [AGENT_TOOLS_REFERENCE.md](./AGENT_TOOLS_REFERENCE.md)
3. **Try Endpoints:** Use curl examples above
4. **Add Tools:** See "Extending Tools" section
5. **Deploy:** Follow [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## FAQs

**Q: Are all tools working?**  
A: Yes! All core tools (Gemini, Supabase) are fully functional. Firebase needs credentials configured.

**Q: Can I add my own tools?**  
A: Yes! Follow the 3-step guide in "Extending Tools" section.

**Q: What if Gemini is not available?**  
A: The app gracefully degrades. Agents still work but without AI analysis.

**Q: How do I know which tool did what?**  
A: Check logs with: `python -m uvicorn backend.app.main:app --reload --log-level debug`

**Q: Can tools work offline?**  
A: No, agents need internet for Gemini AI. Database can work locally with Supabase local dev.
