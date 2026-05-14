# AgentCoolie

AgentCoolie is a personal AI agent application with authenticated chat, short-term Redis memory, long-term Supabase memory, task automation, Gmail tooling through n8n, web search, PDF/image/audio handling, WhatsApp access, and phone-call reminders for important tasks.

This repository contains the production frontend, backend API, SQL schema files, and deployment/startup configuration. 

## What AgentCoolie Does

- Chats with the user using recent conversation context and durable user memory.
- Saves important user facts and personalization settings.
- Routes requests to tools for Gmail, web search, YouTube, websites, PDF/image/audio analysis, and task creation.
- Stores tasks in Supabase and executes due server-side actions where possible.
- Uses Redis for chat-scoped short-term memory and pending multi-turn tool state.
- Uses Supabase for users, chat messages, tasks, notifications, preferences, credentials, long-term memory, and runtime secrets.
- Connects Gmail through Google OAuth and sends/reads mail through an n8n workflow.
- Connects WhatsApp through Twilio after phone ownership is verified with a LINK code.
- Places Twilio phone calls for important task reminders.

## Repository Structure

```text
.
|-- backend/                 FastAPI backend, agents, routes, services, SQL
|   |-- app/
|   |   |-- agents/          LLM-facing agent classes
|   |   |-- core/            config and environment loading
|   |   |-- models/          API schemas
|   |   |-- routes/          HTTP route modules
|   |   `-- services/        Supabase, Redis, Gmail/n8n, search, memory, tasks
|   `-- sql/                 Supabase schema and migration SQL
|-- client/                  React app source is under client/src
|-- shared/                  Shared TypeScript schema definitions
|-- package.json             Frontend build/dev scripts
|-- vite.config.ts           Vite config and local backend proxy
`-- firebase.json            Firebase Hosting config
```

## Architecture

```mermaid
flowchart LR
  U["User browser"] --> FE["React frontend on Firebase Hosting"]
  FE --> API["FastAPI backend on Railway"]
  API --> FB["Firebase Auth Admin SDK"]
  API --> SB["Supabase Postgres"]
  API --> RD["Redis Cloud"]
  API --> LLM["Gemini with fallback keys and Groq fallback"]
  API --> SERP["SerpAPI then DuckDuckGo/RSS fallback"]
  API --> TW["Twilio Voice and WhatsApp"]
  API --> N8N["n8n Gmail workflow"]
  N8N --> GMAIL["Gmail API"]
  N8N --> SB
```

## Chat And Tool Routing

```mermaid
sequenceDiagram
  participant User
  participant Frontend
  participant Backend
  participant Router as ChatWorkflowService
  participant Redis
  participant Supabase
  participant Tool
  participant LLM

  User->>Frontend: Send text, image, PDF, or audio
  Frontend->>Backend: POST /api/webhook/proxy with Firebase ID token
  Backend->>Backend: Extract attachment context
  Backend->>Router: process(user_id, message, attachment_context, conversation_id)
  Router->>Redis: Load short memory and pending states for this chat only
  Router->>Supabase: Load preferences and long-term memories
  Router->>Tool: Use Gmail/tasks/search when intent requires it
  Router->>LLM: General response with injected context
  Router->>Redis: Append latest exchange
  Router->>Supabase: Save chat and important long-term memory
  Backend->>Frontend: Assistant response and tool metadata
```

## Task Automation Flow

```mermaid
flowchart TD
  A["User creates task from chat or Tasks page"] --> B["Task row stored in Supabase"]
  B --> C{"Task due?"}
  C --> D["Backend scheduler polls due pending tasks"]
  C --> E["Frontend visible-tab runner polls due tasks"]
  D --> F{"Server-executable?"}
  F -->|Gmail| G["Call n8n Gmail workflow"]
  F -->|General reminder| H["Mark reminder completed"]
  F -->|Important call| I["Place Twilio call"]
  F -->|Browser-only YouTube/website| J["Leave pending for browser runner"]
  E --> K["Execute browser-visible tasks and open tabs"]
  G --> L["Update task status and execution message"]
  H --> L
  I --> L
  K --> L
```

## Memory Model

```mermaid
flowchart LR
  Chat["Current user message"] --> Short["Redis short-term memory: last N exchanges for this chat"]
  Chat --> Long["Long-term memory classifier"]
  Long --> Facts["Supabase long_term_memories"]
  Pref["Personalization page"] --> PrefDB["Supabase user_preferences"]
  Short --> Prompt["Final agent context"]
  Facts --> Prompt
  PrefDB --> Prompt
  Tasks["Pending tasks"] --> Prompt
```

Short-term memory is isolated by conversation id. Redis stores chat memory as `coolie:short-memory:{user_id}:{conversation_id}` and pending tool state as `coolie:tool-state:{user_id}:{conversation_id}:{tool}`. Deleting or clearing a chat removes that chat's Redis memory and pending state. Long-term memories, personalization settings, credentials, and tasks remain user-level because they should be available across all chats.

## External Services

| Service | Purpose |
| --- | --- |
| Firebase Auth | App authentication and Google sign-in |
| Firebase Hosting | Frontend deployment |
| Railway | Backend and n8n hosting |
| Supabase | Postgres database, runtime secrets, credentials, memory, tasks |
| Redis Cloud | Short-term memory and pending tool state |
| Gemini | Main LLM, image/PDF/audio support |
| Groq | Text fallback when Google generation fails |
| SerpAPI | Primary live web search |
| DuckDuckGo/RSS | Free web-search fallback |
| Twilio | Phone-call reminders and WhatsApp sandbox/business messaging |
| n8n | Gmail workflow tool execution |

## Required Backend Environment

Set these in Railway or local `.env`.

```env
ENV=production
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=https://agentcoolie.web.app
CORS_ORIGINS=["https://agentcoolie.web.app","http://localhost:5173"]

FIREBASE_PROJECT_ID=...
FIREBASE_SERVICE_ACCOUNT_JSON=...

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...

REDIS_URL=redis://default:...@host:port
REDIS_MEMORY_CONTEXT_EXCHANGES=5
REDIS_MEMORY_TTL_SECONDS=86400

GOOGLE_AI_API_KEY=...
GOOGLE_AI_API_FALLBACK_KEY=...
GROQ_API_KEY=...
GROQ_MODEL=llama-3.1-8b-instant
SERPAPI_API_KEY=...

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_OAUTH_REDIRECT_URI=https://agentcoolie-backend-production.up.railway.app/api/oauth/google/callback

TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_VALIDATE_WEBHOOK_SIGNATURE=true

N8N_BASE_URL=https://your-n8n-host
N8N_GMAIL_ACTION_PATH=/webhook/gmail-action
N8N_GMAIL_CREDENTIALS_PATH=/webhook/save-gmail-credentials
N8N_TOOL_SECRET=use-a-long-random-secret

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=agentcoolie-production
SESSION_SECRET_KEY=use-a-long-random-secret
```

## Required Frontend Environment

Set these in `.env` before building and deploying the frontend.

```env
VITE_API_URL=https://agentcoolie-backend-production.up.railway.app
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_APP_ID=...
```

## Supabase Setup

Run the SQL files in `backend/sql/` in this order:

1. `backend/sql/tasks_execution_status.sql`
2. `backend/sql/long_term_memories.sql`
3. `backend/sql/user_preferences.sql`
4. `backend/sql/user_credentials.sql`
5. `backend/sql/user_credentials_gmail_compat.sql`
6. `backend/sql/app_secrets.sql`

Important tables:

- `tasks`: scheduled work, status, execution messages, call metadata.
- `chat_messages`: persisted conversation messages.
- `long_term_memories`: durable facts and preferences extracted from chat.
- `user_preferences`: explicit personalization settings.
- `user_credentials`: per-user Gmail, call reminder, and WhatsApp connection data.
- `app_secrets`: runtime provider credentials so some changes do not require redeploy.

Do not expose the Supabase service role key to the frontend. Only the backend and private tooling should use it.

## Gmail And n8n Security

The backend sends Gmail actions to n8n with:

- `x-user-id`: the authenticated Firebase UID.
- `x-agentcoolie-secret`: the backend configured `N8N_TOOL_SECRET`.

The n8n workflow must validate `x-agentcoolie-secret` before it reads Supabase or calls Gmail. If this check is missing, the public webhook can be abused by anyone who knows the URL.

Recommended first n8n Code node:

```js
const expected = $env.N8N_TOOL_SECRET;
const got = $json.headers?.["x-agentcoolie-secret"];

if (!expected || got !== expected) {
  throw new Error("Unauthorized AgentCoolie tool request");
}

return $input.all();
```

Store `N8N_TOOL_SECRET` in both Railway backend variables and n8n environment variables. Rotate the secret if it has been shared.

## WhatsApp Linking

WhatsApp is mapped to a user only after proof from the actual phone number:

1. User saves the WhatsApp number in Settings.
2. Backend stores a pending credential and returns a six digit code.
3. User sends `LINK 123456` from that WhatsApp number to the Twilio sandbox.
4. Backend marks the credential verified.
5. Future WhatsApp messages from that number route to that user.

This prevents a logged-in user from silently binding someone else’s phone number.

## Task Statuses

| Status | Meaning |
| --- | --- |
| `pending` | Waiting for due time or browser execution |
| `calling` | Backend has claimed the task and is running an action |
| `sent` | Task action completed or reminder delivered |
| `failed` | Tool/provider failed; `execution_message` explains why |
| `missed_offline` | Browser-only task was due while the user device was closed/offline |

Gmail and general reminders can run server-side. YouTube and website tasks still require a browser tab, so the frontend runner opens them when the user is active.

## Local Development

Install dependencies:

```powershell
npm install
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run backend:

```powershell
.\backend\venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Run frontend:

```powershell
npm run dev
```

Open:

```text
http://localhost:5173
```

## Verification Commands

```powershell
python -m compileall backend\app
npm run build
```

Optional checks:

```powershell
rg -n "TODO|FIXME|except Exception|service_role|window.open" backend client shared
```

## Deployment

Backend on Railway:

```powershell
& "$env:APPDATA\npm\railway.cmd" up
& "$env:APPDATA\npm\railway.cmd" service restart --yes
```

Frontend on Firebase Hosting:

```powershell
npm run build
& "$env:APPDATA\npm\firebase.cmd" deploy --only hosting
```

After deployment:

1. Confirm `/health` returns healthy.
2. Confirm Firebase authorized domains include the production hosting domain.
3. Confirm backend `CORS_ORIGINS` includes the Firebase hosting domain.
4. Confirm Google OAuth redirect URI points to the backend callback URL.
5. Confirm Twilio WhatsApp inbound URL points to `/api/whatsapp/twilio-webhook`.
6. Confirm n8n has `N8N_TOOL_SECRET` and rejects requests without it.

## Operational Notes

- Rotate secrets that were pasted into chats, terminals, screenshots, or docs.
- Keep `.env` out of git. This repo ignores `.env`, `.env.local`, and environment-specific local files.
- Prefer adding provider credentials to `app_secrets` for runtime changes that should not require a redeploy.
- Browser popup behavior differs by browser. The frontend now treats a null `window.open` result as unknown instead of claiming the tab was blocked.
