# AgentCoolie

AgentCoolie is a personal AI agent workspace for chat, remembered context, live search, file understanding, scheduled tasks, Gmail automation, WhatsApp access, and important phone-call reminders.

This repository contains the production frontend, backend API, SQL schema files, and deployment/startup configuration. It is built as a real user application: Firebase handles authentication, the React app runs on Firebase Hosting, the FastAPI backend runs on Railway, Supabase stores durable data, Redis stores short chat memory, n8n runs the Gmail workflow, and Twilio powers WhatsApp and voice reminders.

## What Users Can Do

- Chat naturally with an assistant that remembers recent chat context and durable user facts.
- Ask for current information through SerpAPI first, then DuckDuckGo/RSS fallback.
- Upload images, PDFs, and audio clips for analysis or transcription.
- Create reminders and action tasks from chat or the Tasks page.
- Schedule Gmail tasks, website tasks, YouTube tasks, and normal reminders.
- Connect Gmail in Settings and let the agent send or inspect mail through an n8n workflow.
- Connect WhatsApp so messages from the verified phone number route to the right account.
- Mark important tasks for phone-call reminders.
- Personalize tone, response length, formality, and emoji usage.

## Feature Catalog

### Chat And Routing

- Main entry point: `POST /api/webhook/proxy`.
- The frontend can send plain text, JSON, multipart files, image attachments, PDF attachments, and audio recordings.
- `backend/app/services/chat_workflow_service.py` acts as the main router. It decides whether the message should become a general LLM answer, web search, task creation, Gmail workflow, YouTube open, website open, image/PDF/audio analysis, or pending multi-turn tool flow.
- Every request is scoped by Firebase UID. The backend derives the user from the Firebase token; clients are not trusted to provide their own `user_id`.
- Chat messages are stored in Supabase `chat_messages`, and recent chat context is stored in Redis per user and per conversation.

### Memory And Personalization

- Short-term memory: Redis, scoped by `user_id` and `conversation_id`.
- Long-term memory: Supabase `long_term_memories`, selected only when the message looks important enough.
- Personalization: Supabase `user_preferences`, controlled by the Personalization page and injected into the agent prompt.
- Tasks and credentials are also available as durable user-level context where relevant.
- Short-term memory is intentionally chat-specific. Long-term memory is intentionally user-wide.
- Deleting a chat also deletes that chat's Redis short memory and pending tool state.

### Web Search

- Web search uses SerpAPI/Google first when `SERPAPI_API_KEY` is configured.
- If SerpAPI fails or is missing, the backend falls back to DuckDuckGo HTML, DuckDuckGo Lite, Google News RSS, Bing News RSS, and DuckDuckGo Instant Answer where applicable.
- News/current-affairs queries are detected by terms such as `latest`, `current`, `today`, `recent`, `news`, and `politics`.
- Search results are injected as external evidence, not as trusted instructions.

### Uploads And File Understanding

- Image uploads are analyzed with Gemini vision keys from `GEMINI_VISION_API_KEYS` or fallback vision settings.
- PDF uploads are parsed with `pypdf`; page and size limits come from the active plan.
- Audio uploads are transcribed first, then the transcript is routed like a normal user message.
- Attachment text is wrapped as untrusted external context before reaching the LLM. This protects the agent from instructions hidden inside PDFs, images, transcripts, or web snippets.

### Gmail Automation

- Gmail OAuth starts at `GET /api/oauth/google/start` and returns through `GET /api/oauth/google/callback`.
- Credentials are saved per Firebase user in Supabase `user_credentials`.
- Gmail execution is delegated to n8n through `N8N_BASE_URL` and the Gmail workflow path.
- Backend calls to n8n include `x-user-id` and, in production, should include `x-agentcoolie-secret`.
- Gmail actions are planned deterministically for common list/search/send flows before n8n is called.
- High-risk Gmail actions such as send, reply, delete, label changes, and read/unread changes require confirmation before execution.
- The confirmation draft is stored in Redis as chat-scoped pending tool state, so a confirmation in one chat does not apply to another chat.

### Tasks And Reminders

- Users can create tasks from chat, WhatsApp, or the Tasks page.
- Supported task categories include normal reminders, Gmail tasks, YouTube opens, website opens, and call-reminder tasks.
- Supabase `tasks` stores task status, due date, execution message, priority, metadata, and completion state.
- Backend-executable tasks are claimed by the FastAPI scheduler with execution metadata before side effects run.
- Browser-only actions are left for the frontend runner because the backend cannot open a user's browser tab.
- If a browser-only task is due while the app is closed, the frontend can mark it `missed_offline`.

### WhatsApp Access

- WhatsApp access is account-linked by phone number.
- Users save a number in Settings, then verify it by sending `LINK 123456` from the same WhatsApp number.
- Incoming Twilio WhatsApp messages are mapped to the verified Firebase user through Supabase `user_credentials`.
- Free/Companion users cannot use WhatsApp because the quota is zero; Autopilot users get the configured monthly allowance.

### Phone Call Reminders

- Important tasks can request `notify_by_call`.
- Twilio places a task-specific voice call using a Tenglish reminder message.
- Trial-account Twilio errors such as unverified recipient numbers are converted into user-friendly task errors.
- Call reminder phone numbers are stored per user in Supabase `user_credentials`.

### Plans, Quotas, And Demo Billing

- Companion and Autopilot limits are enforced on the backend in `plan_service.py`.
- Frontend checks are for UX only; the backend is the source of truth.
- Usage is recorded in Supabase `usage_events`.
- Demo checkout can activate Autopilot without real payment only when `DEMO_BILLING_ENABLED=true`.
- Real payment is not implemented yet. Replace demo billing with Stripe, Razorpay, or another provider before charging users.

### Safety, Guardrails, And Auditability

- External content from search, PDFs, images, audio transcripts, and uploaded files is wrapped as untrusted context.
- The system prompt tells the LLM not to follow instructions inside external content blocks.
- High-risk Gmail actions require explicit user confirmation.
- Server-side task execution uses leases so stuck `calling` tasks can be recovered.
- Redacted tool audit events are written to `usage_events` with `feature = "tool_audit"` for Gmail, n8n, Twilio calls, and stale task recovery.
- Audit metadata redacts secrets and shrinks long message bodies into previews plus short hashes, so debugging is possible without storing full sensitive payloads in logs.

## Plans And Pricing

AgentCoolie has two product modes:

| Capability | AgentCoolie Companion | AgentCoolie Autopilot |
| --- | ---: | ---: |
| Price | Free | Rs. 499/month or $6/month |
| AI chat messages | 15/day, 150/month | 60/day, 1,000/month |
| Active chats | 5 | 30 |
| Chat history retention | 7 days | 90 days |
| Short-term memory | Last 4 turns/chat | Last 15 turns/chat |
| Long-term memories | 15 total | 200 total |
| New long-term memories | 3/month | 50/month |
| Web searches | 3/day, 25/month | 20/day, 250/month |
| Active tasks/reminders | 5 | 75 |
| Task creation | 3/day, 25/month | 30/day, 300/month |
| Automated task executions | 1/day, 10/month | 15/day, 200/month |
| Critical call tasks | 1 active | 10 active |
| Gmail draft generation | Not included | 100/month |
| Gmail send/reply | Not included | 50/month |
| Gmail search/read | Not included | 100/month |
| WhatsApp messages | Not included | 250/month |
| Call reminders | 1/month | 10/month |
| Max call message | 10 seconds target | 25 seconds target |
| Image uploads | 1/day, 10/month, 3 MB | 15/day, 200/month, 10 MB |
| PDF uploads | 1/day, 5/month, 3 MB, 2 pages | 5/day, 75/month, 15 MB, 25 pages |
| Audio uploads | 1/day, 10/month, 30 seconds, 3 MB | 10/day, 100/month, 5 minutes, 25 MB |
| YouTube open actions | 5/day, 50/month | 50/day, 500/month |
| Website open actions | 5/day, 50/month | 50/day, 500/month |
| Tool retries | 0 | 2 |

Plan enforcement lives on the backend in `backend/app/services/plan_service.py`. The frontend displays the current mode, but it is not trusted for paid-feature enforcement.
Checkout is currently a demo flow, not a real payment provider. The landing page links to `/checkout`; clicking **Pay and Activate Autopilot** calls `POST /api/billing/demo-upgrade`, writes `autopilot` to Supabase `user_plans`, and shows a success screen when `DEMO_BILLING_ENABLED=true`. Keep that flag off in real production and replace the endpoint with Stripe/Razorpay before collecting real money.

## Repository Layout

```text
.
|-- backend/
|   |-- app/
|   |   |-- agents/          Agent classes and LLM-facing behavior
|   |   |-- core/            Settings and environment loading
|   |   |-- models/          Pydantic API schemas
|   |   |-- routes/          FastAPI routers
|   |   `-- services/        Supabase, Redis, Gmail, search, tasks, Twilio
|   |-- sql/                 Supabase schema and migration SQL
|   |-- Dockerfile
|   `-- requirements.txt
|-- client/
|   |-- public/              Static frontend assets
|   `-- src/                 React application
|-- shared/                  Shared TypeScript types
|-- call-reminder-test/      Standalone Twilio voice test harness
|-- firebase.json            Firebase Hosting config
|-- package.json             Frontend scripts
|-- vite.config.ts           Vite dev server and API proxy
`-- README.md
```

## Architecture

```mermaid
flowchart LR
  User["User browser"] --> Frontend["React app / Firebase Hosting"]
  Frontend --> Backend["FastAPI API / Railway"]

  Backend --> Firebase["Firebase Auth Admin SDK"]
  Backend --> Supabase["Supabase Postgres"]
  Backend --> Redis["Redis Cloud"]
  Backend --> LLM["Gemini primary / Groq fallback"]
  Backend --> Search["SerpAPI / DuckDuckGo / RSS"]
  Backend --> Twilio["Twilio Voice and WhatsApp"]
  Backend --> N8N["n8n Gmail workflow"]
  Backend --> Audit["Redacted tool audit events"]
  N8N --> Gmail["Gmail API"]
  N8N --> Supabase
  Audit --> Supabase
```

## Request Flow

```mermaid
sequenceDiagram
  participant U as User
  participant F as Frontend
  participant B as FastAPI
  participant R as Router
  participant M as Redis
  participant DB as Supabase
  participant T as Tool
  participant L as LLM

  U->>F: Send text, file, image, PDF, or audio
  F->>B: POST /api/webhook/proxy with Firebase token
  B->>B: Validate auth and extract attachment context
  B->>R: chat_workflow_service.process(...)
  R->>M: Load chat-scoped short memory and pending tool state
  R->>DB: Load preferences and long-term memories
  R->>T: Run Gmail, task, search, website, or YouTube tool when needed
  R->>DB: Write redacted tool audit events for side effects
  R->>L: Ask LLM for general responses
  R->>M: Save latest exchange for this chat only
  R->>DB: Persist chat and important long-term memory
  B->>F: Return assistant response and tool metadata
```

## Task Automation

AgentCoolie currently does not use Celery. Background work is handled by two lightweight runners:

- Backend runner: `backend/app/services/call_task_scheduler.py` starts from FastAPI startup as an in-process `asyncio` polling loop. It polls Supabase for due `pending` tasks, atomically claims server-executable work by changing status to `calling`, then runs Gmail tasks and Twilio call reminders.
- Frontend runner: `client/src/components/ScheduledTaskRunner.tsx` runs while the user has the app open. It handles plain reminders and browser-only work such as opening YouTube videos or websites, because the backend cannot open tabs or local notifications on the user's device.

```mermaid
flowchart TD
  A["Task created from chat or Tasks page"] --> B["Row saved in Supabase tasks"]
  B --> C{"Due time reached"}
  C --> D["Backend asyncio scheduler"]
  C --> E["Frontend visible-tab runner"]
  D --> F{"Server executable"}
  F -->|Gmail| G["Call n8n Gmail workflow"]
  F -->|Call requested| I["Place Twilio voice call"]
  F -->|Plain reminder or browser-only task| J["Leave pending for browser runner"]
  J --> E
  E --> K["Notify, open browser tab, or mark missed_offline"]
  G --> L["Update task status and execution message"]
  I --> L
  K --> L
```

This setup is simple and works for a small Railway deployment. If the app grows to many replicas or needs guaranteed delayed jobs, move this runner to Celery, RQ, Dramatiq, or a managed queue. Both execution paths reduce duplicate execution by claiming tasks with `status = pending` before running side effects.

Task execution reliability details:

- Backend/manual executions write `metadata.execution_scope`, `execution_attempt`, `execution_claimed_at`, and `execution_lease_seconds`.
- `TASK_EXECUTION_LEASE_SECONDS` controls how long a backend/manual `calling` task can stay claimed before recovery.
- Stale backend/manual `calling` tasks are marked `failed` instead of retried automatically. This avoids duplicate side effects such as sending the same email or placing the same call twice.
- Browser actions use `execution_scope = browser_action_required`, so stale recovery does not incorrectly fail YouTube or website tasks that are waiting for the frontend.
- Completed and failed backend executions keep execution metadata for debugging.

## Memory Model

```mermaid
flowchart LR
  Msg["User message"] --> Short["Redis short memory per chat"]
  Msg --> Classifier["Long-term memory classifier"]
  Classifier --> Facts["Supabase long_term_memories"]
  PrefUI["Personalization page"] --> Prefs["Supabase user_preferences"]
  Tasks["Tasks table"] --> Prompt["Agent context"]
  Short --> Prompt
  Facts --> Prompt
  Prefs --> Prompt
```

Short-term memory is isolated by conversation id:

```text
coolie:short-memory:{user_id}:{conversation_id}
coolie:tool-state:{user_id}:{conversation_id}:{tool}
```

Deleting or clearing a chat deletes that chat's Redis memory and pending tool state. Long-term memory, preferences, credentials, and tasks are user-level because they should apply across chats.

## Data Stores

| Store | Used For |
| --- | --- |
| Supabase `tasks` | Scheduled work, status, execution messages, call metadata |
| Supabase `chat_messages` | Durable chat history |
| Supabase `long_term_memories` | Important facts selected from chat |
| Supabase `user_preferences` | Explicit personalization settings |
| Supabase `user_credentials` | Gmail, WhatsApp, and call reminder connection data |
| Supabase `app_secrets` | Runtime provider credentials that can change without redeploy |
| Supabase `user_plans` | Companion/Autopilot account mode and billing metadata |
| Supabase `usage_events` | Daily/monthly feature usage accounting and redacted `tool_audit` events |
| Redis | Last N exchanges per chat and pending multi-turn tool state |

## External Services

| Service | Purpose |
| --- | --- |
| Firebase Auth | Email/password and Google sign-in |
| Firebase Hosting | Frontend deployment |
| Railway | Backend and n8n deployment |
| Supabase | Postgres data and runtime secrets |
| Redis Cloud | Short-term memory |
| Gemini | Main text, image, PDF, and audio intelligence |
| Groq | Text fallback when Google generation fails |
| SerpAPI | Primary live web search |
| DuckDuckGo/RSS | Free search fallback |
| Twilio | WhatsApp and voice calls |
| n8n | Gmail workflow execution |

## Backend Environment

Set these in Railway variables or local `.env`.

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
REDIS_MEMORY_MAX_MESSAGES=30
REDIS_MEMORY_TTL_SECONDS=86400

GOOGLE_AI_API_KEY=...
GOOGLE_AI_API_FALLBACK_KEY=...
GOOGLE_AI_API_KEYS=["...","..."]
GEMINI_VISION_API_KEYS=["...","..."]
GROQ_API_KEY=...
GROQ_API_KEYS=["...","..."]
GROQ_MODEL=llama-3.1-8b-instant
SERPAPI_API_KEY=...

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_OAUTH_REDIRECT_URI=https://your-backend.up.railway.app/api/oauth/google/callback

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
OAUTH_STATE_MAX_AGE_SECONDS=600
DEMO_BILLING_ENABLED=false
MAX_ATTACHMENT_COUNT=4
MAX_UPLOAD_BYTES=26214400
TASK_EXECUTION_LEASE_SECONDS=300
```

`SESSION_SECRET_KEY` must be a strong stable value in production. Gmail OAuth state is signed with this secret and expires after `OAUTH_STATE_MAX_AGE_SECONDS`.

Runtime key rotation can be managed without redeploy by writing JSON arrays to `app_secrets`, for example `GOOGLE_AI_API_KEYS`, `GEMINI_VISION_API_KEYS`, and `GROQ_API_KEYS`. Gemini vision/audio requests use the vision pool first because Groq is text-only in this app.
Set `DEMO_BILLING_ENABLED=true` only for demo deployments where the fake checkout should activate Autopilot without real payment.

## Frontend Environment

Set these before building the React app.

```env
VITE_API_URL=https://your-backend.up.railway.app
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_APP_ID=...
```

## Supabase Setup

Run SQL files in `backend/sql/`:

1. `core_app_tables.sql`
2. `tasks_execution_status.sql`
3. `long_term_memories.sql`
4. `user_preferences.sql`
5. `user_credentials.sql`
6. `user_credentials_gmail_compat.sql`
7. `app_secrets.sql`
8. `chat_messages_conversation_id.sql`
9. `plans_and_usage.sql`

The backend uses the Supabase service role key, so route-level ownership checks are mandatory. User-facing task, preference, credential, and memory routes scope every read/write by Firebase UID.
`plans_and_usage.sql` also installs the `consume_usage_quota` RPC, which checks limits and inserts usage inside one Postgres transaction. Re-run it after pulling billing changes.
Tool audit events do not require a separate migration; they are stored in `usage_events` with `feature = 'tool_audit'`.

Never expose the service role key in frontend code.

## Gmail And n8n

The browser starts OAuth through:

```text
GET /api/oauth/google/start
GET /api/oauth/google/callback
```

The backend stores Gmail OAuth credentials in Supabase `user_credentials`. Gmail actions are sent to n8n with:

```text
x-user-id: <firebase uid>
x-agentcoolie-secret: <N8N_TOOL_SECRET>
```

Your n8n workflow should reject requests where `x-agentcoolie-secret` does not match its own environment variable.

Gmail safety behavior:

- List/search actions can run directly when Gmail is connected and the plan allows Gmail reads.
- Send/reply/delete/label actions are considered high-risk and require a confirmation turn.
- The agent shows the drafted recipient, subject, and body, then waits for `send` or `confirm`.
- `cancel` deletes the pending Redis state and does not call n8n.
- Every started/completed Gmail workflow writes a redacted `tool_audit` event.

## WhatsApp Linking

WhatsApp is account-specific:

1. User saves a phone number in Settings.
2. Backend stores a pending WhatsApp credential with a six digit code.
3. User sends `LINK 123456` from that same WhatsApp number to the Twilio sandbox or WhatsApp sender.
4. Backend marks that number verified.
5. Future WhatsApp messages from that number route to that Firebase user.

Set the Twilio WhatsApp inbound URL to:

```text
https://your-backend.up.railway.app/api/whatsapp/twilio-webhook
```

The status callback URL is optional unless you want delivery analytics.

## Task Statuses

| Status | Meaning |
| --- | --- |
| `pending` | Waiting for due time or browser execution |
| `calling` | Backend claimed the task and is running a server-side action |
| `sent` | Action completed or reminder delivered |
| `failed` | Tool/provider failed; see `execution_message` |
| `missed_offline` | Browser-only task was due while the user device was closed/offline |

## Tool Audit Events

Tool audit events are stored in `usage_events` so they can be inspected without adding a new table.

| Metadata Field | Meaning |
| --- | --- |
| `tool` | Tool family, for example `gmail`, `call_reminder`, or `task_scheduler` |
| `action` | Action name, for example `send`, `place_call`, or task type |
| `stage` | Lifecycle stage such as `confirmation_requested`, `started`, `completed`, or `stale_lease_recovered` |
| `status` | Human-readable state such as `pending`, `success`, `failed`, `cancelled`, or `confirmed` |
| `metadata` | Sanitized payload preview, provider status, task id, conversation id, or failure reason |

The audit service is best-effort. If Supabase is temporarily unreachable, the action is not blocked only because the audit write failed.

Useful SQL:

```sql
select occurred_at, metadata
from public.usage_events
where user_id = 'firebase_uid_here'
  and feature = 'tool_audit'
order by occurred_at desc
limit 50;
```

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

After deployment, check:

1. `/health` returns `healthy` and includes dependency `checks`; `degraded` means auth or Supabase configuration needs attention.
2. Firebase authorized domains include the deployed hosting domain.
3. Backend `CORS_ORIGINS` includes the deployed frontend URL.
4. Google OAuth redirect URI matches the backend callback URL exactly.
5. Twilio WhatsApp inbound URL points to `/api/whatsapp/twilio-webhook`.
6. n8n has `N8N_TOOL_SECRET` and rejects requests without it.
7. Supabase SQL migrations have been applied.

## Verification

```powershell
python -m compileall backend\app
python backend\test_imports.py
npm run build
```

Useful inspection commands:

```powershell
rg -n "TODO|FIXME|except Exception|service_role|window.open" backend client shared
rg -n "api/gmail/oauth|unauthorized-domain|CORS" backend client README.md
```

## Operational Notes

- Rotate secrets that were pasted into chats, terminals, screenshots, or docs.
- Keep `.env`, `.env.local`, and service-account JSON files out of git. This repo ignores `.env`, `.env.local`, and environment-specific local files.
- Prefer adding provider credentials to `app_secrets` for runtime changes that should not require a redeploy.
- Browser popup behavior differs by browser. The frontend now treats a null `window.open` result as unknown instead of claiming the tab was blocked.
- Browser-only actions require the user device to be online and the app to be open.
- Server-side tasks are handled by the FastAPI in-process scheduler today, not Celery.
- If you add multiple backend replicas, keep atomic task claiming or move background work to a real queue.
