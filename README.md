# CoolieAssistant - AI-Powered Personal Assistant v2.0

A full-stack, production-ready AI assistant application that integrates multiple communication channels (Chat, WhatsApp, Gmail) with intelligent task management and automation. Built with modern technologies: React + Vite frontend, FastAPI backend, Firebase authentication, Supabase database, and LangChain AI agents.

**Live Demo:** Coming Soon | **Documentation:** See sections below

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Project Architecture](#project-architecture)
5. [Quick Start](#quick-start)
6. [Detailed Setup](#detailed-setup)
7. [Project Structure](#project-structure)
8. [API Documentation](#api-documentation)
9. [Database Schema](#database-schema)
10. [AI Agents](#ai-agents)
11. [Deployment](#deployment)
12. [Security](#security)
13. [Troubleshooting](#troubleshooting)
14. [Contributing](#contributing)

---

## 🎯 Overview

**CoolieAssistant** is an intelligent personal assistant that helps users manage tasks, communicate across multiple channels, and automate workflows using AI. It combines:

- **Multi-channel Integration:** Chat, WhatsApp, Gmail, YouTube
- **AI-Powered Intelligence:** Natural language processing, sentiment analysis, intent recognition
- **Task Management:** Create, organize, and track tasks from any channel
- **Automation:** Automatic task creation from messages, email categorization, priority detection
- **Real-time Processing:** Async-first architecture for zero-latency operations

### Use Cases

- 📱 **WhatsApp Integration:** Send messages like "Remind me to call mom tomorrow" and it creates a task
- 📧 **Gmail Integration:** Automatically categorize emails, detect priority, create tasks from important messages
- 💬 **Chat Interface:** Talk to AI assistant for task management, information retrieval, and automation
- 📊 **Dashboard:** View all tasks, messages, and notifications in one place
- 🔄 **Workflow Automation:** Trigger actions based on messages from any channel

---

## ✨ Key Features

### 🤖 AI & Automation
- **LangChain Agents** - Intelligent agents for WhatsApp, Gmail, Chat, and Tasks
- **Multiple AI Models** - Support for Google Gemini, OpenAI GPT-4, and Cohere
- **Natural Language Processing** - Understand user intent from messages
- **Sentiment Analysis** - Analyze emotional tone of messages
- **Smart Task Creation** - Extract tasks from natural language descriptions
- **Email Intelligence** - Categorize, prioritize, and summarize emails

### 💬 Multi-Channel Communication
- **Chat Interface** - Real-time chat with AI assistant
- **WhatsApp Integration** - Send/receive messages via WhatsApp Business API
- **Gmail Integration** - OAuth 2.0 integration for email processing
- **YouTube Detection** - Identify and process YouTube links
- **Notification System** - Real-time notifications across all channels

### 📋 Task Management
- **Create Tasks** - From chat, WhatsApp, Gmail, or manual entry
- **Smart Parsing** - Extract due dates, priorities, and descriptions from text
- **Task Tracking** - View status, update, and complete tasks
- **Priority Levels** - Low, Medium, High, Urgent
- **Due Date Management** - Calendar integration and reminders

### 🔐 Security & Authentication
- **Firebase Authentication** - Secure user login and management
- **JWT Tokens** - Secure API communication
- **Row-Level Security** - Database-level access control
- **Environment Variables** - Secrets management
- **HTTPS Ready** - Production-grade security

### 📊 Data & Analytics
- **Supabase Database** - PostgreSQL-backed persistence
- **Message History** - Store and retrieve chat history
- **User Preferences** - Personalized settings and configurations
- **Credentials Management** - Secure storage of OAuth tokens
- **Notifications Log** - Track all notifications

### 🚀 Performance & Scalability
- **Async-First Architecture** - FastAPI with async/await
- **Docker Containerization** - Easy deployment and scaling
- **Database Indexing** - Optimized queries
- **Caching** - React Query for client-side caching
- **Load Balancing** - Ready for horizontal scaling

---

## 🛠 Technology Stack

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.3.1 | UI framework |
| TypeScript | 5.6.3 | Type safety |
| Vite | 7.1.9 | Build tool |
| Tailwind CSS | 3.4.17 | Styling |
| Radix UI | Latest | Accessible components |
| React Query | 5.60.5 | Data fetching |
| React Hook Form | 7.55.0 | Form management |
| Zod | 3.25.1 | Schema validation |
| Firebase | 12.3.0 | Authentication |
| Wouter | 3.3.5 | Routing |
| Framer Motion | 11.13.1 | Animations |

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| FastAPI | 0.104+ | Web framework |
| Python | 3.10+ | Language |
| Uvicorn | 0.24+ | ASGI server |
| Pydantic | 2.5+ | Data validation |
| LangChain | 0.0.352+ | AI agents |
| Firebase Admin | 6.2+ | Authentication |
| Supabase | 2.3+ | Database client |
| Google Generative AI | Latest | Gemini API |
| OpenAI | 1.3.9+ | GPT-4 API |
| Cohere | 4.38+ | Embeddings |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| PostgreSQL | Database (via Supabase) |
| Firebase | Authentication & hosting |
| Nginx | Reverse proxy |

---

## 🏗 Project Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                           │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│   Web Chat   │  WhatsApp    │    Gmail     │   Mobile (Future)  │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Firebase Auth    │
                    │  (JWT Tokens)     │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────▼─────────────────────┐
        │         FastAPI Backend (Port 8000)       │
        ├─────────────────────────────────────────┤
        │  ┌──────────────────────────────────┐   │
        │  │   API Routes & Controllers       │   │
        │  │  /api/chat, /api/tasks, etc.    │   │
        │  └──────────────────────────────────┘   │
        │  ┌──────────────────────────────────┐   │
        │  │   LangChain AI Agents            │   │
        │  │  ChatAgent, WhatsappAgent, etc.  │   │
        │  └──────────────────────────────────┘   │
        │  ┌──────────────────────────────────┐   │
        │  │   Services Layer                 │   │
        │  │  Firebase, Supabase, AI APIs     │   │
        │  └──────────────────────────────────┘   │
        └─────────────────────┬─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌───▼────┐          ┌────▼────┐          ┌────▼────┐
    │Firebase │          │Supabase │          │External │
    │  Auth   │          │Database │          │  APIs   │
    │         │          │         │          │         │
    │ Users   │          │Messages │          │Gemini   │
    │ Tokens  │          │Tasks    │          │OpenAI   │
    │         │          │Prefs    │          │Cohere   │
    └─────────┘          └─────────┘          └─────────┘
```

### Data Flow

```
User Input (Chat/WhatsApp/Gmail)
    ↓
Firebase Authentication (Verify JWT)
    ↓
FastAPI Route Handler
    ↓
LangChain Agent (Process Intent)
    ↓
AI Model (Gemini/OpenAI/Cohere)
    ↓
Supabase Database (Store/Retrieve)
    ↓
Response to User
```

### Component Interaction

```
Frontend (React)
├── AuthContext (Firebase Auth)
├── ChatContext (Message State)
├── NotificationContext (Alerts)
├── ThemeProvider (Dark/Light Mode)
└── Pages
    ├── Login (Authentication)
    ├── Home (Dashboard)
    ├── Chat (AI Chat Interface)
    ├── Tasks (Task Management)
    ├── Settings (User Preferences)
    └── Personalization (Customization)

Backend (FastAPI)
├── Routes
│   ├── /api/auth (Authentication)
│   ├── /api/chat (Chat Messages)
│   ├── /api/tasks (Task Management)
│   ├── /api/whatsapp (WhatsApp Integration)
│   ├── /api/gmail (Gmail Integration)
│   ├── /api/notifications (Notifications)
│   ├── /api/website (Website Opening)
│   └── /api/youtube (YouTube Detection)
├── Services
│   ├── FirebaseService (Auth)
│   ├── SupabaseService (Database)
│   ├── EmbeddingService (AI Embeddings)
│   └── GeminiService (AI Analysis)
└── Agents
    ├── ChatAgent (Conversations)
    ├── WhatsappAgent (WhatsApp)
    ├── GmailAgent (Email)
    └── TaskAgent (Task Creation)
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose (optional)
- Firebase Project
- Supabase Project
- API Keys (Google Generative AI, OpenAI, or Cohere)

### 5-Minute Setup (Docker)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/CoolieAssistant.git
cd CoolieAssistant

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env with your credentials
# Required:
# - VITE_FIREBASE_API_KEY
# - VITE_FIREBASE_PROJECT_ID
# - VITE_FIREBASE_APP_ID
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
# - GOOGLE_AI_API_KEY (or OPENAI_API_KEY)

# 4. Start all services
docker-compose up -d

# 5. Access the app
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup (Local Development)

See [Detailed Setup](#detailed-setup) section below.

---

## 📖 Detailed Setup

### Backend Setup (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your editor

# Run development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend runs at:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### Frontend Setup (React)

```bash
cd client

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with backend URL
# VITE_API_URL=http://localhost:8000
# VITE_FIREBASE_API_KEY=your_key
# etc.

# Run development server
npm run dev
```

**Frontend runs at:** http://localhost:5173

### Environment Variables

#### Backend (.env)
```env
# Server
HOST=0.0.0.0
PORT=8000
ENV=development
DEBUG=true

# Firebase
FIREBASE_ADMIN_CREDENTIALS_PATH=/path/to/serviceAccount.json
FIREBASE_PROJECT_ID=your-project-id

# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI Providers (choose one or more)
EMBEDDING_PROVIDER=google  # cohere, google, openai
GOOGLE_AI_API_KEY=your-google-key
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...

# Google OAuth (optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/gmail/oauth/callback

# YouTube (optional)
YOUTUBE_API_KEY=...

# Session
SESSION_SECRET_KEY=your-secret-key-change-in-production

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_APP_ID=your-app-id
VITE_N8N_WEBHOOK_URL=http://localhost:5678/webhook  # optional
```

---

## 📁 Project Structure

```
CoolieAssistant/
│
├── backend/                          # Python FastAPI Backend
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py            # Settings & environment
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   ├── schemas.py           # Pydantic models
│   │   │   └── __init__.py
│   │   ├── routes/                  # API endpoints
│   │   │   ├── auth.py              # Authentication
│   │   │   ├── chat.py              # Chat messages
│   │   │   ├── tasks.py             # Task management
│   │   │   ├── whatsapp.py          # WhatsApp integration
│   │   │   ├── gmail.py             # Gmail integration
│   │   │   ├── website.py           # Website opening
│   │   │   ├── youtube.py           # YouTube detection
│   │   │   ├── notifications.py     # Notifications
│   │   │   └── __init__.py
│   │   ├── services/                # Business logic
│   │   │   ├── firebase_service.py  # Firebase auth
│   │   │   ├── supabase_service.py  # Database ops
│   │   │   ├── ai_service.py        # AI/Embeddings
│   │   │   └── __init__.py
│   │   ├── agents/                  # LangChain agents
│   │   │   ├── base_agents.py       # Agent implementations
│   │   │   └── __init__.py
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   ├── main.py                  # FastAPI app
│   │   └── __init__.py
│   ├── requirements.txt              # Python dependencies
│   ├── requirements-pinned.txt       # Pinned versions
│   ├── pyproject.toml               # Project metadata
│   ├── Dockerfile                   # Docker image
│   ├── .env.example                 # Environment template
│   ├── README.md                    # Backend documentation
│   └── DATABASE_SCHEMA.md           # Database schema
│
├── client/                           # React + Vite Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── AppSidebar.tsx       # Navigation
│   │   │   ├── ChatBubble.tsx       # Message display
│   │   │   ├── ChatInput.tsx        # Message input
│   │   │   ├── TaskCard.tsx         # Task display
│   │   │   ├── ErrorBoundary.tsx    # Error handling
│   │   │   ├── NotificationBell.tsx # Notifications
│   │   │   ├── ThemeToggle.tsx      # Theme switcher
│   │   │   └── examples/            # Example components
│   │   ├── pages/
│   │   │   ├── Home.tsx             # Dashboard
│   │   │   ├── Login.tsx            # Authentication
│   │   │   ├── Chat.tsx             # Chat interface
│   │   │   ├── Tasks.tsx            # Task management
│   │   │   ├── Settings.tsx         # User settings
│   │   │   ├── Personalization.tsx  # Customization
│   │   │   ├── Website.tsx          # Website opener
│   │   │   └── not-found.tsx        # 404 page
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx      # Auth state
│   │   │   ├── ChatContext.tsx      # Chat state
│   │   │   ├── NotificationContext.tsx # Notifications
│   │   │   └── ThemeProvider.tsx    # Theme state
│   │   ├── hooks/
│   │   │   ├── use-mobile.tsx       # Mobile detection
│   │   │   ├── use-toast.ts         # Toast notifications
│   │   │   └── use-microphone.ts    # Microphone access
│   │   ├── lib/
│   │   │   ├── api.ts               # API client
│   │   │   ├── firebase.ts          # Firebase init
│   │   │   ├── queryClient.ts       # React Query setup
│   │   │   └── utils.ts             # Utilities
│   │   ├── App.tsx                  # Root component
│   │   ├── main.tsx                 # Entry point
│   │   └── index.css                # Global styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── .env.example
│   └── README.md
│
├── shared/                           # Shared types & schemas
│   └── schema.ts
│
├── docker-compose.yml                # Multi-container setup
├── .env.example                      # Root environment template
├── .gitignore                        # Git ignore rules
├── package.json                      # Root package config
├── tsconfig.json                     # TypeScript config
├── tailwind.config.ts                # Tailwind config
├── vite.config.ts                    # Vite config
├── components.json                   # shadcn/ui config
├── postcss.config.js                 # PostCSS config
│
├── GIT_SECURITY_SETUP.md             # Security best practices
├── ISSUES_FIXED.md                   # Fixed issues documentation
├── FIXES_SUMMARY.md                  # Quick fixes summary
├── README.md                         # This file
└── LICENSE                           # MIT License
```

---

## 🔌 API Documentation

### Base URL
- **Development:** http://localhost:8000
- **Production:** https://api.example.com

### Authentication
All endpoints (except `/api/auth/verify`) require Firebase JWT token in header:
```
Authorization: Bearer <firebase_id_token>
```

### Endpoints

#### Authentication
```
POST /api/auth/verify
  Body: { token: string }
  Response: { valid: boolean, user_id: string }

POST /api/auth/refresh
  Response: { token: string }
```

#### Chat
```
POST /api/chat/message
  Body: { message: string, user_id: string }
  Response: { response: string, sentiment: string }

GET /api/chat/history?limit=50&offset=0
  Response: { messages: Message[], total: number }

POST /api/chat/analyze-sentiment
  Body: { text: string }
  Response: { sentiment: string, score: number }
```

#### Tasks
```
POST /api/tasks
  Body: { title: string, description: string, due_date: string, priority: string }
  Response: { id: string, ...task }

POST /api/tasks/from-text
  Body: { text: string }
  Response: { id: string, ...task }

GET /api/tasks?status=pending&priority=high
  Response: { tasks: Task[], total: number }

GET /api/tasks/{task_id}
  Response: { ...task }

PUT /api/tasks/{task_id}
  Body: { title?: string, status?: string, ... }
  Response: { ...updated_task }

DELETE /api/tasks/{task_id}
  Response: { success: boolean }
```

#### WhatsApp
```
GET /api/whatsapp/verify?hub.challenge=xxx
  Response: hub.challenge (for webhook verification)

POST /api/whatsapp/webhook
  Body: { entry: [...] }  # WhatsApp webhook payload
  Response: { success: boolean }

POST /api/whatsapp/send
  Body: { phone_number: string, message: string }
  Response: { message_id: string }
```

#### Gmail
```
POST /api/gmail/process-email
  Body: { email_id: string, subject: string, body: string }
  Response: { summary: string, priority: string, task?: Task }

POST /api/gmail/oauth/authorize
  Response: { auth_url: string }

POST /api/gmail/oauth/callback
  Body: { code: string }
  Response: { success: boolean }
```

#### Notifications
```
GET /api/notifications?limit=20
  Response: { notifications: Notification[], total: number }

PUT /api/notifications/{notification_id}/read
  Response: { success: boolean }
```

**Full API Documentation:** http://localhost:8000/docs (Swagger UI)

---

## 🗄 Database Schema

### Tables Overview

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `users` | User accounts | id, firebase_uid, email, display_name |
| `chat_messages` | Chat history | id, user_id, content, role, sentiment |
| `tasks` | Task management | id, user_id, title, status, priority, due_date |
| `user_preferences` | User settings | id, user_id, theme, language, timezone |
| `user_credentials` | OAuth tokens | id, user_id, service, encrypted_value |
| `notifications` | User alerts | id, user_id, title, type, is_read |
| `whatsapp_messages` | WhatsApp history | id, user_id, phone_number, content, direction |
| `gmail_messages` | Gmail metadata | id, user_id, gmail_id, subject, sender, body |

**Detailed Schema:** See [backend/DATABASE_SCHEMA.md](backend/DATABASE_SCHEMA.md)

---

## 🤖 AI Agents

### ChatAgent
**Purpose:** Main conversational AI for multi-turn chats

**Capabilities:**
- Natural language understanding
- Context-aware responses
- Sentiment analysis
- Task extraction from conversation

**Example:**
```python
agent = ChatAgent(user_id="user123")
response = await agent.chat("Create a task to call mom tomorrow at 3 PM")
# Response: "I've created a task 'Call mom' for tomorrow at 3 PM"
```

### WhatsappAgent
**Purpose:** Process WhatsApp messages and determine actions

**Capabilities:**
- Intent recognition
- Automatic task creation
- Message categorization
- Sentiment analysis

**Example:**
```python
agent = WhatsappAgent(user_id="user123")
result = await agent.process_message("Remind me to buy groceries", "+1234567890")
# Creates task and sends confirmation
```

### GmailAgent
**Purpose:** Analyze emails and organize them

**Capabilities:**
- Email categorization
- Priority detection
- Automatic task creation
- Summary generation

**Example:**
```python
agent = GmailAgent(user_id="user123")
result = await agent.process_email("email_id", "Subject", "Body", "sender@example.com")
# Analyzes email and creates task if needed
```

### TaskAgent
**Purpose:** Create tasks from natural language

**Capabilities:**
- Title extraction
- Due date recognition
- Priority assignment
- Description parsing

**Example:**
```python
agent = TaskAgent(user_id="user123")
result = await agent.create_from_text("Meeting with John on Friday at 3 PM")
# Creates task with extracted details
```

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build images
docker-compose build

# Run services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Railway Deployment

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### Render Deployment

1. Connect GitHub repository
2. Create new Web Service
3. Set environment variables
4. Deploy

### Google Cloud Run

```bash
# Deploy backend
gcloud run deploy coolie-backend \
  --source backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars FIREBASE_ADMIN_CREDENTIALS_PATH=/etc/secrets/firebase.json

# Deploy frontend
gcloud run deploy coolie-frontend \
  --source client \
  --platform managed \
  --region us-central1
```

---

## 🔐 Security

### Best Practices
- ✅ Never commit `.env` files
- ✅ Use environment variables for secrets
- ✅ Rotate API keys regularly
- ✅ Use separate credentials for dev/prod
- ✅ Enable Firebase security rules
- ✅ Use HTTPS in production
- ✅ Implement rate limiting
- ✅ Validate all inputs

### Security Features
- Firebase JWT authentication
- Row-level database security
- CORS configuration
- Pydantic input validation
- Non-root Docker users
- Encrypted credential storage

**See:** [GIT_SECURITY_SETUP.md](GIT_SECURITY_SETUP.md)

---

## 🐛 Troubleshooting

### Backend Issues

**Backend won't start**
```bash
# Check Python version
python --version  # Should be 3.10+

# Check .env file
cat .env  # Verify all required variables

# Check Firebase credentials
ls -la /path/to/serviceAccount.json

# Check port availability
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

**Database connection error**
```bash
# Verify Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# Test connection
python -c "from supabase import create_client; create_client('$SUPABASE_URL', '$SUPABASE_SERVICE_ROLE_KEY')"
```

### Frontend Issues

**Frontend can't reach backend**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check VITE_API_URL
echo $VITE_API_URL

# Check browser console for CORS errors
# Verify backend CORS_ORIGINS includes frontend URL
```

**Firebase not initializing**
```bash
# Check environment variables
echo $VITE_FIREBASE_API_KEY
echo $VITE_FIREBASE_PROJECT_ID
echo $VITE_FIREBASE_APP_ID

# Check browser console for errors
# Verify Firebase project is active
```

### Common Errors

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Run `pip install -r requirements.txt` |
| `CORS error` | Check backend `CORS_ORIGINS` setting |
| `Firebase not initialized` | Verify `VITE_FIREBASE_*` environment variables |
| `Supabase connection failed` | Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` |
| `Port already in use` | Change port or kill process using it |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open pull request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Use meaningful commit messages
- Keep PRs focused and small

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 📚 Additional Resources

- **Backend Documentation:** [backend/README.md](backend/README.md)
- **Frontend Documentation:** [client/README.md](client/README.md)
- **Database Schema:** [backend/DATABASE_SCHEMA.md](backend/DATABASE_SCHEMA.md)
- **Security Setup:** [GIT_SECURITY_SETUP.md](GIT_SECURITY_SETUP.md)
- **Issues Fixed:** [ISSUES_FIXED.md](ISSUES_FIXED.md)
- **API Docs:** http://localhost:8000/docs

---

## 🆘 Support

- 📧 **Email:** support@example.com
- 💬 **Issues:** Create GitHub issue
- 📖 **Docs:** Check documentation files
- 🐛 **Bugs:** Report with reproduction steps

---

## 🎉 Acknowledgments

Built with modern technologies and best practices. Special thanks to:
- FastAPI community
- React community
- Firebase team
- Supabase team
- LangChain developers

---

**Last Updated:** April 2026 | **Version:** 2.0.0
