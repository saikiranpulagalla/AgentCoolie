# CoolieAssistant - Startup Guide

Complete guide to start the project correctly.

---

## 🪟 **Windows (PowerShell)**

### Option 1: Automatic (Recommended)

**Start Both Services:**
```powershell
.\start-all.ps1
```

This will:
- ✅ Open backend in new window
- ✅ Open frontend in new window
- ✅ Auto-install dependencies
- ✅ Auto-activate virtual environment

**Start Only Backend:**
```powershell
.\start-backend.ps1
```

**Start Only Frontend:**
```powershell
.\start-frontend.ps1
```

### Option 2: Manual

**Terminal 1 - Backend:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd client
npm install
npm run dev
```

---

## 🍎 **macOS/Linux (Bash)**

### Option 1: Automatic (Recommended)

**Make scripts executable:**
```bash
chmod +x start-backend.sh
chmod +x start-frontend.sh
```

**Start Backend:**
```bash
./start-backend.sh
```

**Start Frontend (in new terminal):**
```bash
./start-frontend.sh
```

### Option 2: Manual

**Terminal 1 - Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd client
npm install
npm run dev
```

---

## ✅ **Verify Everything Works**

### Check Backend
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}
```

### Check Frontend
Open http://localhost:5173 in browser
- Should see login page

### Check API Docs
Open http://localhost:8000/docs
- Should see Swagger UI

---

## 🎯 **Access Points**

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Web app |
| Backend | http://localhost:8000 | API server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health | http://localhost:8000/health | Backend status |

---

## 🐛 **Troubleshooting**

### "ModuleNotFoundError: No module named 'app'"
**Cause:** Running from wrong directory
**Fix:** Use the startup scripts or `cd backend` first

### "Port 8000 already in use"
```powershell
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### "Port 5173 already in use"
```powershell
# Windows
npm run dev -- --port 5174

# macOS/Linux
npm run dev -- --port 5174
```

### "Virtual environment not found"
```powershell
# Windows
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
cd backend
python3 -m venv venv
source venv/bin/activate
```

### "npm: command not found"
- Install Node.js from https://nodejs.org/
- Restart terminal
- Try again

### "python: command not found"
- Install Python 3.10+ from https://python.org/
- Restart terminal
- Try again

---

## 📝 **Important Notes**

1. **Always run from project root** - Not from backend or client directory
2. **Keep both terminals open** - Backend and frontend need to run simultaneously
3. **Use the startup scripts** - They handle all setup automatically
4. **Check .env file** - Make sure all credentials are set
5. **Wait for startup** - Give services 5-10 seconds to fully start

---

## 🚀 **Quick Start (Copy-Paste)**

### Windows PowerShell
```powershell
# From project root
.\start-all.ps1
```

### macOS/Linux Bash
```bash
# From project root
chmod +x start-backend.sh start-frontend.sh
./start-backend.sh  # Terminal 1
./start-frontend.sh # Terminal 2
```

---

## 📊 **Expected Output**

### Backend
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
2026-04-28 12:33:44,519 - app.main - INFO - Starting CoolieAssistant API...
```

### Frontend
```
VITE v7.1.12  ready in 1043 ms
➜  Local:   http://localhost:5173/
```

---

## 🎓 **Next Steps**

1. Open http://localhost:5173
2. Sign up with email
3. Create a task
4. Send a message
5. Check API docs at http://localhost:8000/docs

---

**That's it! You're ready to develop.** 🎉
