# CoolieAssistant - AI-Powered Personal Assistant v2.0

A full-stack, production-ready AI assistant application that integrates multiple communication channels (Chat, WhatsApp, Gmail) with intelligent task management and automation. Built with modern technologies: React + Vite frontend, FastAPI backend, Firebase authentication, Supabase database, and LangChain AI agents.

**Status:** ✅ Production Ready | **Version:** 2.0.0 | **Last Updated:** April 2026

---

## 📋 Quick Navigation

**Getting Started:**
- [🚀 Quick Start (5 minutes)](#quick-start)
- [📖 Detailed Setup Guide](#detailed-setup)
- [🐛 Troubleshooting](#troubleshooting)

**Documentation:**
- [🎯 Project Overview](#overview)
- [✨ Features](#key-features)
- [🛠 Tech Stack](#technology-stack)
- [🏗 Architecture](#project-architecture)
- [📁 Project Structure](#project-structure)

**Development:**
- [🔌 API Documentation](#api-documentation)
- [🗄 Database Schema](#database-schema)
- [🤖 AI Agents](#ai-agents)
- [🚀 Deployment](#deployment)
- [🔐 Security](#security)

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
14. [Known Limitations](#known-limitations)
15. [Contributing](#contributing)

---

## 🎯 Overview

**CoolieAssistant** is an intelligent personal assistant that helps users manage tasks, communicate across multiple channels, and automate workflows using AI. It combines:

- **Multi-channel Integration:** Chat, WhatsApp, Gmail, YouTube
- **AI-Powered Intelligence:** Natural language processing, sentiment analysis, intent recognition
- **Task Management:** Create, organize, and track tasks from any channel
- **Automation:** Automatic task creation from messages, email categorization, priority detection
- **Real-time Processing:** Async-first architecture for zero-latency operations

### What You Can Do

- 📱 **WhatsApp Integration:** Send messages like "Remind me to call mom tomorrow" and it creates a task
- 📧 **Gmail Integration:** Automatically categorize emails, detect priority, create tasks from important messages
- 💬 **Chat Interface:** Talk to AI assistant for task management, information retrieval, and automation
- 📊 **Dashboard:** View all tasks, messages, and notifications in one place
- 🔄 **Workflow Automation:** Trigger actions based on messages from any channel
- 🤖 **AI-Powered Analysis:** Sentiment analysis, intent recognition, and smart task extraction
- 🔐 **Secure & Private:** Firebase authentication with row-level database security

### Who Should Use This

- **Developers** building AI-powered applications
- **Teams** needing multi-channel communication management
- **Businesses** automating task creation and email processing
- **Individuals** wanting a personal AI assistant

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
- Firebase Project (free tier works)
- Supabase Project (free tier works)
- At least one AI API key (Google Generative AI, OpenAI, or Cohere)

### Option 1: Docker (Recommended for Quick Testing)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/CoolieAssistant.git
cd CoolieAssistant

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your credentials (see Detailed Setup)

# 3. Start all services
docker-compose up -d

# 4. Access the app
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd client
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Verify Setup

1. **Backend Health:** `curl http://localhost:8000/health`
   - Should return: `{"status": "ok"}`

2. **Frontend:** Open http://localhost:5173
   - Should see login page

3. **API Docs:** Open http://localhost:8000/docs
   - Should see interactive Swagger UI

---

## 📖 Detailed Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/CoolieAssistant.git
cd CoolieAssistant
```

### Step 2: Configure Environment Variables

Copy the example file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# ============================================
# REQUIRED - Must be configured
# ============================================

# Firebase (Get from Firebase Console)
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_APP_ID=1:123456:web:abc...

# Supabase (Get from Supabase Dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# AI Provider (Choose one or more)
# Option 1: Google Generative AI (Recommended - Free tier available)
GOOGLE_AI_API_KEY=AIzaSy...

# Option 2: OpenAI
# OPENAI_API_KEY=sk-...

# Option 3: Cohere
# COHERE_API_KEY=...

# ============================================
# OPTIONAL - For specific features
# ============================================

# Gmail Integration (Optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/gmail/oauth/callback

# YouTube Detection (Optional)
YOUTUBE_API_KEY=...

# Frontend API URL (Usually auto-detected)
VITE_API_URL=http://localhost:8000

# ============================================
# BACKEND ONLY
# ============================================

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENV=development
DEBUG=true

# Session Security (Change in production!)
SESSION_SECRET_KEY=your-secret-key-change-in-production

# CORS Origins (Comma-separated)
CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
```

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Backend URLs:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Step 4: Frontend Setup

Open a new terminal:

```bash
cd client

# Install dependencies
npm install

# Run development server
npm run dev
```

**Expected Output:**
```
  VITE v7.1.9  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

**Frontend URL:**
- App: http://localhost:5173

### Step 5: Database Setup

The database schema is automatically created by Supabase. If you need to manually initialize:

1. Go to Supabase Dashboard
2. Open SQL Editor
3. Run the SQL from `backend/DATABASE_SCHEMA.md`

Or use the provided script:
```bash
# This is optional - Supabase handles it automatically
psql -h your-supabase-host -U postgres -d postgres -f backend/supabase_init.sql
```

### Step 6: Verify Everything Works

1. **Backend Health:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "ok"}
   ```

2. **Frontend Access:**
   - Open http://localhost:5173
   - Should see login page

3. **API Documentation:**
   - Open http://localhost:8000/docs
   - Try a test endpoint

4. **Create Account:**
   - Sign up with email on login page
   - Should redirect to dashboard

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
# Check Python version (must be 3.10+)
python --version

# Check if port 8000 is in use
# Windows:
netstat -ano | findstr :8000
# macOS/Linux:
lsof -i :8000

# Kill process using port (if needed)
# Windows:
taskkill /PID <PID> /F
# macOS/Linux:
kill -9 <PID>

# Try different port
python -m uvicorn app.main:app --reload --port 8001
```

**ModuleNotFoundError: No module named 'fastapi'**
```bash
# Make sure virtual environment is activated
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Supabase connection error**
```bash
# Verify credentials
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# Test connection
python -c "from supabase import create_client; print('OK')"

# Check .env file exists and has values
cat .env | grep SUPABASE
```

**Firebase authentication fails**
```bash
# Check Firebase credentials are set
echo $FIREBASE_PROJECT_ID

# Verify Firebase project is active in console
# Check security rules allow your app
```

### Frontend Issues

**Frontend can't reach backend**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check VITE_API_URL is correct
echo $VITE_API_URL

# Check browser console (F12) for CORS errors
# Verify backend CORS_ORIGINS includes http://localhost:5173
```

**Firebase not initializing**
```bash
# Check environment variables
echo $VITE_FIREBASE_API_KEY
echo $VITE_FIREBASE_PROJECT_ID
echo $VITE_FIREBASE_APP_ID

# Check browser console (F12) for errors
# Verify Firebase project is active
```

**npm install fails**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

**Port 5173 already in use**
```bash
# Find process using port
# Windows:
netstat -ano | findstr :5173
# macOS/Linux:
lsof -i :5173

# Kill process or use different port
npm run dev -- --port 5174
```

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `CORS error in browser` | Backend CORS not configured | Check `CORS_ORIGINS` in `.env` |
| `Firebase not initialized` | Missing Firebase credentials | Check `VITE_FIREBASE_*` in `.env` |
| `Supabase connection failed` | Wrong credentials or offline | Verify `SUPABASE_URL` and key |
| `Port already in use` | Another process using port | Kill process or use different port |
| `Module not found` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `Cannot find module '@/components'` | Path alias not working | Check `vite.config.ts` and `tsconfig.json` |
| `API returns 401 Unauthorized` | Firebase token invalid | Check token in browser DevTools |
| `Database query fails` | Supabase not initialized | Run database schema setup |

### Debug Mode

**Enable verbose logging:**

Backend:
```bash
# Set DEBUG=true in .env
DEBUG=true
python -m uvicorn app.main:app --reload --log-level debug
```

Frontend:
```bash
# Check browser console (F12)
# Look for network requests in Network tab
# Check Application tab for stored tokens
```

### Getting Help

1. **Check logs:**
   - Backend terminal for API errors
   - Browser console (F12) for frontend errors
   - Browser Network tab for API calls

2. **Verify configuration:**
   - Check `.env` file has all required variables
   - Check Firebase project is active
   - Check Supabase project is accessible

3. **Test endpoints:**
   - Use http://localhost:8000/docs to test API
   - Use curl to test backend connectivity
   - Check browser DevTools for frontend issues

4. **Common fixes:**
   - Restart backend and frontend
   - Clear browser cache (Ctrl+Shift+Delete)
   - Reinstall dependencies
   - Check internet connection

---

## ⚠️ Known Limitations

### Current Implementation Status

**Fully Implemented:**
- ✅ Chat interface with AI responses
- ✅ Task creation and management
- ✅ Firebase authentication
- ✅ Supabase database integration
- ✅ User preferences and settings
- ✅ Notification system
- ✅ Theme switching (dark/light mode)
- ✅ Sentiment analysis
- ✅ Task extraction from text

**Partially Implemented:**
- ⚠️ **WhatsApp Integration** - Webhook receiving works, but sending messages requires Twilio/Vonage setup (TODO in code)
- ⚠️ **Gmail Integration** - Webhook receiving works, but OAuth flow and email fetching need completion (TODO in code)
- ⚠️ **YouTube Detection** - Link detection works, but full video processing not implemented

**Not Yet Implemented:**
- ❌ Real-time WebSocket messaging
- ❌ Email notifications
- ❌ Rate limiting on API endpoints
- ❌ Advanced caching layer (Redis)
- ❌ Automated testing suite
- ❌ CI/CD pipeline
- ❌ Mobile app
- ❌ Multi-language support

### What This Means

- **For Development:** The project is suitable for learning and development. Some features are stubbed out with TODO comments.
- **For Production:** Core features (chat, tasks, auth) are production-ready. External integrations (WhatsApp, Gmail) need additional setup.
- **For Deployment:** Docker setup is ready, but you'll need to configure external services (Firebase, Supabase, AI APIs).

### Roadmap

**Next Phase:**
1. Complete WhatsApp send implementation
2. Complete Gmail OAuth flow
3. Add rate limiting
4. Implement WebSocket support
5. Add test suite

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
