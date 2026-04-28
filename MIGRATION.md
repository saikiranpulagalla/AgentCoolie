# Migration Guide: Express to FastAPI

This document outlines the migration from the legacy Express.js + n8n backend to the new FastAPI backend.

---

## What Changed

### ❌ Removed
- **Express.js server** (`server/index.ts`) - No longer needed
- **n8n webhook integration** - Replaced with direct LangChain agents
- **TypeScript backend** - Now Python-based
- **Vite mounting in Express** - Separated concerns

### ✅ Added
- **FastAPI backend** (`backend/app/`) - Modern async Python framework
- **LangChain agents** - Direct AI agent execution without external platform
- **Separated frontend/backend** - Independent services
- **Docker support** - Full containerization for both services
- **Production-ready architecture** - Proper separation of concerns

---

## Breaking Changes

### API Endpoints
All API endpoints remain the same but now point to FastAPI:

```javascript
// Before (Express on port 5050)
fetch('http://localhost:5050/api/chat/message')

// After (FastAPI on port 8000)
fetch('http://localhost:8000/api/chat/message')
```

### Environment Variables
No changes required - same env vars work on both backends:
```bash
FIREBASE_ADMIN_CREDENTIALS_PATH
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
GOOGLE_AI_API_KEY  # or OPENAI_API_KEY or COHERE_API_KEY
```

### Server Port
- **Before**: 5050 (Express serving frontend + backend)
- **After**: 
  - Backend: 8000 (FastAPI)
  - Frontend: 5173 (Vite dev) or 80 (nginx in Docker)

---

## Migration Steps

### 1. Update Environment Variables

```bash
# Create backend/.env from backend/.env.example
cp backend/.env.example backend/.env

# Fill in the same credentials as before
# All variables remain compatible
```

### 2. Install Backend Dependencies

```bash
cd backend

# Create Python virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Install Playwright browsers (for web scraping)
playwright install
```

### 3. Update Frontend API Configuration

Frontend should automatically use:
```bash
VITE_API_URL=http://localhost:8000
```

Or update manually in frontend `.env.local`.

### 4. Start Services

**Option A: Docker Compose (Easiest)**
```bash
docker-compose up -d
# Everything runs automatically
```

**Option B: Local Development**
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd client
npm run dev

# Terminal 3: Optional - Proxy for convenience
# Not needed with proper VITE_API_URL
```

### 5. Verify It Works

```bash
# Check backend health
curl http://localhost:8000/health

# Check API documentation
# Visit http://localhost:8000/docs

# Check frontend
# Visit http://localhost:5173 (dev) or http://localhost (Docker)
```

---

## Data Migration

### Supabase Tables (No Changes)
All Supabase tables remain the same:
- ✅ `users`
- ✅ `chat_messages`
- ✅ `tasks`
- ✅ `user_preferences`
- ✅ `user_credentials`
- ✅ `notifications`

No data migration needed! FastAPI uses the same database.

### Firebase (No Changes)
- ✅ User authentication
- ✅ ID tokens
- ✅ User credentials

No changes to Firebase setup needed.

---

## API Changes

### Same Endpoints, Same Behavior

```bash
# Chat
POST /api/chat/message          # Same request/response
GET  /api/chat/history
POST /api/chat/analyze-sentiment

# Tasks
POST /api/tasks
POST /api/tasks/from-text
GET  /api/tasks
PUT  /api/tasks/{task_id}
DELETE /api/tasks/{task_id}

# WhatsApp
POST /api/whatsapp/webhook
POST /api/whatsapp/send

# Gmail
POST /api/gmail/process-email
POST /api/gmail/oauth/authorize
POST /api/gmail/oauth/callback
```

### Requests & Responses

Request/response formats are **100% compatible**. No frontend code changes needed!

```typescript
// This code works on both Express and FastAPI
const response = await fetch('http://localhost:8000/api/chat/message', {
  method: 'POST',
  body: JSON.stringify({ content: 'Hello' })
});
```

---

## Performance Improvements

### Latency
- ✅ **Reduced** - Direct agent execution vs n8n round-trips
- ✅ **Async-first** - Python asyncio for concurrent requests
- ✅ **Optimized** - FastAPI is faster than Express for async

### Scalability
- ✅ **Horizontal** - Easy to scale with Docker
- ✅ **Database** - Supabase handles multi-region
- ✅ **Load balancing** - nginx in docker-compose ready

### Deployment
- ✅ **Containerized** - Docker images for both services
- ✅ **Stateless** - Backend is stateless, easy to scale
- ✅ **Health checks** - Built-in liveness probes

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Ensure venv is activated and requirements installed
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### "Address already in use" on port 8000
```bash
# Another process is using port 8000
# Either:
# 1. Change port in app/core/config.py
# 2. Kill the other process
pk ill -f "uvicorn" # macOS/Linux
```

### Frontend can't connect to backend
```bash
# Check VITE_API_URL is set correctly
echo $VITE_API_URL

# Should output: http://localhost:8000
```

### Firebase authentication fails
```bash
# Check Firebase credentials are loaded
curl http://localhost:8000/health  # Should work

# If health check fails, Firebase init failed
# Check backend/.env for FIREBASE_ADMIN_CREDENTIALS_PATH
```

---

## Rollback (If Needed)

If you need to go back to Express:

```bash
# Switch back to legacy server
git checkout server/
git checkout package.json
git checkout tsconfig.json

# Remove new backend
rm -rf backend/

# Reinstall and run Express
npm install
npm run dev
```

---

## Questions?

See **backend/README.md** for detailed backend documentation.

---

## Checklist

- [ ] Backend `.env` configured
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend `VITE_API_URL` set to `http://localhost:8000`
- [ ] Services started (Docker Compose or manual)
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] API docs work: `http://localhost:8000/docs`
- [ ] Frontend loads: `http://localhost:5173` or `http://localhost`
- [ ] Login works with Firebase
- [ ] Chat sends messages successfully
- [ ] Tasks can be created

You're done! 🎉
