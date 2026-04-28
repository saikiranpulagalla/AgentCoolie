# Deployment Guide: Firebase + Railway

Deploy CoolieAssistant frontend to Firebase Hosting and backend to Railway.

---

## Prerequisites

### Accounts Needed
- ✅ [Firebase Console](https://console.firebase.google.com)
- ✅ [Railway Account](https://railway.app)
- ✅ GitHub Account (for CI/CD)

### Tools
- Node.js 18+
- Python 3.10+
- `firebase-tools` CLI
- Git

---

## Part 1: Backend Deployment (Railway)

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Sign up / Log in
3. Create new project
4. Select "Deploy from GitHub repo"
5. Connect your GitHub and select the repo

### Step 2: Configure Backend Service

Railway will auto-detect Python and create service. Configure:

```bash
# In Railway dashboard → Environment Variables tab
# Add these:

ENV=production
HOST=0.0.0.0
PORT=8000

# Firebase
FIREBASE_ADMIN_CREDENTIALS_PATH=/etc/secrets/firebase.json
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-role-key

# AI Providers (choose one or more)
GOOGLE_AI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...

# Optional
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SESSION_SECRET_KEY=your-production-secret-key-change-this
```

### Step 3: Create .railwayrc.json

In project root:

```json
{
  "$schema": "https://railway.app/railwayrc.json",
  "build": {
    "builder": "dockerfile",
    "dockerfile": "backend/Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 4: Add Firebase Credentials to Railway

Railway has secure secret management:

1. In Railway dashboard → Variables → Create Secret
2. Name it: `FIREBASE_SERVICE_ACCOUNT_JSON`
3. Paste your Firebase service account JSON

**OR** if using file path:

1. Add secret `FIREBASE_SERVICE_ACCOUNT_JSON` with the full JSON
2. Set `FIREBASE_ADMIN_CREDENTIALS_PATH=/tmp/firebase.json`
3. Railway will handle it automatically

### Step 5: Deploy

Push to GitHub - Railway auto-deploys:

```bash
git add backend/
git commit -m "Deploy backend to Railway"
git push origin main
```

Railway will:
- ✅ Detect Python
- ✅ Build Docker image
- ✅ Deploy to container
- ✅ Generate public URL

**Your backend URL**: `https://your-project-backend.railway.app`

### Step 6: Verify Backend

```bash
# Test health endpoint
curl https://your-project-backend.railway.app/health

# Should return:
# {"status":"healthy","version":"2.0.0",...}
```

---

## Part 2: Frontend Deployment (Firebase Hosting)

### Step 1: Set up Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create new project (or use existing)
3. Enable **Hosting** (in left menu)

### Step 2: Install Firebase CLI

```bash
npm install -g firebase-tools

# Login
firebase login
```

### Step 3: Initialize Firebase in Project

```bash
cd client

# Initialize Firebase
firebase init hosting

# Prompts:
# "What folder to deploy?" → dist
# "Configure as SPA?" → Yes
# "Overwrite .gitignore?" → No
```

This creates `firebase.json` and `.firebaserc`

### Step 4: Update firebase.json

```json
{
  "hosting": [
    {
      "target": "coolie-frontend",
      "public": "dist",
      "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
      "rewrites": [
        {
          "source": "**",
          "destination": "/index.html"
        }
      ],
      "headers": [
        {
          "source": "**/*.@(js|css|png|svg|jpg|jpeg|gif|ico|woff|woff2|ttf|eot)",
          "headers": [
            {
              "key": "Cache-Control",
              "value": "public, max-age=31536000, immutable"
            }
          ]
        },
        {
          "source": "/index.html",
          "headers": [
            {
              "key": "Cache-Control",
              "value": "public, max-age=3600, must-revalidate"
            }
          ]
        }
      ]
    }
  ]
}
```

### Step 5: Set Environment Variables

Create `.env.production` in `client/`:

```env
VITE_API_URL=https://your-project-backend.railway.app
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_APP_ID=your-app-id
```

### Step 6: Build Frontend

```bash
cd client

# Build with production env vars
npm run build
```

### Step 7: Deploy to Firebase

```bash
# From client directory
firebase deploy --only hosting:coolie-frontend

# Or from project root
firebase deploy --only hosting --project <project-id>
```

Firebase will:
- ✅ Upload `dist/` folder
- ✅ Configure CDN
- ✅ Enable automatic HTTPS
- ✅ Create public URL

**Your frontend URL**: `https://your-project-id.web.app`

---

## Step 8: Update Backend CORS

Update backend to allow Firebase Hosting origin:

In `backend/app/core/config.py`:

```python
CORS_ORIGINS: list[str] = [
    "https://your-project-id.web.app",
    "https://your-project-id.firebaseapp.com",
    "http://localhost:5173",  # dev
    "http://localhost:8000",  # dev
]
```

Redeploy backend (Railway auto-updates on git push).

---

## Part 3: CI/CD Setup (Automatic Deployments)

### GitHub Actions for Frontend

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend to Firebase

on:
  push:
    branches: [main]
    paths:
      - 'client/**'
      - '.github/workflows/deploy-frontend.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: cd client && npm ci
      
      - name: Build
        run: cd client && npm run build
        env:
          VITE_API_URL: ${{ secrets.RAILWAY_API_URL }}
          VITE_FIREBASE_API_KEY: ${{ secrets.FIREBASE_API_KEY }}
          VITE_FIREBASE_PROJECT_ID: ${{ secrets.FIREBASE_PROJECT_ID }}
          VITE_FIREBASE_APP_ID: ${{ secrets.FIREBASE_APP_ID }}
      
      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          projectId: ${{ secrets.FIREBASE_PROJECT_ID }}
          channelId: live
```

### GitHub Actions for Backend

Create `.github/workflows/deploy-backend.yml`:

```yaml
name: Deploy Backend to Railway

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/deploy-backend.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        run: |
          curl -X POST https://api.railway.app/graphql \
            -H "Authorization: Bearer ${{ secrets.RAILWAY_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"query":"mutation{deploy(input:{projectId:\"${{ secrets.RAILWAY_PROJECT_ID }}\"})}"}'
```

### Add GitHub Secrets

Go to GitHub repo → Settings → Secrets → New secret:

```
RAILWAY_TOKEN=               # From Railway → Account → API Tokens
RAILWAY_PROJECT_ID=          # From Railway dashboard
RAILWAY_API_URL=             # Your Railway backend URL
FIREBASE_SERVICE_ACCOUNT=    # Paste entire JSON from Firebase
FIREBASE_PROJECT_ID=         # Your Firebase project ID
FIREBASE_API_KEY=            # Your Firebase API key
FIREBASE_APP_ID=             # Your Firebase app ID
GITHUB_TOKEN=                # Auto-provided by GitHub
```

---

## Configuration Summary

### Frontend (Firebase Hosting)
- **URL**: `https://your-project-id.web.app`
- **Environment**: `VITE_API_URL`, Firebase config
- **Build**: `npm run build` → `dist/`
- **Deploy**: `firebase deploy`
- **CDN**: Global, automatic

### Backend (Railway)
- **URL**: `https://your-project-backend.railway.app`
- **Environment**: Firebase creds, Supabase, AI keys
- **Build**: Automatic from Dockerfile
- **Deploy**: Git push or Railway CLI
- **Scaling**: Easy horizontal scaling

---

## Testing Deployment

### Frontend Test
```bash
# Visit https://your-project-id.web.app
# Should load React app
# Open browser console - no errors
```

### Backend Test
```bash
# Health check
curl https://your-project-backend.railway.app/health

# API docs
https://your-project-backend.railway.app/docs
```

### End-to-End Test
1. Visit frontend URL
2. Login with Firebase
3. Send chat message
4. Should work without errors

---

## Common Issues

### CORS Error
**Problem**: Frontend can't reach backend
**Solution**: 
```python
# backend/app/core/config.py
CORS_ORIGINS = ["https://your-project-id.web.app", ...]
# Redeploy backend
```

### Firebase Build Error
**Problem**: `npm run build` fails
**Solution**: 
```bash
# Check Node version
node --version  # Should be 18+

# Clear cache
rm -rf client/node_modules client/package-lock.json
npm install
npm run build
```

### Railway Deployment Fails
**Problem**: Build error or startup error
**Solution**:
```bash
# Check logs
railway logs

# Verify Python version requirement
# backend/Dockerfile should use python:3.11

# Check environment variables in Railway dashboard
```

### API Key Not Found
**Problem**: "GOOGLE_AI_API_KEY must be set"
**Solution**:
```bash
# In Railway → Variables tab
# Make sure key is set and deployed
# Restart service
```

---

## Monitoring & Logs

### Firebase Hosting Logs
```bash
firebase hosting:channel:list
firebase hosting:channel:create <channel>
```

### Railway Logs
```bash
railway logs -f  # Follow logs

# Or in Railway dashboard → Logs tab
```

### Error Tracking
- JavaScript errors: Browser console
- Backend errors: Railway logs
- Database errors: Supabase dashboard

---

## Rollback Plan

### Frontend Rollback
```bash
# Redeploy previous build
git revert <commit>
npm run build
firebase deploy
```

### Backend Rollback
```bash
# Railway keeps deployment history
# In Railway dashboard, select previous deployment
# Click "Ignore" then "Deploy"
```

---

## Cost Estimation

### Firebase Hosting (Free)
- 1 GB storage free
- 10 GB/month bandwidth free
- Paid: $0.18/GB after free tier

### Railway
- **Free tier**: $5/month credit
- **Pay-as-you-go**: ~$6 per month for small backend
- Includes 100 GB bandwidth/month

**Total Monthly**: ~$6-15 (both free tiers cover most cases)

---

## Production Checklist

- [ ] Environment variables configured in both platforms
- [ ] Firebase project created and hosting enabled
- [ ] Railway project created and connected to GitHub
- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] Login works
- [ ] Chat API responds
- [ ] Tasks can be created
- [ ] CORS configured correctly
- [ ] CI/CD workflows set up
- [ ] GitHub secrets configured
- [ ] Custom domain configured (optional)
- [ ] SSL certificates configured (automatic)
- [ ] Analytics enabled (optional)
- [ ] Error tracking set up (optional)

---

## Next Steps

1. **Deploy backend first** (Railway)
2. **Test backend** health endpoint
3. **Update frontend env vars** with Railway backend URL
4. **Deploy frontend** (Firebase)
5. **Test end-to-end** login → chat → tasks
6. **Set up CI/CD** for automatic deployments
7. **Monitor logs** for issues

---

## Support & Troubleshooting

- 📚 [Firebase Hosting Docs](https://firebase.google.com/docs/hosting)
- 🚂 [Railway Docs](https://docs.railway.app)
- 🔗 [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- 💬 Check logs for specific errors

**Questions?** Review the deployment logs in each platform's dashboard.
