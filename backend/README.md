# CoolieAssistant Backend (FastAPI)

High-performance Python backend for CoolieAssistant using FastAPI, with AI agents powered by LangChain.

## 🌟 Features

- **FastAPI** - Modern async API framework
- **AI Agents** - LangChain-based agents for WhatsApp, Gmail, chat, and task management
- **Firebase Authentication** - Secure user authentication
- **Supabase Database** - PostgreSQL-backed persistence
- **Multiple AI Providers** - Google Generative AI, Cohere, OpenAI
- **WebSocket Support** - Real-time messaging (ready for implementation)
- **Type Safety** - Full Pydantic validation
- **Error Handling** - Comprehensive error responses

## 📋 Prerequisites

- **Python 3.10+**
- **PostgreSQL** (via Supabase)
- **Firebase Project**
- **API Keys** for one or more AI providers (Google, OpenAI, or Cohere)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Install Playwright browser drivers (required for web scraping)
playwright install
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your credentials
# Required:
# - FIREBASE_ADMIN_CREDENTIALS_PATH
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
# - GOOGLE_AI_API_KEY (or OPENAI_API_KEY)
```

### 3. Run Development Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
backend/
├── app/
│   ├── core/              # Configuration management
│   │   └── config.py      # Settings (Pydantic)
│   ├── models/            # Data schemas
│   │   └── schemas.py     # Pydantic models
│   ├── routes/            # API endpoints
│   │   ├── auth.py        # Authentication
│   │   ├── chat.py        # Chat API
│   │   ├── tasks.py       # Task management
│   │   ├── whatsapp.py    # WhatsApp integration
│   │   └── gmail.py       # Gmail integration
│   ├── services/          # Business logic
│   │   ├── firebase_service.py    # Firebase operations
│   │   ├── supabase_service.py    # Database operations
│   │   └── ai_service.py          # AI/Embedding services
│   ├── agents/            # LangChain agents
│   │   └── base_agents.py # Agent implementations
│   ├── utils/             # Utility functions
│   └── main.py            # FastAPI app
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project metadata
├── .env.example          # Example environment
└── README.md             # This file
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/verify` - Verify Firebase token
- `POST /api/auth/refresh` - Token refresh

### Chat
- `POST /api/chat/message` - Send message to assistant
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/analyze-sentiment` - Analyze text sentiment

### Tasks
- `POST /api/tasks` - Create task
- `POST /api/tasks/from-text` - Create task from natural language
- `GET /api/tasks` - Get all tasks
- `GET /api/tasks/{task_id}` - Get specific task
- `PUT /api/tasks/{task_id}` - Update task
- `DELETE /api/tasks/{task_id}` - Delete task

### WhatsApp
- `GET /api/whatsapp/verify` - Webhook verification
- `POST /api/whatsapp/webhook` - Receive messages
- `POST /api/whatsapp/send` - Send message

### Gmail
- `POST /api/gmail/webhook` - Webhook notifications
- `POST /api/gmail/process-email` - Process email with AI
- `POST /api/gmail/oauth/authorize` - OAuth authorization
- `POST /api/gmail/oauth/callback` - OAuth callback

## 🤖 Agents

### ChatAgent
Main conversational assistant powered by LLM (Gemini, OpenAI, or Cohere).

**Capabilities:**
- Multi-turn conversations
- Sentiment analysis
- Context awareness

```python
from app.agents import ChatAgent

agent = ChatAgent(user_id="user123")
response = await agent.chat("Hello, how are you?")
```

### WhatsappAgent
Processes WhatsApp messages and determines actions.

**Capabilities:**
- Intent recognition
- Task creation from messages
- Automatic responses

```python
from app.agents import WhatsappAgent

agent = WhatsappAgent(user_id="user123")
result = await agent.process_message("Remind me to call mom", "+1234567890")
```

### GmailAgent
Analyzes emails and determines actions.

**Capabilities:**
- Email categorization
- Priority detection
- Automatic task creation

```python
from app.agents import GmailAgent

agent = GmailAgent(user_id="user123")
result = await agent.process_email("email_id", "Subject", "Body", "sender@example.com")
```

### TaskAgent
Creates tasks from natural language descriptions.

**Capabilities:**
- Title extraction
- Due date recognition
- Priority assignment

```python
from app.agents import TaskAgent

agent = TaskAgent(user_id="user123")
result = await agent.create_from_text("Meeting with John on Friday at 3 PM")
```

## 🔧 Services

### FirebaseService
Authentication and user management.

```python
from app.services import firebase_service

# Verify token
decoded = await firebase_service.verify_id_token(token)

# Get user
user = await firebase_service.get_user(uid)
```

### SupabaseService
Database operations.

```python
from app.services import supabase_service

# Create message
msg = await supabase_service.create_message(user_id, content, role)

# Get tasks
tasks = await supabase_service.get_tasks(user_id)
```

### AI Services

**EmbeddingService**
```python
from app.services import embedding_service

# Single embedding
embedding = await embedding_service.embed_text("Hello world")

# Batch embeddings
embeddings = await embedding_service.embed_batch(["text1", "text2"])
```

**GeminiService**
```python
from app.services import gemini_service

# Analyze text
analysis = await gemini_service.analyze_text(text, prompt)

# Analyze image
result = await gemini_service.analyze_image(base64_image, prompt)
```

## 🔐 Security

- **Firebase Auth** - Secure user authentication
- **CORS** - Configured origins
- **Environment Variables** - Secrets management via `.env`
- **Pydantic Validation** - Request validation
- **Error Handling** - Safe error responses

## 📦 Docker Deployment

```bash
# Build image
docker build -t coolie-assistant-backend .

# Run container
docker run -p 8000:8000 \
  -e FIREBASE_ADMIN_CREDENTIALS_PATH=/app/creds.json \
  -e SUPABASE_URL=https://... \
  -e SUPABASE_SERVICE_ROLE_KEY=... \
  coolie-assistant-backend
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app

# Watch mode
pytest-watch
```

## 📝 Environment Variables

See [.env.example](.env.example) for complete list.

**Required:**
- `FIREBASE_ADMIN_CREDENTIALS_PATH` - Path to Firebase service account
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `GOOGLE_AI_API_KEY` - Google Generative AI API key (or `OPENAI_API_KEY`)

**Optional:**
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - For Gmail OAuth
- `YOUTUBE_API_KEY` - For YouTube features
- `SESSION_SECRET_KEY` - For session management

## 🚀 Production Deployment

### Railway
```bash
railway init
railway add
railway up
```

### Render
```bash
# Set environment variables in Render dashboard
# Build Command: pip install -r requirements.txt
# Start Command: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Google Cloud Run
```bash
gcloud run deploy coolie-assistant-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars FIREBASE_ADMIN_CREDENTIALS_PATH=/etc/secrets/firebase.json
```

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

## 🤝 Contributing

1. Create virtual environment
2. Install dev dependencies: `pip install -r requirements.txt[dev]`
3. Format code: `black app/`
4. Run tests: `pytest`
5. Submit PR

## 📄 License

MIT License - See LICENSE file

## 🆘 Support

For issues and questions:
- Check [API Docs](/docs)
- Review error logs
- Check `.env` configuration
- Verify Firebase/Supabase credentials
