# CoolieAssistant - Quick Reference Guide

**Quick links and commands for common tasks.**

---

## 🚀 Getting Started

### Clone & Setup (5 minutes)
```bash
git clone https://github.com/yourusername/CoolieAssistant.git
cd CoolieAssistant
cp .env.example .env
# Edit .env with your credentials
```

### Run Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Run Frontend
```bash
cd client
npm install
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | Main documentation |
| `DEVELOPMENT_GUIDE.md` | Development setup & workflow |
| `KNOWN_ISSUES.md` | Issues & TODOs |
| `PROJECT_ANALYSIS.md` | Project health & recommendations |
| `IMPROVEMENTS_SUMMARY.md` | What was improved |
| `QUICK_REFERENCE.md` | This file |

---

## 🔧 Common Commands

### Backend
```bash
# Start development server
python -m uvicorn app.main:app --reload

# Run on different port
python -m uvicorn app.main:app --reload --port 8001

# Check health
curl http://localhost:8000/health

# View API docs
# Open http://localhost:8000/docs
```

### Frontend
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests (when available)
npm run test
```

### Docker
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.10+

# Check port availability
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # macOS/Linux

# Kill process using port
taskkill /PID <PID> /F  # Windows
kill -9 <PID>  # macOS/Linux
```

### Frontend Can't Reach Backend
```bash
# Check backend is running
curl http://localhost:8000/health

# Check VITE_API_URL in .env
echo $VITE_API_URL

# Check browser console (F12) for CORS errors
```

### Firebase Not Working
```bash
# Check environment variables
echo $VITE_FIREBASE_API_KEY
echo $VITE_FIREBASE_PROJECT_ID

# Verify Firebase project is active
# Check browser console (F12) for errors
```

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5173
kill -9 <PID>

# Or use different port
npm run dev -- --port 5174
```

---

## 📋 Environment Variables

### Required
```env
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_APP_ID=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
GOOGLE_AI_API_KEY=...  # or OPENAI_API_KEY or COHERE_API_KEY
```

### Optional
```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
YOUTUBE_API_KEY=...
VITE_API_URL=http://localhost:8000
```

---

## 🔐 Security Checklist

- [ ] .env file in .gitignore
- [ ] No API keys in code
- [ ] No credentials in repository
- [ ] Use .env.example for templates
- [ ] Different credentials for dev/prod
- [ ] Rotate API keys regularly

---

## 📊 Project Structure

```
CoolieAssistant/
├── backend/          # Python FastAPI
├── client/           # React TypeScript
├── shared/           # Shared types
├── docker-compose.yml
├── .env.example
├── README.md
├── DEVELOPMENT_GUIDE.md
├── KNOWN_ISSUES.md
├── PROJECT_ANALYSIS.md
└── QUICK_REFERENCE.md
```

---

## 🎯 Key URLs

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | Frontend app |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/health | Health check |

---

## 📞 Getting Help

1. **Check README.md** - Main documentation
2. **Check DEVELOPMENT_GUIDE.md** - Development questions
3. **Check KNOWN_ISSUES.md** - Known problems
4. **Check troubleshooting** - Common issues
5. **Check browser console** - Frontend errors (F12)
6. **Check backend logs** - Backend errors

---

## 🚀 Deployment

### Docker
```bash
docker-compose up -d
```

### Manual
```bash
# Backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd client
npm run build
npm run preview
```

---

## 📈 Project Status

- **Overall Health:** 78/100
- **Architecture:** 85/100
- **Documentation:** 90/100
- **Security:** 75/100
- **Testing:** 10/100 (gap)
- **Deployment:** 80/100

---

## ⚠️ Known Limitations

- ❌ WhatsApp send not implemented
- ❌ Gmail OAuth not implemented
- ❌ No rate limiting
- ❌ No test suite
- ❌ No CI/CD pipeline
- ❌ No monitoring

See `KNOWN_ISSUES.md` for details.

---

## 🎓 Learning Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [TypeScript Docs](https://www.typescriptlang.org/)
- [Supabase Docs](https://supabase.com/docs)
- [Firebase Docs](https://firebase.google.com/docs)

---

## 💡 Tips

- Keep both backend and frontend terminals open
- Use browser DevTools (F12) for debugging
- Check backend logs for API errors
- Use http://localhost:8000/docs to test APIs
- Hot reload works for both frontend and backend
- Save files to see changes immediately

---

**Last Updated:** April 28, 2026  
**Version:** 2.0.0
