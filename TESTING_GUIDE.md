# CoolieAssistant - Testing Guide

Complete guide to test the system prompts and AI responses.

---

## ✅ What Was Fixed

1. **System Prompt Integration** - ChatAgent now uses robust system prompt
2. **Prompt Handling** - Fixed double-appending of text in AI service
3. **Model Configuration** - Using configurable model names instead of hardcoded values
4. **Response Quality** - AI now responds as CoolieAssistant, not generic LLM

---

## 🚀 How to Test

### Step 1: Start the Project

```powershell
.\verify-setup.ps1
.\start-all.ps1
```

### Step 2: Open the Application

```
http://localhost:5173
```

### Step 3: Sign In

- Create account or sign in with existing credentials
- Make sure you're authenticated

### Step 4: Test Messages

Send these test messages and check the responses:

#### Test 1: Task Creation
```
Message: "I need to call my mom tomorrow at 3 PM"
Expected: Response should offer to create a task with specific details
```

#### Test 2: Task Extraction
```
Message: "Remind me to buy groceries on Friday"
Expected: Response should extract task details and offer to create it
```

#### Test 3: General Question
```
Message: "What's the weather like?"
Expected: Response should be helpful and acknowledge limitations
```

#### Test 4: Productivity Help
```
Message: "Help me organize my tasks for today"
Expected: Response should focus on productivity and task management
```

#### Test 5: Feature Suggestion
```
Message: "How can I be more productive?"
Expected: Response should suggest CoolieAssistant features
```

---

## 🔍 What to Look For

### Good Responses (System Prompt Working)
✅ Responses mention tasks, productivity, or organization
✅ Responses are concise and actionable
✅ Responses offer to create tasks when appropriate
✅ Responses use friendly but professional tone
✅ Responses suggest relevant features

### Bad Responses (System Prompt Not Working)
❌ Generic "As a large language model..." responses
❌ Responses about general knowledge unrelated to tasks
❌ Verbose, non-actionable responses
❌ Responses that ignore the CoolieAssistant context

---

## 🐛 Debugging

### Check Backend Logs

Look for these messages in the backend terminal:

```
INFO - Chat agent initialized for user [user_id]
INFO - Gemini service initialized with model: gemini-1.5-flash
```

### Check Frontend Console

Open browser DevTools (F12) and check:

1. **Network Tab**
   - POST to `/api/webhook/proxy`
   - Response should contain assistant message

2. **Console Tab**
   - Look for any errors
   - Check for debug messages about webhook

### Test API Directly

```bash
# Open Swagger UI
http://localhost:8000/docs

# Find /api/chat/message endpoint
# Click "Try it out"
# Send a test message
# Check the response
```

---

## 📊 Expected Response Flow

```
User Input
    ↓
Frontend sends to /api/webhook/proxy
    ↓
Backend ChatAgent.chat() called
    ↓
System prompt + user message combined
    ↓
Sent to Gemini API
    ↓
Gemini responds with CoolieAssistant-like response
    ↓
Response returned to frontend
    ↓
Displayed in chat
```

---

## ✨ System Prompt Content

The ChatAgent uses this system prompt:

```
You are CoolieAssistant, an intelligent personal AI assistant designed to help users 
manage tasks, communicate effectively, and automate workflows.

## Your Core Purpose
- Help users create, organize, and track tasks
- Provide intelligent responses to user queries
- Extract actionable tasks from natural language
- Analyze sentiment and intent from messages
- Assist with productivity and organization

## Your Capabilities
1. Task Management
2. Natural Language Understanding
3. Sentiment Analysis
4. Information Retrieval
5. Workflow Automation

## How to Respond
- Be concise and actionable
- Focus on helping the user accomplish their goals
- When a user mentions a task, offer to create it
- Ask clarifying questions if needed
- Provide specific, helpful suggestions
- Use a friendly but professional tone
```

---

## 🔧 Troubleshooting

### Issue: Still Getting Generic Responses

**Check 1: Backend Logs**
```
Look for: "Chat agent initialized"
If missing: Backend not restarted after changes
Solution: Restart backend with .\start-backend.ps1
```

**Check 2: Model Configuration**
```
Check .env file:
GEMINI_MODEL=gemini-1.5-flash
GOOGLE_AI_API_KEY=<your_key>
```

**Check 3: API Endpoint**
```
Frontend should send to: /api/webhook/proxy
Check browser Network tab to verify
```

### Issue: Timeout or Error

**Check 1: API Key**
```
Verify GOOGLE_AI_API_KEY is set in .env
Test with: curl http://localhost:8000/health
```

**Check 2: Model Availability**
```
Verify gemini-1.5-flash is available
Try different model: gemini-1.5-pro
Update .env: GEMINI_MODEL=gemini-1.5-pro
```

**Check 3: Network**
```
Verify backend is running: http://localhost:8000/docs
Verify frontend can reach backend
Check CORS settings
```

---

## 📈 Performance Testing

### Response Time
- Expected: 2-5 seconds
- If longer: Check API key rate limits
- If much longer: Check network connection

### Response Quality
- Check if response is relevant to input
- Check if response follows system prompt guidelines
- Check if response is actionable

### Error Handling
- Send invalid input
- Send very long messages
- Send special characters
- Verify graceful error handling

---

## 🎯 Test Scenarios

### Scenario 1: New User
1. Sign up with new account
2. Send first message
3. Verify response is welcoming and helpful

### Scenario 2: Task Management
1. Send message about a task
2. Verify response offers to create task
3. Check if task details are extracted

### Scenario 3: Multiple Messages
1. Send several messages in sequence
2. Verify responses are consistent
3. Check if context is maintained

### Scenario 4: Error Recovery
1. Send message while backend is down
2. Verify error message is shown
3. Restart backend
4. Verify messages work again

---

## 📝 Test Report Template

```
Date: [date]
Tester: [name]
Environment: [dev/staging/prod]

Test Results:
- Task Creation: [PASS/FAIL]
- Task Extraction: [PASS/FAIL]
- General Questions: [PASS/FAIL]
- Productivity Help: [PASS/FAIL]
- Feature Suggestions: [PASS/FAIL]

Issues Found:
1. [issue description]
2. [issue description]

Notes:
[any additional observations]
```

---

## 🚀 Automated Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd client
npm run test
```

### E2E Tests
```bash
# Coming soon
```

---

## 📞 Support

If tests fail:

1. Check backend logs
2. Check frontend console
3. Verify .env configuration
4. Check API endpoint
5. Restart services
6. Check SYSTEM_PROMPTS.md for details

---

**Last Updated:** April 28, 2026  
**Version:** 2.0.0
