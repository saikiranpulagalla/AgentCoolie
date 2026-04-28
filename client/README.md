# CoolieAssistant Frontend

Modern React-based frontend for CoolieAssistant, a multi-channel AI-powered personal assistant.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example client/src/.env

# Edit with your credentials
# Required:
# - VITE_FIREBASE_API_KEY
# - VITE_FIREBASE_PROJECT_ID
# - VITE_FIREBASE_APP_ID
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
```

### Development

```bash
# Start dev server (runs on http://localhost:5173)
npm run dev

# Type checking
npm run check

# Build for production
npm run build

# Preview production build
npm start
```

## 📁 Project Structure

```
client/src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn/ui components (Radix UI)
│   ├── AppSidebar.tsx  # Main navigation sidebar
│   ├── ChatBubble.tsx  # Chat message display
│   ├── ChatInput.tsx   # Chat input field
│   ├── TaskCard.tsx    # Task display card
│   ├── ErrorBoundary.tsx # Error handling
│   └── ...
├── contexts/           # React Context providers
│   ├── AuthContext.tsx      # Authentication state
│   ├── ChatContext.tsx      # Chat state
│   ├── NotificationContext.tsx # Notifications
│   └── ThemeProvider.tsx    # Theme management
├── pages/              # Page components
│   ├── Home.tsx        # Dashboard
│   ├── Login.tsx       # Authentication
│   ├── Chat.tsx        # Chat interface
│   ├── Tasks.tsx       # Task management
│   ├── Settings.tsx    # User settings
│   └── ...
├── hooks/              # Custom React hooks
│   ├── use-mobile.tsx
│   ├── use-toast.ts
│   └── use-microphone.ts
├── lib/                # Utilities and helpers
│   ├── api.ts          # API client
│   ├── firebase.ts     # Firebase initialization
│   ├── queryClient.ts  # React Query setup
│   └── utils.ts        # Helper functions
├── App.tsx             # Root component
├── main.tsx            # Entry point
└── index.css           # Global styles
```

## 🎨 Technology Stack

- **React** 18.3.1 - UI framework
- **TypeScript** 5.6.3 - Type safety
- **Vite** 7.1.9 - Build tool
- **Tailwind CSS** 3.4.17 - Styling
- **Radix UI** - Accessible component primitives
- **shadcn/ui** - Pre-built components
- **React Query** 5.60.5 - Data fetching
- **React Hook Form** 7.55.0 - Form management
- **Zod** 3.25.1 - Schema validation
- **Firebase** 12.3.0 - Authentication
- **Wouter** 3.3.5 - Routing
- **Framer Motion** 11.13.1 - Animations

## 🔐 Authentication

Uses Firebase Authentication with email/password and OAuth support.

```typescript
import { useAuth } from '@/contexts/AuthContext';

function MyComponent() {
  const { user, signIn, signOut, loading } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  if (!user) return <div>Please log in</div>;
  
  return <div>Welcome, {user.displayName}</div>;
}
```

## 🌐 API Integration

API client configured to communicate with FastAPI backend:

```typescript
import { apiFetch, apiUrl } from '@/lib/api';

// Fetch with auth token automatically included
const response = await apiFetch('/api/chat/message', {
  method: 'POST',
  body: JSON.stringify({ message: 'Hello' })
});
```

## 🎯 Key Features

### Authentication
- Email/password signup and login
- Firebase authentication
- Protected routes
- Session persistence

### Chat Interface
- Real-time messaging with AI assistant
- Message history
- Typing indicators
- Sentiment analysis

### Task Management
- Create, read, update, delete tasks
- Natural language task creation
- Task prioritization
- Due date tracking

### Personalization
- User preferences
- Theme customization (light/dark mode)
- Notification settings

### Notifications
- Real-time notification bell
- Notification history
- Dismissible alerts

## 🎨 Theming

The app supports light and dark modes with customizable colors:

```typescript
import { useTheme } from '@/contexts/ThemeProvider';

function MyComponent() {
  const { theme, setTheme } = useTheme();
  
  return (
    <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      Toggle Theme
    </button>
  );
}
```

## 📱 Responsive Design

Built with mobile-first approach using Tailwind CSS:
- Mobile (< 640px)
- Tablet (640px - 1024px)
- Desktop (> 1024px)

## 🧪 Testing

Currently no test setup. To add tests:

```bash
# Install Vitest
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Create test files
# src/components/__tests__/Button.test.tsx
```

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

Output goes to `dist/` directory.

### Docker Deployment

```bash
docker build -t coolie-assistant-frontend .
docker run -p 80:80 coolie-assistant-frontend
```

### Environment Variables for Build

```bash
docker build \
  --build-arg VITE_API_URL=https://api.example.com \
  --build-arg VITE_FIREBASE_API_KEY=xxx \
  --build-arg VITE_FIREBASE_PROJECT_ID=xxx \
  --build-arg VITE_FIREBASE_APP_ID=xxx \
  -t coolie-assistant-frontend .
```

## 🔧 Configuration

### Vite Config
- Path aliases: `@` → `client/src`, `@shared` → `shared`
- API proxy: `/api` → backend server
- Build output: `dist/public`

### Tailwind Config
- Custom theme colors (HSL variables)
- Sidebar width: 16rem
- Border radius customization

### TypeScript Config
- Strict mode enabled
- Path mapping for imports
- React JSX support

## 📚 Component Library

### UI Components (shadcn/ui)
- Button, Input, Select, Checkbox
- Dialog, Drawer, Popover
- Card, Badge, Alert
- Tabs, Accordion, Collapsible
- Toast, Tooltip, Dropdown Menu
- And 30+ more...

### Custom Components
- `AppSidebar` - Navigation
- `ChatBubble` - Message display
- `ChatInput` - Message input
- `TaskCard` - Task display
- `NotificationBell` - Notifications
- `ThemeToggle` - Theme switcher

## 🐛 Error Handling

The app includes an Error Boundary that catches unhandled errors:

```typescript
// Automatically wrapped in App.tsx
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

Shows user-friendly error message with development details in dev mode.

## 📝 Environment Variables

Create `client/src/.env` (or root `.env`):

```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_N8N_WEBHOOK_URL=http://localhost:5678/webhook
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## 🤝 Contributing

1. Create a feature branch
2. Make changes
3. Run type checking: `npm run check`
4. Build: `npm run build`
5. Submit PR

## 📄 License

MIT License - See LICENSE file

## 🆘 Troubleshooting

### Firebase not initializing
- Check `VITE_FIREBASE_*` environment variables
- Verify Firebase project is active
- Check browser console for errors

### API calls failing
- Ensure backend is running on `VITE_API_URL`
- Check CORS configuration in backend
- Verify authentication token is valid

### Styling issues
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Rebuild Tailwind: `npm run build`
- Check `tailwind.config.ts` for custom theme

## 📞 Support

For issues and questions:
- Check [API Docs](http://localhost:8000/docs)
- Review error logs in browser console
- Check `.env` configuration
- Verify Firebase/Supabase credentials
