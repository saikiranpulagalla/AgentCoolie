# Quick Deploy Guide: Firebase (Frontend) + Railway (Backend)

Fast reference for deploying to Firebase Hosting and Railway.

---

## 30-Minute Deployment

### Prerequisites (5 min)
```bash
# Install tools
npm install -g firebase-tools

# Clone repo
git clone <repo>
cd CoolieAssistant

# Create accounts
# 1. Firebase: https://console.firebase.google.com
# 2. Railway: https://railway.app
```

### Backend to Railway (10 min)

1. **Push code to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Railway Dashboard**
   - New Project → Deploy from GitHub
   - Select your repo
   - Select `backend` service

3. **Set Environment Variables** (in Railway dashboard)
```
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
FIREBASE_SERVICE_ACCOUNT_JSON={...}
GOOGLE_AI_API_KEY=...
SESSION_SECRET_KEY=generate-random-string
```

4. **Wait for deployment** (2-3 minutes)
   - Get your Railway URL: `https://your-backend.railway.app`
   - Test: `curl https://your-backend.railway.app/health`

### Frontend to Firebase (10 min)

1. **Initialize Firebase**
```bash
cd client
firebase init hosting
# Questions: dist → yes, SPA → yes
```

2. **Create .env.production**
```
VITE_API_URL=https://your-backend.railway.app
VITE_FIREBASE_API_KEY=xxx
VITE_FIREBASE_PROJECT_ID=xxx
VITE_FIREBASE_APP_ID=xxx
```

3. **Build & Deploy**
```bash
npm run build
firebase deploy --only hosting
```

4. **Get Your URL**
   - Firebase Console → Hosting → Domain
   - Format: `https://your-project.web.app`

### Update Backend CORS (2 min)

In `backend/app/core/config.py`:

```python
CORS_ORIGINS: list[str] = [
    "https://your-project.web.app",
    "https://your-project.firebaseapp.com",
]
```

```bash
git add backend/
git commit -m "Update CORS for production"
git push
```

---

## Verification Checklist

```bash
# 1. Backend health
curl https://your-backend.railway.app/health
# {"status":"healthy",...}

# 2. Backend docs
# https://your-backend.railway.app/docs

# 3. Frontend loads
# https://your-project.web.app

# 4. Login works
# Click login button

# 5. Send message
# Type in chat, should work
```

---

## Environment Variables Reference

### Railway (Backend)
```
ENV=production
HOST=0.0.0.0
PORT=8000
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
GOOGLE_AI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-...
SESSION_SECRET_KEY=change-this
CORS_ORIGINS=["https://your-project.web.app"]
```

### Firebase Frontend
```
VITE_API_URL=https://your-backend.railway.app
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_PROJECT_ID=project-id
VITE_FIREBASE_APP_ID=...
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| CORS Error | Update `CORS_ORIGINS` in backend, redeploy |
| 404 Frontend | Ensure `dist/` exists: `npm run build` |
| "Module not found" backend | Check `requirements.txt`, Railway rebuilds on push |
| Firebase login fails | Check `VITE_FIREBASE_*` variables |
| API request times out | Check Railway logs: `https://railway.app` |

---

## Updating Code

### Update Backend
```bash
# Make changes in `backend/`
git add backend/
git commit -m "Update backend"
git push
# Railway auto-deploys in 1-2 minutes
```

### Update Frontend  
```bash
# Make changes in `client/`
npm run build  # Build locally first
git add client/
git commit -m "Update frontend"
git push
firebase deploy
# Firebase deploys in ~1 minute
```

---

## Custom Domain (Optional)

### Firebase
1. Firebase Console → Hosting → Domains
2. Click "Add custom domain"
3. Verify DNS ownership
4. Point to Firebase

### Railway (optional, if needed)
1. Railway Docs → Custom Domains
2. Add domain to Railway project
3. Update DNS

---

## Estimated Time & Cost

| Metric | Value |
|--------|-------|
| **Setup Time** | 30 minutes |
| **Deploy Time** | 5 minutes per update |
| **Monthly Cost** | Free - $15 (mostly free tier) |
| **Uptime SLA** | 99.9%+ (both platforms) |

---

## Need Help?

- 📚 Full Guide: See `DEPLOY_FIREBASE_RAILWAY.md`
- 🚂 Railway Logs: `https://railway.app` → Logs tab
- 🔥 Firebase Logs: `firebase hosting:channel:list`
- 📖 API Docs: `https://your-backend.railway.app/docs`

Done! 🎉
