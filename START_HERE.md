# 🚀 CoolieAssistant - START HERE

**Complete guide to run the project in 2 minutes.**

---

## ✅ Prerequisites Check

Run this first to verify everything is installed:

```powershell
.\verify-setup.ps1
```

**Expected output:**
```
All checks passed! Ready to start.
```

If you see errors, install the missing software:
- Python 3.10+: https://python.org/
- Node.js 18+: https://nodejs.org/

---

## 🚀 Start the Project

### Windows (PowerShell)

**Option 1: Start Both (Recommended)**
```powershell
.\start-all.ps1
```

**Option 2: Start Separately**

Terminal 1:
```powershell
.\start-backend.ps1
```

Terminal 2:
```powershell
.\start-frontend.ps1
```

### macOS/Linux (Bash)

**Make scripts executable:**
```bash
chmod +x start-backend.sh start-frontend.sh
```

**Terminal 1:**
```bash
./start-backend.sh
```

**Terminal 2:**
```bash
./start-frontend.sh
```

---

## 📍 Access the App

Once both services are running:

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Backend** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

---

## 🎯 What to Do Next

1. **Open Frontend:** http://localhost:5173
2. **Sign Up:** Create account with email
3. **Create Task:** Click "New Task"
4. **Send Message:** Type in chat box
5. **Check API:** Open http://localhost:8000/docs

---

## ⚠️ Common Issues

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
npm run dev -- --port 5174
```

### "ModuleNotFoundError"
- Make sure you're using the startup scripts
- Don't run `python -m uvicorn` from root directory

### "npm: command not found"
- Install Node.js from https://nodejs.org/
- Restart terminal

---

## 📚 Documentation

- **README.md** - Full project documentation
- **STARTUP_GUIDE.md** - Detailed startup instructions
- **DEVELOPMENT_GUIDE.md** - Development workflow
- **KNOWN_ISSUES.md** - Known issues and TODOs
- **PROJECT_ANALYSIS.md** - Project health assessment
- **QUICK_REFERENCE.md** - Quick lookup guide

---

## 🎓 First Time?

1. Run `.\verify-setup.ps1` to check prerequisites
2. Run `.\start-all.ps1` to start both services
3. Open http://localhost:5173
4. Sign up and explore

---

## 💡 Tips

- Keep both terminals open while developing
- Use http://localhost:8000/docs to test API
- Check browser console (F12) for errors
- Check backend terminal for API errors
- Hot reload works for both frontend and backend

---

## 🆘 Need Help?

1. Check **STARTUP_GUIDE.md** for detailed instructions
2. Check **KNOWN_ISSUES.md** for common problems
3. Check browser console (F12) for errors
4. Check backend terminal for API errors

---

**Ready? Run:** `.\verify-setup.ps1` then `.\start-all.ps1`

**Happy coding! 🎉**
