# CoolieAssistant - Known Issues & TODOs

This document tracks known issues, incomplete features, and areas for improvement.

---

## 🔴 Critical Issues

### 1. WhatsApp Send Not Implemented
**File:** `backend/app/routes/whatsapp.py` (line ~128)
**Status:** TODO
**Impact:** WhatsApp sending feature doesn't work

**Current State:**
```python
# TODO: Implement actual WhatsApp send via Twilio/Vonage
# For now, just log and save to database
```

**What's Needed:**
- Integrate Twilio or Vonage API
- Implement message sending logic
- Add error handling and retries
- Test with real WhatsApp numbers

**To Fix:**
1. Choose WhatsApp provider (Twilio or Vonage)
2. Get API credentials
3. Implement send logic in `whatsapp_service.py`
4. Add tests

---

### 2. Gmail OAuth Flow Not Implemented
**File:** `backend/app/routes/gmail.py` (lines ~128-170)
**Status:** TODO
**Impact:** Gmail integration doesn't work

**Current State:**
```python
# TODO: Implement Google OAuth flow
# TODO: Exchange code for access token
# TODO: Save credentials to Supabase
```

**What's Needed:**
- Complete OAuth authorization URL generation
- Implement token exchange
- Store credentials securely
- Implement email fetching

**To Fix:**
1. Set up Google OAuth credentials
2. Implement OAuth flow using `google-auth-oauthlib`
3. Store tokens in Supabase
4. Implement email processing

---

### 3. Gmail Email Fetching Not Implemented
**File:** `backend/app/routes/gmail.py` (line ~52)
**Status:** TODO
**Impact:** Gmail webhook receives notifications but doesn't fetch emails

**Current State:**
```python
# TODO: Fetch email from Gmail API
# For now, just acknowledge
```

**What's Needed:**
- Fetch email content from Gmail API
- Parse email structure
- Extract attachments
- Process with AI agents

---

## 🟡 High Priority Issues

### 4. No Rate Limiting
**Status:** Not Implemented
**Impact:** API endpoints can be abused

**What's Needed:**
- Add rate limiting middleware
- Configure limits per endpoint
- Add rate limit headers to responses

**To Fix:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/chat/message")
@limiter.limit("10/minute")
async def send_message():
    pass
```

---

### 5. Incomplete Error Handling
**Status:** Partially Implemented
**Impact:** Generic error messages, hard to debug

**What's Needed:**
- Structured error responses
- Specific error codes
- Better error messages
- Error logging

**Example:**
```python
class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
```

---

### 6. No Input Validation Layer
**Status:** Partially Implemented
**Impact:** Potential security issues

**What's Needed:**
- Centralized input validation
- Sanitization of user inputs
- SQL injection prevention
- XSS prevention

---

## 🟠 Medium Priority Issues

### 7. Large Agents File
**File:** `backend/app/agents/base_agents.py`
**Status:** Code smell
**Impact:** Hard to maintain, difficult to test

**Current State:** 300+ lines in single file

**What's Needed:**
- Split into separate files:
  - `chat_agent.py`
  - `whatsapp_agent.py`
  - `gmail_agent.py`
  - `task_agent.py`

---

### 8. No Structured Logging
**Status:** Basic logging only
**Impact:** Hard to debug in production

**What's Needed:**
- Structured logging format (JSON)
- Log levels configuration
- Log aggregation setup
- Sensitive data filtering

---

### 9. No Caching Layer
**Status:** Not Implemented
**Impact:** Repeated database queries

**What's Needed:**
- Redis setup
- Cache invalidation strategy
- Cache warming
- TTL configuration

---

### 10. No Database Migrations
**Status:** Manual setup only
**Impact:** Hard to version control schema changes

**What's Needed:**
- Alembic or similar migration tool
- Migration scripts
- Version control for schema

---

## 🔵 Low Priority Issues

### 11. No WebSocket Support
**Status:** Not Implemented
**Impact:** No real-time messaging

**What's Needed:**
- WebSocket endpoint setup
- Connection management
- Message broadcasting
- Reconnection logic

---

### 12. No Email Notifications
**Status:** Not Implemented
**Impact:** Users can't receive email alerts

**What's Needed:**
- Email service integration (SendGrid, AWS SES)
- Email templates
- Notification preferences
- Unsubscribe handling

---

### 13. No Test Suite
**Status:** Not Implemented
**Impact:** No automated testing

**What's Needed:**
- Unit tests
- Integration tests
- E2E tests
- Test coverage reporting

---

### 14. No CI/CD Pipeline
**Status:** Not Implemented
**Impact:** Manual deployment

**What's Needed:**
- GitHub Actions workflow
- Automated testing
- Automated deployment
- Environment management

---

### 15. No Monitoring & Alerting
**Status:** Not Implemented
**Impact:** Can't detect issues in production

**What's Needed:**
- Error tracking (Sentry)
- Performance monitoring (New Relic)
- Uptime monitoring
- Alert configuration

---

## 📋 Feature Requests

### Planned Features
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Custom workflows
- [ ] API rate limiting
- [ ] Webhook support
- [ ] Batch operations
- [ ] Export functionality

---

## 🔧 Configuration Issues

### 1. Dual Virtual Environments
**Issue:** Both `backend/venv/` and `backend/.venv/` exist
**Solution:** Use only one (recommend `.venv/`)

### 2. Loose Dependency Versions
**Issue:** `requirements.txt` uses `>=` without upper bounds
**Solution:** Use `requirements-pinned.txt` for production

### 3. Hardcoded CORS Origins
**Issue:** CORS origins hardcoded in `config.py`
**Solution:** Move to environment variables

---

## 📝 Documentation Gaps

### Missing Documentation
- [ ] API authentication guide
- [ ] Agent configuration guide
- [ ] Database migration strategy
- [ ] Performance tuning guide
- [ ] Monitoring setup guide
- [ ] Deployment checklist
- [ ] Contribution guidelines
- [ ] Architecture decision records

---

## 🚀 Improvement Opportunities

### Code Quality
- [ ] Add type hints to all functions
- [ ] Reduce code duplication
- [ ] Improve error messages
- [ ] Add docstrings
- [ ] Refactor large functions

### Performance
- [ ] Add database indexes
- [ ] Implement caching
- [ ] Optimize queries
- [ ] Add pagination
- [ ] Compress responses

### Security
- [ ] Add rate limiting
- [ ] Implement CSRF protection
- [ ] Add input validation
- [ ] Sanitize outputs
- [ ] Rotate secrets regularly

### Testing
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add E2E tests
- [ ] Increase coverage
- [ ] Add performance tests

---

## 📊 Issue Tracking

### Priority Matrix

```
        High Impact
             ↑
             │
    Critical │ High Priority
             │
    ─────────┼─────────→ High Effort
             │
    Medium   │ Low Priority
             │
             ↓
        Low Impact
```

### Current Status

| Issue | Priority | Effort | Status |
|-------|----------|--------|--------|
| WhatsApp Send | Critical | High | TODO |
| Gmail OAuth | Critical | High | TODO |
| Gmail Fetch | Critical | Medium | TODO |
| Rate Limiting | High | Medium | TODO |
| Error Handling | High | Medium | Partial |
| Input Validation | High | Medium | Partial |
| Agent Refactor | Medium | High | TODO |
| Logging | Medium | Medium | TODO |
| Caching | Medium | High | TODO |
| Migrations | Medium | Medium | TODO |

---

## 🎯 Next Steps

### Immediate (This Sprint)
1. [ ] Implement WhatsApp send
2. [ ] Implement Gmail OAuth
3. [ ] Add rate limiting
4. [ ] Improve error handling

### Short-term (Next Sprint)
5. [ ] Refactor agents
6. [ ] Add structured logging
7. [ ] Add input validation
8. [ ] Start test suite

### Medium-term (Next Quarter)
9. [ ] Implement caching
10. [ ] Add database migrations
11. [ ] Set up CI/CD
12. [ ] Add monitoring

---

## 📞 Reporting Issues

If you find an issue:

1. Check this document first
2. Search existing GitHub issues
3. Create a new issue with:
   - Clear title
   - Detailed description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment info

---

**Last Updated:** April 28, 2026
**Version:** 2.0.0
