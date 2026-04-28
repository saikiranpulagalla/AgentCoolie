# Coolie Assistant v2.0

An AI-enabled assistant web app combining a **React + Vite frontend** with a **FastAPI backend**. The project integrates Firebase authentication, Supabase database, LangChain AI agents, and multiple embedding providers (Cohere, Google, OpenAI).

**Architecture**: Decoupled frontend and backend services with proper separation of concerns, async-first design, and production-ready infrastructure.

---

## Key Features
- ⚡ **FastAPI Backend** - Modern async Python with LangChain AI agents (replaces Express/n8n)
- 🎨 **React + Vite Frontend** - Latest tooling for fast development and builds
- 🤖 **AI Agents** - WhatsApp, Gmail, Chat, and Task agents powered by LangChain
- 🔐 **Firebase Auth** - Secure user authentication and management
- 💾 **Supabase Database** - PostgreSQL-backed persistence
- 🧠 **Multiple AI Models** - Google Generative AI, OpenAI, Cohere support
- 📦 **Docker & Docker Compose** - Full-stack deployment ready
- 🔄 **Async Processing** - Zero-latency agent execution (no n8n overhead)

---

## Project Structure

```
CoolieAssistant/
├── backend/                      # Python FastAPI backend (NEW)
│   ├── app/
│   │   ├── core/                # Configuration & settings
│   │   ├── models/              # Pydantic schemas
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Firebase, Supabase, AI services
│   │   ├── agents/              # LangChain agent implementations
│   │   └── main.py              # FastAPI app
│   ├── requirements.txt          # Python dependencies
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md                # Backend documentation
├── client/                       # React + Vite frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom hooks
│   │   ├── contexts/            # React context providers
│   │   ├── lib/                 # Utilities and API client
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   └── README.md
├── shared/                       # Shared types & schemas
├── docker-compose.yml            # Full-stack deployment
├── .env.example                 # Root environment template
└── README.md                     # This file
```

---

## Prerequisites

### Backend
- **Python 3.10+**
- **Firebase Project** with service account
- **Supabase Project** (PostgreSQL database)
- **API Keys** - One or more of: Google Generative AI, OpenAI, or Cohere

### Frontend
- **Node.js 18+**
- **npm or pnpm**

### Deployment (Optional)
- **Docker & Docker Compose**
- **Cloud account** (Railway, Render, Google Cloud Run, etc.)

---

## Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
# Backend (python)
FIREBASE_ADMIN_CREDENTIALS_PATH=/path/to/serviceAccount.json
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here
GOOGLE_AI_API_KEY=your-google-key
OPENAI_API_KEY=sk-...

# Frontend (react/vite)
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_APP_ID=your-app-id
VITE_API_URL=http://localhost:8000
```

**Full configuration details**: See `backend/.env.example` and root `.env.example`

---

## Quick Start (Development)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and setup
git clone <repo>
cd CoolieAssistant

# Copy env file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start all services (backend, frontend, db)
docker-compose up -d

# Access the app
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Local Development

#### Backend (Python)

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

# Copy and configure .env
cp .env.example .env
# Edit .env with your credentials

# Run development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend starts at `http://localhost:8000`
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### Frontend (React)

```bash
cd client

# Install dependencies
npm install

# Create .env with backend URL
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

Frontend starts at `http://localhost:5173`

---

## API Endpoints

### Authentication
- `POST /api/auth/verify` - Verify Firebase token

### Chat
- `POST /api/chat/message` - Send message to assistant
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/analyze-sentiment` - Analyze sentiment

### Tasks
- `POST /api/tasks` - Create task
- `POST /api/tasks/from-text` - Create from natural language
- `GET /api/tasks` - Get all tasks
- `PUT /api/tasks/{task_id}` - Update task
- `DELETE /api/tasks/{task_id}` - Delete task

### WhatsApp
- `GET /api/whatsapp/verify` - Webhook verification
- `POST /api/whatsapp/webhook` - Receive messages
- `POST /api/whatsapp/send` - Send message

### Gmail
- `POST /api/gmail/process-email` - Process with AI
- `POST /api/gmail/oauth/authorize` - Start OAuth flow
- `POST /api/gmail/oauth/callback` - Handle OAuth callback

**Full API documentation available at**: `/docs` (Swagger UI)

---

## Build & Deployment

### Production Build

```bash
# Backend (creates optimized Python package)
cd backend
pip install -r requirements.txt
# Uses Python 3.11+ slim image in Docker

# Frontend (creates dist/ folder)
cd client
npm run build
# Creates optimized static files
```

### Docker Deployment

```bash
# Build images
docker-compose build

# Run (with environment variables)
docker-compose up

# Scale backend if needed
docker-compose up -d --scale backend=3
```

### Cloud Deployment

#### Railway
```bash
railway login
railway init
railway up
```

#### Render
```bash
# Set environment variables in Render dashboard
# Build: pip install -r requirements.txt
# Start: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Google Cloud Run
```bash
gcloud run deploy coolie-backend \
  --source backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars FIREBASE_ADMIN_CREDENTIALS_PATH=/etc/secrets/firebase.json
```

---

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await
- **Agents**: LangChain-based agents for AI operations
- **Database**: Supabase (PostgreSQL)
- **Auth**: Firebase Admin SDK
- **AI Models**: Gemini, OpenAI, Cohere (pluggable)
- **Real-time**: WebSocket ready

### Frontend (React)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Auth**: Firebase SDK
- **UI**: Radix UI + Tailwind CSS
- **State**: React Query + Zustand/Context
- **HTTP**: Fetch API with error handling

### Data Flow
```
User Input (React)
    ↓
Firebase Auth Token
    ↓
FastAPI Backend
    ↓
LangChain Agents
    ↓
External APIs (Gemini, OpenAI, Cohere)
    ↓
Supabase Database
    ↓
Response to Frontend
```

---

## Configuration

### Backend Configuration (app/core/config.py)

Uses Pydantic settings with environment variables:
- Server: `HOST`, `PORT`, `ENV`, `DEBUG`
- Firebase: `FIREBASE_ADMIN_CREDENTIALS_PATH` or `FIREBASE_SERVICE_ACCOUNT_JSON`
- Database: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- AI Providers: `GOOGLE_AI_API_KEY`, `OPENAI_API_KEY`, `COHERE_API_KEY`
- OAuth: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

### Frontend Configuration (vite.config.ts)

Environment variables prefixed with `VITE_`:
- `VITE_API_URL` - Backend API endpoint
- `VITE_FIREBASE_API_KEY` - Firebase client key
- `VITE_FIREBASE_PROJECT_ID` - Firebase project
- `VITE_FIREBASE_APP_ID` - Firebase app

---

## AI Agents

### ChatAgent
Main conversational assistant for multi-turn chats.

### WhatsappAgent
Processes WhatsApp messages and determines automatic actions.

### GmailAgent
Analyzes emails and organizes them into tasks.

### TaskAgent
Creates tasks from natural language descriptions.

See `backend/README.md` for detailed agent documentation.

---

## Security

- ✅ Firebase authentication
- ✅ Environment variable secrets
- ✅ CORS configured
- ✅ Pydantic validation
- ✅ Non-root Docker users
- ✅ HTTPS ready (use reverse proxy)

**Security best practices**:
- Never commit `.env` files
- Use cloud secret managers (AWS Secrets, GCP Secret Manager, etc.)
- Rotate API keys regularly
- Use separate credentials for dev/prod
- Enable Firebase security rules

---

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.10+)
- Verify `.env` file exists and has all required keys
- Check Firebase credentials file path
- Look for typos in environment variables

### Frontend can't reach backend
- Verify backend is running on port 8000
- Check `VITE_API_URL` environment variable
- Look for CORS errors in browser console
- Verify backend CORS_ORIGINS includes frontend URL

### Database errors
- Verify Supabase credentials
- Check network connectivity
- Ensure migrations have run
- Check Supabase dashboard for table creation

### AI model errors
- Verify API keys are set correctly
- Check API key quotas in provider dashboard
- Ensure provider is configured in `.env`
- Test with simple prompts first

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open pull request

---

## License

MIT License - See LICENSE file for details

---

## Support & Resources

- 📚 **Backend Docs**: [backend/README.md](backend/README.md)
- 🎨 **Frontend Docs**: See React components
- 🔗 **API Docs**: http://localhost:8000/docs
- 💬 **Issues**: Create GitHub issue
- 📧 **Email**: support@example.com

---

## Version History

### v2.0.0 (Current)
- ✅ FastAPI backend (replaces Express)
- ✅ LangChain agents (replaces n8n)
- ✅ Docker & Docker Compose
- ✅ Production-ready architecture

### v1.0.0 (Legacy)
- Express.js backend
- n8n workflow orchestration
- See `server/` folder (deprecated)

- Follow the existing TypeScript + project style.
- When adding features that require new env vars, update `README.md` and add sensible defaults where appropriate.

---

## Security & Best Practices
- Keep secret keys out of the repo. Use platform secret stores (Cloud Run secrets, Render secrets, GitHub Actions secrets, etc.).
- Rotate keys if exposed.
- Limit service-role keys usage (prefer scoped API keys where possible).

---

## Contact / Credits

This project was organized by the repository owner. For questions about specific integrations, open an issue or reach out to the maintainer.
