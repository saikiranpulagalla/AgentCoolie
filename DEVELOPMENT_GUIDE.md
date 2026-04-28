# CoolieAssistant - Development Guide

This guide covers development setup, architecture, and best practices for contributing to CoolieAssistant.

---

## 📚 Table of Contents

1. [Development Setup](#development-setup)
2. [Project Architecture](#project-architecture)
3. [Code Organization](#code-organization)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Common Tasks](#common-tasks)
7. [Debugging](#debugging)
8. [Performance Tips](#performance-tips)

---

## Development Setup

### Prerequisites

- Node.js 18+
- Python 3.10+
- Git
- Your favorite code editor (VS Code recommended)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/CoolieAssistant.git
cd CoolieAssistant

# Copy environment file
cp .env.example .env

# Edit .env with your development credentials
# (See README.md for detailed environment setup)
```

### Backend Development

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

# Run with auto-reload
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd client

# Install dependencies
npm install

# Run development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Project Architecture

### Backend Architecture

```
FastAPI Application
├── Routes (API Endpoints)
│   ├── /api/auth - Authentication
│   ├── /api/chat - Chat messages
│   ├── /api/tasks - Task management
│   ├── /api/whatsapp - WhatsApp integration
│   ├── /api/gmail - Gmail integration
│   └── ... (other routes)
├── Services (Business Logic)
│   ├── FirebaseService - Authentication
│   ├── SupabaseService - Database
│   ├── AIService - AI/Embeddings
│   └── ... (other services)
├── Agents (LangChain)
│   ├── ChatAgent - Conversations
│   ├── WhatsappAgent - WhatsApp
│   ├── GmailAgent - Email
│   └── TaskAgent - Task creation
└── Models (Data Validation)
    └── Pydantic schemas
```

### Frontend Architecture

```
React Application
├── Pages (Route Components)
│   ├── Home - Dashboard
│   ├── Login - Authentication
│   ├── Chat - Chat interface
│   ├── Tasks - Task management
│   └── ... (other pages)
├── Components (Reusable UI)
│   ├── ChatBubble - Message display
│   ├── ChatInput - Message input
│   ├── TaskCard - Task display
│   └── ... (other components)
├── Contexts (State Management)
│   ├── AuthContext - Auth state
│   ├── ChatContext - Chat state
│   ├── NotificationContext - Notifications
│   └── ThemeProvider - Theme state
├── Hooks (Custom Logic)
│   ├── use-mobile - Mobile detection
│   ├── use-toast - Toast notifications
│   └── use-microphone - Microphone access
└── Lib (Utilities)
    ├── api.ts - API client
    ├── firebase.ts - Firebase setup
    └── queryClient.ts - React Query setup
```

### Data Flow

```
User Input
    ↓
Frontend Component
    ↓
API Call (lib/api.ts)
    ↓
Backend Route Handler
    ↓
Service Layer (Business Logic)
    ↓
LangChain Agent (AI Processing)
    ↓
External APIs (Firebase, Supabase, AI Models)
    ↓
Response to Frontend
    ↓
Update UI State
    ↓
Re-render Component
```

---

## Code Organization

### Backend Structure

```
backend/app/
├── main.py                 # FastAPI app setup
├── core/
│   └── config.py          # Settings & environment
├── models/
│   └── schemas.py         # Pydantic models
├── routes/
│   ├── auth.py            # Authentication endpoints
│   ├── chat.py            # Chat endpoints
│   ├── tasks.py           # Task endpoints
│   ├── whatsapp.py        # WhatsApp endpoints
│   ├── gmail.py           # Gmail endpoints
│   └── ...
├── services/
│   ├── firebase_service.py    # Firebase operations
│   ├── supabase_service.py    # Database operations
│   ├── ai_service.py          # AI operations
│   └── ...
└── agents/
    └── base_agents.py     # LangChain agents
```

### Frontend Structure

```
client/src/
├── pages/                 # Route components
│   ├── Home.tsx
│   ├── Login.tsx
│   ├── Chat.tsx
│   └── ...
├── components/            # Reusable components
│   ├── ChatBubble.tsx
│   ├── ChatInput.tsx
│   ├── TaskCard.tsx
│   └── ui/               # shadcn/ui components
├── contexts/             # React contexts
│   ├── AuthContext.tsx
│   ├── ChatContext.tsx
│   └── ...
├── hooks/                # Custom hooks
│   ├── use-mobile.tsx
│   ├── use-toast.ts
│   └── ...
├── lib/                  # Utilities
│   ├── api.ts           # API client
│   ├── firebase.ts      # Firebase setup
│   └── ...
├── App.tsx              # Root component
└── main.tsx             # Entry point
```

---

## Development Workflow

### Creating a New Feature

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Backend changes:**
   - Add route in `backend/app/routes/`
   - Add service logic in `backend/app/services/`
   - Add Pydantic model in `backend/app/models/schemas.py`
   - Test with http://localhost:8000/docs

3. **Frontend changes:**
   - Create component in `client/src/components/`
   - Add page in `client/src/pages/` if needed
   - Update context if state management needed
   - Test in browser

4. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style

**Backend (Python):**
- Follow PEP 8
- Use type hints
- Use meaningful variable names
- Add docstrings to functions

**Frontend (TypeScript):**
- Use TypeScript for type safety
- Follow React best practices
- Use meaningful component names
- Add JSDoc comments for complex logic

---

## Testing

### Backend Testing

```bash
cd backend

# Run tests (when test suite is added)
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_auth.py
```

### Frontend Testing

```bash
cd client

# Run tests (when test suite is added)
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### Manual Testing

1. **Backend API:**
   - Open http://localhost:8000/docs
   - Test endpoints with Swagger UI
   - Check responses and error handling

2. **Frontend:**
   - Open http://localhost:5173
   - Test user flows
   - Check browser console for errors
   - Test on mobile (DevTools)

---

## Common Tasks

### Adding a New API Endpoint

1. **Create route handler:**
   ```python
   # backend/app/routes/your_route.py
   from fastapi import APIRouter, Depends
   from app.core.config import settings
   
   router = APIRouter(prefix="/api/your-endpoint", tags=["your-endpoint"])
   
   @router.get("/")
   async def get_data():
       """Get data endpoint."""
       return {"data": "value"}
   ```

2. **Register route in main.py:**
   ```python
   from app.routes import your_router
   app.include_router(your_router)
   ```

3. **Test in Swagger UI:**
   - Open http://localhost:8000/docs
   - Find your endpoint
   - Click "Try it out"

### Adding a New Frontend Component

1. **Create component:**
   ```typescript
   // client/src/components/YourComponent.tsx
   import React from 'react';
   
   interface YourComponentProps {
     title: string;
   }
   
   export const YourComponent: React.FC<YourComponentProps> = ({ title }) => {
     return <div>{title}</div>;
   };
   ```

2. **Use in page:**
   ```typescript
   import { YourComponent } from '@/components/YourComponent';
   
   export default function YourPage() {
     return <YourComponent title="Hello" />;
   }
   ```

### Adding a New Database Table

1. **Create SQL migration:**
   ```sql
   CREATE TABLE your_table (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id),
     data TEXT,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. **Run in Supabase SQL Editor:**
   - Go to Supabase Dashboard
   - Open SQL Editor
   - Paste and run SQL

3. **Update service:**
   ```python
   # backend/app/services/supabase_service.py
   async def create_your_data(self, user_id: str, data: str):
       return await self.client.table("your_table").insert({
           "user_id": user_id,
           "data": data
       }).execute()
   ```

---

## Debugging

### Backend Debugging

**Using print statements:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Debug info: {variable}")
```

**Using debugger:**
```python
import pdb; pdb.set_trace()  # Breakpoint
```

**Check logs:**
```bash
# Backend terminal shows all logs
# Look for ERROR, WARNING, INFO messages
```

### Frontend Debugging

**Browser DevTools (F12):**
- Console tab - JavaScript errors
- Network tab - API calls
- Application tab - Local storage, cookies
- React DevTools extension - Component state

**Using console.log:**
```typescript
console.log('Debug:', variable);
console.error('Error:', error);
```

**Using debugger:**
```typescript
debugger;  // Breakpoint in DevTools
```

---

## Performance Tips

### Backend Performance

1. **Use async/await:**
   ```python
   async def get_data():
       # Non-blocking operations
       result = await some_async_operation()
       return result
   ```

2. **Add database indexes:**
   ```sql
   CREATE INDEX idx_user_id ON your_table(user_id);
   ```

3. **Cache responses:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_operation(param):
       return result
   ```

### Frontend Performance

1. **Use React.memo for expensive components:**
   ```typescript
   export const YourComponent = React.memo(({ prop }) => {
     return <div>{prop}</div>;
   });
   ```

2. **Use useCallback for event handlers:**
   ```typescript
   const handleClick = useCallback(() => {
     // Handle click
   }, [dependencies]);
   ```

3. **Lazy load components:**
   ```typescript
   const YourComponent = lazy(() => import('./YourComponent'));
   ```

4. **Use React Query for data fetching:**
   ```typescript
   const { data, isLoading } = useQuery({
     queryKey: ['data'],
     queryFn: () => api.getData()
   });
   ```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Supabase Documentation](https://supabase.com/docs)
- [Firebase Documentation](https://firebase.google.com/docs)
- [LangChain Documentation](https://python.langchain.com/)

---

## Getting Help

- Check existing issues on GitHub
- Read documentation files
- Check browser console for errors
- Check backend logs
- Ask in discussions or create an issue

---

**Happy coding! 🚀**
