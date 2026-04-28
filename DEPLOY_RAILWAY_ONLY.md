# Deployment Guide: Both on Railway

Alternative approach: Deploy both frontend and backend to Railway for simplicity.

---

## Architecture

```
User Browser
    ↓
Railway (Frontend - Static Site)
    ↓ API calls
Railway (Backend - Web Service + PostgreSQL)
    ↓
External APIs (Firebase, Supabase, AI models)
```

---

## Pros & Cons

### ✅ Advantages
- Single platform to manage
- Easier networking (same infrastructure)
- Unified billing
- Simple environment management

### ⚠️ Trade-offs vs Firebase Hosting
- No global CDN (Firebase = faster)
- Slightly higher cost (~$6-10/month vs free)
- Frontend on same server pool as backend
- Not optimized for static assets

---

## Prerequisites

- Railway account: [railway.app](https://railway.app)
- GitHub account (for auto-deployment)
- Project pushed to GitHub

---

## Deployment Steps

### Step 1: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app)
2. Create project → Deploy from GitHub repo
3. Select your GitHub repo
4. Authorize Railway to access repo

### Step 2: Configure Backend Service

Railway auto-detects Python from `backend/`:

1. **Environment Variables** tab:
```
ENV=production
HOST=0.0.0.0
PORT=8000

# Firebase
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-role-key

# AI
GOOGLE_AI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-...

# Session
SESSION_SECRET_KEY=change-this
```

2. **Deployment settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Root Directory: `backend/`

3. **Wait for deployment** → Get backend URL

### Step 3: Configure Frontend Service

Create `railway.json` in project root:

```json
{
  "services": {
    "backend": {
      "rootDirectory": "backend",
      "buildCommand": "pip install -r requirements.txt",
      "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port 8000"
    },
    "frontend": {
      "rootDirectory": "client",
      "buildCommand": "npm install && npm run build",
      "startCommand": "npx serve -s dist -l 3000",
      "environmentVariables": {
        "VITE_API_URL": "$BACKEND_URL/api",
        "VITE_FIREBASE_API_KEY": "$FIREBASE_API_KEY",
        "VITE_FIREBASE_PROJECT_ID": "$FIREBASE_PROJECT_ID",
        "VITE_FIREBASE_APP_ID": "$FIREBASE_APP_ID"
      }
    }
  }
}
```

OR manually in Railway dashboard:

1. **Add second service** → Docker → Pull from GitHub
2. **Environment Variables**:
```
VITE_API_URL=https://your-backend.railway.app
VITE_FIREBASE_API_KEY=xxx
VITE_FIREBASE_PROJECT_ID=xxx
VITE_FIREBASE_APP_ID=xxx
```

3. **Deployment**:
   - Root: `client/`
   - Build: `npm install && npm run build`
   - Start: `npx serve -s dist -l 3000`

### Step 4: Link Services Together

In Railway dashboard:

1. Backend service → Variables
2. Add: `FRONTEND_URL=https://your-frontend.railway.app`
3. Update `CORS_ORIGINS` in backend config

### Step 5: Deploy

Push to GitHub - Railway auto-deploys:

```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

Both services build and deploy automatically.

---

## Dockerfile for Frontend (if needed)

Create `client/Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Runtime stage
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

Then Railway will auto-detect and use it.

---

## URL Structure

After deployment:

```
Frontend: https://your-project-frontend.railway.app
Backend:  https://your-project-backend.railway.app

OR

Frontend: https://your-project.railway.app
Backend:  https://your-project-api.railway.app
```

Check Railways dashboard for exact URLs.

---

## Environment Variables Setup

Create `.env.production` in `client/`:

```bash
VITE_API_URL=https://your-backend.railway.app
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_PROJECT_ID=your-project
VITE_FIREBASE_APP_ID=...
```

This gets picked up during `npm run build`.

---

## Updating Code

Both services auto-deploy on git push:

```bash
# Make changes
git add .
git commit -m "Update code"
git push origin main

# Railway automatically:
# 1. Builds backend Docker image
# 2. Builds frontend React app
# 3. Deploys both services
# 4. Runs health checks

# Status: Check Railway dashboard
```

---

## Monitoring

### Railway Logs

```bash
# Backend logs
railway logs --service backend -f

# Frontend logs
railway logs --service frontend -f

# Or in dashboard: Logs tab
```

### Health Checks

```bash
# Backend
curl https://your-backend.railway.app/health

# Frontend (should return HTML)
curl https://your-frontend.railway.app
```

---

## Database (Optional PostgreSQL)

Railway can add PostgreSQL for free tier:

1. Railway Dashboard → New
2. Select PostgreSQL
3. It integrates with projects

But Supabase is better for this project (already set up).

---

## Scaling

### Horizontal Scaling
```bash
# In Railway dashboard
# Increase replicas for either service
# Pay per replica (~$6 each)
```

### Environment Optimization
- Node.js: Use `node:18-alpine` (smaller)
- Python: Use `python:3.11-slim` (smaller)
- Static assets: Serve from Railway or add CDN

---

## Cost Comparison

| Component | Firebase+Railway | Both on Railway |
|-----------|-----------------|-----------------|
| Frontend Hosting | Free (CDN) | $6-10/mo |
| Backend | $6-10/mo | $6-10/mo |
| Database | Supabase free | Supabase free |
| **Total** | **$6-10/mo** | **$12-20/mo** |

**Recommendation**: Use Firebase Hosting for frontend (saves ~$6/month, faster)

---

## Troubleshooting

### Frontend build fails
```bash
# Check Node version
node --version  # Should be 18+

# Check build locally
npm run build

# Check Railway build logs
# Railway Dashboard → Logs tab
```

### Backend can't reach Supabase
```bash
# Check SUPABASE_URL environment variable
# Must be exact match from Supabase dashboard

# Test connection
curl "https://your-project.supabase.co/rest/v1/"
```

### CORS errors
```python
# backend/app/core/config.py
CORS_ORIGINS = [
    "https://your-frontend.railway.app",
    "https://your-project-frontend.railway.app",
]
```

---

## Switching to Firebase Hosting Later

If you want to move frontend to Firebase Hosting:

```bash
# 1. Build frontend
cd client
npm run build

# 2. Install Firebase CLI
npm install -g firebase-tools

# 3. Initialize Firebase
firebase init hosting

# 4. Deploy
firebase deploy

# 5. Remove frontend from Railway
# Go to Railway → Services → Delete frontend
```

---

## Next Steps

1. Create Railway project
2. Add backend service → Set environment variables
3. Add frontend service → Set build/start commands
4. Push to GitHub → Auto-deploy
5. Get URLs from Railway dashboard
6. Test health endpoints
7. Test login and API

---

## Comparison Table

| Aspect | Firebase+Railway | Both Railway |
|--------|------------------|-------------|
| **Setup** | Moderate | Easy |
| **Cost** | Lower | Higher |
| **Speed** | Faster (CDN) | Normal |
| **Management** | 2 dashboards | 1 dashboard |
| **Recommended** | ✅ Yes | Good alternative |

---

**Recommendation**: Use **Firebase Hosting + Railway** for better performance and cost.

See `DEPLOY_FIREBASE_RAILWAY.md` for detailed Firebase Hosting guide.
