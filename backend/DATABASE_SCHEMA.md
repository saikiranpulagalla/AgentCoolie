# CoolieAssistant Database Schema

PostgreSQL database schema for CoolieAssistant, hosted on Supabase.

## Overview

The database stores user data, chat history, tasks, preferences, and credentials for multi-channel integration.

## Tables

### 1. `users`
Stores user account information.

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  firebase_uid VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  display_name VARCHAR(255),
  avatar_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT true
);
```

**Columns:**
- `id` - Unique identifier (UUID)
- `firebase_uid` - Firebase user ID for authentication
- `email` - User email address
- `display_name` - User's display name
- `avatar_url` - Profile picture URL
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp
- `last_login` - Last login timestamp
- `is_active` - Account status

**Indexes:**
```sql
CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);
CREATE INDEX idx_users_email ON users(email);
```

---

### 2. `chat_messages`
Stores chat conversation history.

```sql
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  role VARCHAR(50) NOT NULL, -- 'user' or 'assistant'
  sentiment VARCHAR(50), -- 'positive', 'negative', 'neutral'
  metadata JSONB, -- Additional data (source, intent, etc.)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**
- `id` - Message ID
- `user_id` - Reference to user
- `content` - Message text
- `role` - 'user' or 'assistant'
- `sentiment` - Analyzed sentiment
- `metadata` - JSON data (source, intent, etc.)
- `created_at` - Message timestamp
- `updated_at` - Last update timestamp

**Indexes:**
```sql
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
```

---

### 3. `tasks`
Stores user tasks and to-do items.

```sql
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
  priority VARCHAR(50) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
  due_date TIMESTAMP,
  created_from_text TEXT, -- Original natural language input
  source VARCHAR(50), -- 'chat', 'whatsapp', 'gmail', 'manual'
  metadata JSONB, -- Additional data (tags, subtasks, etc.)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);
```

**Columns:**
- `id` - Task ID
- `user_id` - Reference to user
- `title` - Task title
- `description` - Detailed description
- `status` - Current status
- `priority` - Task priority level
- `due_date` - Due date/time
- `created_from_text` - Original NLP input
- `source` - Where task was created
- `metadata` - JSON (tags, subtasks, etc.)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `completed_at` - Completion timestamp

**Indexes:**
```sql
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
```

---

### 4. `user_preferences`
Stores user settings and preferences.

```sql
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  theme VARCHAR(50) DEFAULT 'light', -- 'light', 'dark', 'auto'
  language VARCHAR(10) DEFAULT 'en',
  timezone VARCHAR(50) DEFAULT 'UTC',
  notifications_enabled BOOLEAN DEFAULT true,
  email_notifications BOOLEAN DEFAULT true,
  whatsapp_notifications BOOLEAN DEFAULT true,
  ai_provider VARCHAR(50) DEFAULT 'gemini', -- 'gemini', 'openai', 'cohere'
  embedding_provider VARCHAR(50) DEFAULT 'cohere',
  metadata JSONB, -- Additional preferences
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**
- `id` - Preference ID
- `user_id` - Reference to user (unique)
- `theme` - UI theme preference
- `language` - Preferred language
- `timezone` - User timezone
- `notifications_enabled` - Global notification toggle
- `email_notifications` - Email notification preference
- `whatsapp_notifications` - WhatsApp notification preference
- `ai_provider` - Preferred AI model
- `embedding_provider` - Preferred embedding service
- `metadata` - JSON for additional settings
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

**Indexes:**
```sql
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
```

---

### 5. `user_credentials`
Stores encrypted credentials for external services.

```sql
CREATE TABLE user_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  service VARCHAR(50) NOT NULL, -- 'gmail', 'whatsapp', 'youtube', etc.
  credential_type VARCHAR(50) NOT NULL, -- 'oauth_token', 'api_key', 'phone_number'
  encrypted_value TEXT NOT NULL, -- Encrypted credential
  expires_at TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, service, credential_type)
);
```

**Columns:**
- `id` - Credential ID
- `user_id` - Reference to user
- `service` - External service name
- `credential_type` - Type of credential
- `encrypted_value` - Encrypted credential value
- `expires_at` - Expiration timestamp (for tokens)
- `is_active` - Credential status
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

**Indexes:**
```sql
CREATE INDEX idx_user_credentials_user_id ON user_credentials(user_id);
CREATE INDEX idx_user_credentials_service ON user_credentials(service);
```

---

### 6. `notifications`
Stores user notifications.

```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  type VARCHAR(50) NOT NULL, -- 'info', 'success', 'warning', 'error'
  source VARCHAR(50), -- 'system', 'task', 'chat', 'whatsapp', 'gmail'
  related_id UUID, -- Reference to related entity (task_id, message_id, etc.)
  is_read BOOLEAN DEFAULT false,
  action_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  read_at TIMESTAMP
);
```

**Columns:**
- `id` - Notification ID
- `user_id` - Reference to user
- `title` - Notification title
- `message` - Notification message
- `type` - Notification type
- `source` - Where notification came from
- `related_id` - Reference to related entity
- `is_read` - Read status
- `action_url` - URL for action button
- `created_at` - Creation timestamp
- `read_at` - Read timestamp

**Indexes:**
```sql
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

---

### 7. `whatsapp_messages`
Stores WhatsApp message history.

```sql
CREATE TABLE whatsapp_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  phone_number VARCHAR(20) NOT NULL,
  message_id VARCHAR(255) UNIQUE NOT NULL,
  content TEXT NOT NULL,
  direction VARCHAR(50) NOT NULL, -- 'inbound', 'outbound'
  status VARCHAR(50) DEFAULT 'received', -- 'received', 'sent', 'delivered', 'read', 'failed'
  media_url TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**
- `id` - Record ID
- `user_id` - Reference to user
- `phone_number` - WhatsApp phone number
- `message_id` - WhatsApp message ID
- `content` - Message text
- `direction` - Inbound or outbound
- `status` - Message status
- `media_url` - URL to media attachment
- `metadata` - JSON metadata
- `created_at` - Timestamp

**Indexes:**
```sql
CREATE INDEX idx_whatsapp_messages_user_id ON whatsapp_messages(user_id);
CREATE INDEX idx_whatsapp_messages_phone_number ON whatsapp_messages(phone_number);
```

---

### 8. `gmail_messages`
Stores Gmail message metadata.

```sql
CREATE TABLE gmail_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  gmail_id VARCHAR(255) UNIQUE NOT NULL,
  thread_id VARCHAR(255),
  subject VARCHAR(255),
  sender VARCHAR(255),
  recipient VARCHAR(255),
  body TEXT,
  is_read BOOLEAN DEFAULT false,
  is_starred BOOLEAN DEFAULT false,
  labels TEXT[], -- Array of Gmail labels
  processed BOOLEAN DEFAULT false,
  ai_summary TEXT,
  priority VARCHAR(50), -- 'low', 'medium', 'high'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  received_at TIMESTAMP
);
```

**Columns:**
- `id` - Record ID
- `user_id` - Reference to user
- `gmail_id` - Gmail message ID
- `thread_id` - Gmail thread ID
- `subject` - Email subject
- `sender` - Sender email
- `recipient` - Recipient email
- `body` - Email body
- `is_read` - Read status
- `is_starred` - Starred status
- `labels` - Gmail labels
- `processed` - AI processing status
- `ai_summary` - AI-generated summary
- `priority` - Detected priority
- `created_at` - Record creation
- `received_at` - Email received time

**Indexes:**
```sql
CREATE INDEX idx_gmail_messages_user_id ON gmail_messages(user_id);
CREATE INDEX idx_gmail_messages_gmail_id ON gmail_messages(gmail_id);
CREATE INDEX idx_gmail_messages_processed ON gmail_messages(processed);
```

---

## Relationships

```
users (1) ──→ (many) chat_messages
users (1) ──→ (many) tasks
users (1) ──→ (1) user_preferences
users (1) ──→ (many) user_credentials
users (1) ──→ (many) notifications
users (1) ──→ (many) whatsapp_messages
users (1) ──→ (many) gmail_messages
```

---

## Row Level Security (RLS)

Enable RLS on all tables to ensure users can only access their own data:

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE gmail_messages ENABLE ROW LEVEL SECURITY;

-- Example policy for chat_messages
CREATE POLICY "Users can only access their own messages"
  ON chat_messages
  FOR ALL
  USING (auth.uid()::text = user_id::text);
```

---

## Migrations

To apply schema changes:

```bash
# Using Supabase CLI
supabase migration new add_new_table
supabase migration up

# Or run SQL directly in Supabase dashboard
```

---

## Backups

Supabase automatically backs up your database. To restore:

1. Go to Supabase Dashboard
2. Settings → Backups
3. Select backup and restore

---

## Performance Optimization

### Recommended Indexes (Already Included)
- User lookups: `firebase_uid`, `email`
- Message queries: `user_id`, `created_at`
- Task filtering: `user_id`, `status`, `due_date`
- Notification queries: `user_id`, `is_read`

### Query Optimization Tips
1. Always filter by `user_id` first
2. Use pagination for large result sets
3. Index frequently filtered columns
4. Archive old messages periodically

---

## Maintenance

### Regular Tasks
- Monitor database size
- Review slow queries
- Archive old data
- Update statistics

### Monitoring
```sql
-- Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Troubleshooting

### Connection Issues
- Check Supabase URL and key
- Verify network connectivity
- Check firewall rules

### Performance Issues
- Analyze slow queries
- Add missing indexes
- Consider partitioning large tables

### Data Issues
- Use transactions for consistency
- Enable audit logging
- Regular backups
