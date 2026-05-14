import { useEffect, useState } from "react";
import { TaskCard } from "@/components/TaskCard";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Mail, AlertCircle, CheckCircle2, Play, Globe, PhoneCall } from "lucide-react";
import type { Task } from "@shared/schema";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { useNotification } from "@/contexts/NotificationContext";
import { apiFetch, apiUrl } from "@/lib/api";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";

const debugLog = (...args: unknown[]) => {
  if (import.meta.env.DEV) {
    console.debug(...args);
  }
};

const toTaskType = (value: unknown): Task["type"] => {
  const raw = String(value || "reminder").toLowerCase();
  if (raw === "general" || raw === "task") return "reminder";
  if (raw === "gmail" || raw === "whatsapp" || raw === "youtube" || raw === "website" || raw === "reminder") {
    return raw;
  }
  return "reminder";
};

const toPriority = (value: unknown): Task["priority"] => {
  const raw = String(value || "medium").toLowerCase();
  return raw === "low" || raw === "medium" || raw === "high" ? raw : "medium";
};

const toTaskStatus = (value: unknown): Task["status"] => {
  const raw = String(value || "pending").toLowerCase();
  return raw === "pending" || raw === "calling" || raw === "sent" || raw === "missed_offline" || raw === "failed"
    ? raw
    : "pending";
};

const reminderRowToTask = (row: any, fallbackCreatedAt: Date = new Date()): Task => ({
  id: row.id,
  title: String(row.message || "").slice(0, 40) || "Reminder",
  description: row.message,
  type: toTaskType(row.type),
  priority: toPriority(row.priority),
  completed: row.status === "sent",
  status: toTaskStatus(row.status),
  executionMessage: row.execution_message,
  lastAttemptAt: row.last_attempt_at ? new Date(row.last_attempt_at) : undefined,
  notifyByCall: Boolean(row.notify_by_call),
  callStatus: row.call_status,
  callErrorCode: row.call_error_code,
  dueDate: row.datetime ? new Date(row.datetime) : undefined,
  createdAt: row.created_at ? new Date(row.created_at) : fallbackCreatedAt,
});

export default function Tasks() {
  const [filter, setFilter] = useState<"all" | "gmail" | "reminder" | "youtube" | "website">("all");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const { user, getIdToken } = useAuth();
  const { toast } = useToast();
  const { addNotification } = useNotification();

  useEffect(() => {
    // Only fetch reminders if user is authenticated
    if (!user) {
      debugLog('No user authenticated, skipping reminder fetch');
      setLoading(false);
      return;
    }

    debugLog('User authenticated, fetching reminders');
    setLoading(true);
    setTasks([]);
    const cacheKey = `cached_reminders_${user.uid}`;
    try {
      const legacy = localStorage.getItem('cached_reminders');
      if (legacy) {
        localStorage.removeItem('cached_reminders');
      }
    } catch (e) {
      // ignore storage errors
    }
    
    // fetch reminders
    (async () => {
      try {
        // hydrate from cache first (per-user)
        try {
          const cached = localStorage.getItem(cacheKey);
          debugLog('Cached reminder data found:', Boolean(cached));
          if (cached) {
            const parsed = JSON.parse(cached) as any[];
            debugLog('Parsed cached reminder count:', Array.isArray(parsed) ? parsed.length : 0);
            if (Array.isArray(parsed) && parsed.length > 0) {
              debugLog('Loading cached reminders:', parsed.length);
              const cachedTasks = parsed.map((d, i) => reminderRowToTask(
                { ...d, id: d.id || `${d.created_at || d.createdAt || Date.now()}-${i}` },
                new Date(d.created_at || d.createdAt || Date.now()),
              ));
              debugLog('Mapped cached task count:', cachedTasks.length);
              setTasks(cachedTasks);
            } else {
              debugLog('No cached reminders found or empty array');
            }
          } else {
            debugLog('No cached data in localStorage');
          }
        } catch (e) {
          console.warn('Failed to read cached reminders', e);
        }

        if (!getIdToken) {
          debugLog('getIdToken not available');
          return;
        }
        const token = await getIdToken();
        if (!token) {
          debugLog('No token available');
          return;
        }
        debugLog('Fetching reminders from server...');
        const resp = await apiFetch('/api/reminders', { headers: { Authorization: `Bearer ${token}` } });
        debugLog('API response status:', resp.status, resp.statusText);
        if (!resp.ok) {
          const text = await resp.text().catch(() => '');
          console.warn('/api/reminders failed', resp.status, resp.statusText);
          debugLog('/api/reminders error body length:', text.length);
          // Keep existing tasks instead of wiping them on transient errors
          return;
        }
        const data = await resp.json().catch((e) => {
          console.error('Failed to parse /api/reminders JSON', e);
          return null;
        });
        debugLog('Reminder API returned data:', Boolean(data));
        if (!data) {
          // parsing failed or no data; leave existing tasks intact
          console.warn('No data returned from /api/reminders');
          return;
        }

        const rows = Array.isArray(data) ? data : (Array.isArray((data as any).data) ? (data as any).data : null);
        debugLog('Processed reminder row count:', Array.isArray(rows) ? rows.length : 0);
        if (!Array.isArray(rows)) {
          console.warn('Unexpected /api/reminders response shape', {
            dataType: Array.isArray(data) ? 'array' : typeof data,
          });
          // unexpected shape; do not clear existing tasks
          return;
        }

        debugLog('Received reminders from server:', rows.length);

        const mapped = rows.map((d: any, i: number) => reminderRowToTask(
          { ...d, id: d.id || `${d.created_at || d.createdAt || Date.now()}-${i}` },
          new Date(d.created_at || d.createdAt || Date.now()),
        ));

        // dedupe by id (in case of duplicates) and preserve ordering
        const map = new Map<string, Task>();
        for (const t of mapped) map.set(t.id, t);
        const final = Array.from(map.values());
        debugLog('Setting tasks count:', final.length);
        setTasks(final);
        try {
          localStorage.setItem(cacheKey, JSON.stringify(rows));
          debugLog('Cached reminders to localStorage (per-user)');
        } catch (e) {
          console.warn('Failed to cache reminders', e);
        }
      } catch (err) {
        console.error('Error fetching reminders', err);
        // keep cached tasks if fetch fails
      } finally {
        setLoading(false);
      }
    })();

    // SSE for general reminders
    let sse: EventSource | null = null;
    let isConnecting = false;
    
    const connectSSE = async () => {
      if (!user || isConnecting) return;
      isConnecting = true;
      
      try {
        const token = await getIdToken();
        if (!token) return;
        
        // Close existing connection if any
        if (sse) {
          sse.close();
          sse = null;
        }
        
        // request a short-lived connectId
        const resp = await apiFetch('/api/sse/connect', { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
        if (!resp.ok) {
          console.error('SSE connect failed:', resp.status, resp.statusText);
          return;
        }
        const body = await resp.json();
        const connectId = body.connectId;
        debugLog('SSE connecting');
        
        sse = new EventSource(apiUrl(`/api/sse/stream/${connectId}`));
        
        sse.addEventListener("reminder", (ev: any) => {
          try {
            debugLog('SSE reminder received');
            const d = JSON.parse(ev.data);
            
            // Check if we already have this reminder to avoid duplicates
            setTasks((prev) => {
              const existing = prev.find(t => t.id === d.id);
              if (existing) {
                debugLog('Duplicate reminder ignored:', d.id);
                return prev;
              }
              
              const t = reminderRowToTask(d);
              
              const map = new Map<string, Task>();
              map.set(t.id, t);
              for (const p of prev) map.set(p.id, p);
              return Array.from(map.values());
            });
            
            // show browser notification
            if (Notification.permission === "granted") {
              debugLog('Showing browser notification for reminder');
              new Notification("Reminder", { body: d.message });
            } else {
              debugLog('Browser notification permission not granted:', Notification.permission);
            }
            // show in-app toast
            toast({ title: 'Reminder', description: d.message });
            // add to notification center
            addNotification({ id: d.id, title: d.message.slice(0,40), description: d.message, type: d.type, completedAt: new Date() });
          } catch (e) {
            console.error('Error processing SSE reminder:', e);
          }
        });
        
        sse.addEventListener("error", (ev) => {
          console.error('SSE error:', ev);
        });
        
        sse.addEventListener("open", () => {
          debugLog('SSE connection opened');
        });
        
      } catch (err) {
        console.error('SSE setup failed', err);
      } finally {
        isConnecting = false;
      }
    };
    
    connectSSE();

    return () => {
      if (sse) {
        sse.close();
        sse = null;
      }
    };
  }, [user, getIdToken]);

  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');
  
  // request notification permission on mount (if not granted)
  useEffect(() => {
    if (typeof Notification !== 'undefined') {
      setNotificationPermission(Notification.permission);
      debugLog('Current notification permission:', Notification.permission);
    } else {
      debugLog('Notification API not available');
    }
  }, []);

  const requestNotificationPermission = async () => {
    debugLog('Requesting notification permission...');
    
    if (typeof Notification === 'undefined') {
      console.error('Notification API not available');
      toast({ title: 'Notifications not supported', description: 'Your browser does not support notifications.', variant: 'destructive' });
      return;
    }
    
    try {
      debugLog('Current permission before request:', Notification.permission);
      
      // Check if we can request permission
      if (Notification.permission === 'denied') {
        debugLog('Permission already denied, cannot request again');
        toast({ 
          title: 'Notifications blocked', 
          description: 'Notifications are blocked. Please enable them manually in your browser settings (click the lock icon in the address bar).', 
          variant: 'destructive' 
        });
        return;
      }
      
      const permission = await Notification.requestPermission();
      debugLog('Permission request result:', permission);
      setNotificationPermission(permission);
      
      if (permission === 'granted') {
        toast({ title: 'Notifications enabled', description: 'You will now receive browser notifications for reminders' });
        // Test notification
        new Notification('Test Notification', { 
          body: 'Notifications are now working!',
          icon: '/favicon.svg'
        });
      } else if (permission === 'denied') {
        toast({ 
          title: 'Notifications blocked', 
          description: 'Please enable notifications in your browser settings (click the lock icon in the address bar).', 
          variant: 'destructive' 
        });
      } else {
        toast({ 
          title: 'Permission request dismissed', 
          description: 'Please try again and click "Allow" when prompted.', 
          variant: 'destructive' 
        });
      }
    } catch (err) {
      console.error('Error requesting notification permission:', err);
      toast({ 
        title: 'Error', 
        description: 'Failed to request notification permission. Please enable manually in browser settings.', 
        variant: 'destructive' 
      });
    }
  };

    const openYoutubeFromTask = async (task: Task) => {
      try {
        // Try extract a YouTube URL/time from the task description
        const msg = task.description || '';
        // look for an explicit YouTube URL
        const urlRegex = /(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/[\S]+/i;
        const urlMatch = msg.match(urlRegex);
        let url: string | null = urlMatch ? urlMatch[0] : null;

        // extract time like t=123 or start=123 in URL
        const timeParamRegex = /(?:t=|start=)(\d+)(s)?/i;
        let seconds: number | null = null;
        if (url) {
          const m = url.match(timeParamRegex);
          if (m && m[1]) seconds = Number(m[1]);
        }

        // If no explicit url, call server youtube open endpoint to search
        if (!url) {
          try {
            const token = await getIdToken();
            const resp = await apiFetch('/api/youtube/open', { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ query: msg }) });
            if (resp.ok) {
              const j = await resp.json();
              url = j?.video?.url || null;
            }
          } catch (e) {
            console.warn('YouTube search failed for task open', e);
          }
        }

        // attempt to parse natural-language time like "at 1:30" or "at 90s"
        if (seconds === null) {
          const atTimeRegex = /at\s+(\d+:)?\d{1,2}(?::\d{2})?\s*(am|pm)?/i; // rough
          const m = msg.match(/at\s+(\d+:)?(\d{1,2})(?::(\d{2}))?/i);
          if (m) {
            // convert mm:ss or hh:mm:ss to seconds
            const parts = m[0].replace(/at/i, '').trim().split(':').map(p => p.replace(/[^0-9]/g, ''));
            let s = 0;
            if (parts.length === 3) s = Number(parts[0]) * 3600 + Number(parts[1]) * 60 + Number(parts[2]);
            else if (parts.length === 2) s = Number(parts[0]) * 60 + Number(parts[1]);
            else s = Number(parts[0]);
            if (!Number.isNaN(s)) seconds = s;
          }
        }

        if (url) {
          // add start time if available
          if (seconds && !/([?&])(t|start)=/.test(url)) {
            const sep = url.includes('?') ? '&' : '?';
            url = `${url}${sep}t=${seconds}s`;
          }
          // try open
          try {
            const w = window.open(url, '_blank');
            if (w) {
              try { w.opener = null; } catch (e) {}
              try { w.focus(); } catch (e) {}
            }
          } catch (e) {
            console.warn('Failed to open YouTube from task', e);
          }
        }
      } catch (e) {
        console.error('openYoutubeFromTask error', e);
      }
    };

  const handleToggle = (id: string) => {
    const task = tasks.find((t) => t.id === id);
    if (task) {
      const newStatus = task.completed ? 'pending' : 'sent';
      (async () => {
        try {
          const token = await getIdToken();
          if (!token) {
            toast({ title: 'Not signed in', description: 'Please sign in to update tasks.', variant: 'destructive' });
            return;
          }
          const resp = await apiFetch(`/api/reminders/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({
              status: newStatus,
              execution_message: newStatus === 'sent' ? 'Task manually marked complete.' : '',
              last_attempt_at: new Date().toISOString(),
            }),
          });
          const payload = await resp.json().catch(() => ({}));
          if (!resp.ok) {
            toast({
              title: 'Task update failed',
              description: payload?.detail || payload?.message || 'Could not update this task.',
              variant: 'destructive',
            });
            return;
          }

          const updatedTask = reminderRowToTask(payload, task.createdAt);
          setTasks((prev) => prev.map((item) => (item.id === id ? updatedTask : item)));
          toast({ title: 'Task updated', description: `Task ${task.title} marked ${newStatus === 'sent' ? 'complete' : 'pending'}` });
          if (newStatus === 'sent') {
            addNotification({ id: task.id, title: task.title, description: task.description, type: task.type, completedAt: new Date() });
            // If this is a YouTube task, open the video when marked sent/completed
            if (task.type === 'youtube') {
              openYoutubeFromTask(task);
            }
          }
        } catch (err) {
          console.error(err);
          toast({ title: 'Task update failed', description: 'Could not reach the server.', variant: 'destructive' });
        }
      })();
    }
  };

  const handleDelete = (id: string) => {
    (async () => {
      try {
        const token = await getIdToken();
        if (!token) {
          toast({ title: 'Not signed in', description: 'Please sign in to delete tasks.', variant: 'destructive' });
          return;
        }
        const resp = await apiFetch(`/api/reminders/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
        if (!resp.ok) {
          const payload = await resp.json().catch(() => ({}));
          toast({
            title: 'Delete failed',
            description: payload?.detail || payload?.message || 'Could not delete this task.',
            variant: 'destructive',
          });
          return;
        }
        setTasks((prev) => prev.filter((task) => task.id !== id));
        toast({ title: 'Task deleted', description: 'The task was removed from your Tasks page.' });
      } catch (err) {
        console.error(err);
        toast({ title: 'Delete failed', description: 'Could not reach the server.', variant: 'destructive' });
      }
    })();
  };

  const handleAdd = async () => {
    // Open modal handled via component state
  };

  // --- Modal form state and submit handler ---
  const [open, setOpen] = useState(false);
  const [formType, setFormType] = useState<'general' | 'gmail' | 'youtube' | 'website'>('general');
  const [formMessage, setFormMessage] = useState('');
  // Helper: format a Date to a value usable by <input type="datetime-local"> (YYYY-MM-DDTHH:mm)
  const formatForDatetimeLocal = (d: Date) => {
    const tzOffset = d.getTimezoneOffset();
    const local = new Date(d.getTime() - tzOffset * 60000);
    return local.toISOString().slice(0, 16); // drop seconds
  };

  const [formDatetime, setFormDatetime] = useState(() => formatForDatetimeLocal(new Date(Date.now() + 60000)));
  const [formEmail, setFormEmail] = useState('');
  const [notifyByCall, setNotifyByCall] = useState(false);
  const [formCallPhone, setFormCallPhone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async () => {
    const newErrors: Record<string, string> = {};
    if (!formMessage) newErrors.message = 'Message is required';
    // validate datetime
    const parsedDate = Date.parse(formDatetime);
    if (Number.isNaN(parsedDate)) newErrors.datetime = 'Please provide a valid date/time';
    // gmail validation for gmail addresses only
    if (formType === 'gmail') {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!formEmail) newErrors.email = 'Email is required for Gmail reminders';
      else if (!emailRegex.test(formEmail)) newErrors.email = 'Please provide a valid email address';
    }
    if (notifyByCall && formCallPhone.trim()) {
      const phoneRegex = /^\+[1-9]\d{7,14}$/;
      if (!phoneRegex.test(formCallPhone.trim())) {
        newErrors.callPhone = 'Call phone must be in E.164 format, e.g. +919000000000';
      }
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setErrors({});
    setSubmitting(true);
    try {
      // formDatetime is in local 'YYYY-MM-DDTHH:mm' format; parse as local and convert to ISO UTC
      const localDate = new Date(formDatetime);
      const sendType = formType;
      const payload: any = { type: sendType, message: formMessage, datetime: localDate.toISOString() };
      if (formType === 'gmail') { payload.user_email = formEmail; }
      if (notifyByCall) {
        payload.notify_by_call = true;
        if (formCallPhone.trim()) payload.call_phone = formCallPhone.trim();
      }
      const token = await getIdToken();
      const headers: any = { 'Content-Type': 'application/json' };
      if (token) headers.Authorization = `Bearer ${token}`;
      const res = await apiFetch('/api/reminders', { method: 'POST', headers, body: JSON.stringify(payload) });
      const rawText = await res.text();
      let data: any = {};
      try {
        data = rawText ? JSON.parse(rawText) : {};
      } catch (e) {
        data = { detail: rawText || res.statusText };
      }
      if (res.ok) {
        const t = reminderRowToTask(data, new Date(data.created_at || Date.now()));
        setTasks((prev) => {
          const map = new Map<string, Task>();
          map.set(t.id, t);
          for (const p of prev) map.set(p.id, p);
          return Array.from(map.values());
        });
        setOpen(false);
        // reset
        setFormMessage('');
        setFormEmail('');
        setNotifyByCall(false);
        setFormCallPhone('');
      } else {
        const errorMessage = data.detail || data.message || res.statusText || 'unknown';
        toast({ title: 'Failed to create reminder', description: errorMessage, variant: 'destructive' });
      }
    } catch (err) {
      console.error(err);
      toast({ title: 'Failed to create reminder', description: 'Could not reach the server.', variant: 'destructive' });
    } finally {
      setSubmitting(false);
    }
  };

  const visibleTasks = tasks.filter((task) => task.type !== "whatsapp");
  const filteredTasks = visibleTasks.filter((task) => {
    if (filter === "all") return true;
    return task.type === filter;
  });

  const activeTasks = filteredTasks.filter((t) => !t.completed && t.status !== "missed_offline" && t.status !== "failed");
  const completedTasks = filteredTasks.filter((t) => t.completed);
  const attentionTasks = filteredTasks.filter((t) => t.status === "missed_offline" || t.status === "failed");

  const stats = [
    {
      label: "Active Tasks",
      value: activeTasks.length,
      icon: AlertCircle,
      gradient: "from-chart-1/20 to-chart-1/10",
      iconColor: "text-chart-1",
    },
    {
      label: "Needs Review",
      value: attentionTasks.length,
      icon: AlertCircle,
      gradient: "from-amber-500/20 to-amber-600/10",
      iconColor: "text-amber-600",
    },
    {
      label: "Completed",
      value: completedTasks.length,
      icon: CheckCircle2,
      gradient: "from-chart-3/20 to-chart-3/10",
      iconColor: "text-chart-3",
    },
    {
      label: "Gmail",
      value: visibleTasks.filter((t) => t.type === "gmail").length,
      icon: Mail,
      gradient: "from-chart-2/20 to-chart-2/10",
      iconColor: "text-chart-2",
    },
    {
      label: "YouTube",
      value: visibleTasks.filter((t) => t.type === "youtube").length,
      icon: Play,
      gradient: "from-red-500/20 to-red-600/10",
      iconColor: "text-red-500",
    },
    {
      label: "Websites",
      value: visibleTasks.filter((t) => t.type === "website").length,
      icon: Globe,
      gradient: "from-chart-2/20 to-primary/10",
      iconColor: "text-primary",
    },
    {
      label: "Call Alerts",
      value: visibleTasks.filter((t) => t.notifyByCall).length,
      icon: PhoneCall,
      gradient: "from-chart-5/20 to-primary/10",
      iconColor: "text-chart-5",
    },
  ];

  return (
    <div className="h-full overflow-auto app-surface relative">
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />
      
      <div className="max-w-6xl mx-auto p-6 space-y-8 relative z-10">
        <div className="flex items-center justify-between gap-4 flex-wrap animate-in fade-in slide-in-from-top-4 duration-700">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-chart-5 to-primary bg-clip-text text-transparent mb-2" data-testid="text-page-title">
              Tasks Dashboard
            </h1>
            <p className="text-muted-foreground text-lg">
              Manage your Gmail, YouTube, website, and reminder tasks
            </p>
          </div>
          
          <AlertDialog open={open} onOpenChange={setOpen}>
            <AlertDialogTrigger asChild>
              <Button 
                data-testid="button-add-task" 
                className="bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/30 transition-all duration-300 hover:scale-105"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Task
              </Button>
            </AlertDialogTrigger>

            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Create a Task</AlertDialogTitle>
                <AlertDialogDescription>
                  Create a Gmail, YouTube, website, or general reminder task.
                </AlertDialogDescription>
              </AlertDialogHeader>

              <div className="space-y-4">
                <div>
                  <Label>Type</Label>
                  <Select onValueChange={(v) => setFormType(v as any)} value={formType}>
                    <SelectTrigger className="w-full"><SelectValue placeholder="Select type" /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="general">General</SelectItem>
                        <SelectItem value="youtube">YouTube</SelectItem>
                        <SelectItem value="website">Website</SelectItem>
                        <SelectItem value="gmail">Gmail</SelectItem>
                      </SelectContent>
                  </Select>
                  {errors.credentials && <p className="text-sm text-destructive mt-2">{errors.credentials}</p>}
                </div>
                <div>
                  <Label>Message</Label>
                  <Textarea value={formMessage} onChange={(e) => setFormMessage(e.target.value)} />
                  {errors.message && <p className="text-sm text-destructive mt-1">{errors.message}</p>}
                </div>
                <div>
                  <Label>Datetime</Label>
                  <Input type="datetime-local" value={formDatetime} onChange={(e) => setFormDatetime(e.target.value)} />
                  {errors.datetime && <p className="text-sm text-destructive mt-1">{errors.datetime}</p>}
                </div>
                <div className="rounded-lg border bg-card/60 p-4 space-y-3">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <Label htmlFor="notify-by-call" className="text-sm font-semibold">
                        Call me when due
                      </Label>
                      <p className="text-xs text-muted-foreground">
                        Uses your saved call-reminder phone from Settings unless you enter one here.
                      </p>
                    </div>
                    <Switch
                      id="notify-by-call"
                      checked={notifyByCall}
                      onCheckedChange={setNotifyByCall}
                    />
                  </div>
                  {notifyByCall && (
                    <div>
                      <Label>Optional call phone</Label>
                      <Input
                        value={formCallPhone}
                        onChange={(e) => setFormCallPhone(e.target.value)}
                        placeholder="+919000000000"
                      />
                      {errors.callPhone && <p className="text-sm text-destructive mt-1">{errors.callPhone}</p>}
                    </div>
                  )}
                </div>
              </div>

              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleSubmit} disabled={submitting || Boolean(errors.credentials)}>{submitting ? 'Creating...' : 'Create'}</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-150">
          {stats.map((stat, index) => (
            <div
              key={stat.label}
              className="relative p-4 rounded-lg bg-card border interactive-card group overflow-hidden"
              style={{ animationDelay: `${200 + index * 50}ms` }}
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} opacity-50 group-hover:opacity-70 transition-opacity duration-300`} />
              <div className="relative flex items-center gap-3">
                <stat.icon className={`h-8 w-8 ${stat.iconColor}`} />
                <div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
          <Tabs value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
            <TabsList className="bg-card/80 backdrop-blur-xl border">
              <TabsTrigger value="all" data-testid="tab-all" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary/10 data-[state=active]:to-chart-2/10">
                All ({visibleTasks.length})
              </TabsTrigger>
              <TabsTrigger value="gmail" data-testid="tab-gmail" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-chart-1/10 data-[state=active]:to-chart-2/10">
                <Mail className="h-4 w-4 mr-1" />
                Gmail ({visibleTasks.filter((t) => t.type === "gmail").length})
              </TabsTrigger>
              <TabsTrigger value="youtube" data-testid="tab-youtube" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-red-50/10 data-[state=active]:to-red-600/10">
                <Play className="h-4 w-4 mr-1" />
                YouTube ({visibleTasks.filter((t) => t.type === "youtube").length})
              </TabsTrigger>
              <TabsTrigger value="website" data-testid="tab-website" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-chart-2/10 data-[state=active]:to-primary/10">
                <Globe className="h-4 w-4 mr-1" />
                Websites ({visibleTasks.filter((t) => t.type === "website").length})
              </TabsTrigger>
              <TabsTrigger value="reminder" data-testid="tab-reminder" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-chart-4/10 data-[state=active]:to-chart-5/10">
                <AlertCircle className="h-4 w-4 mr-1" />
                Reminders ({visibleTasks.filter((t) => t.type === "reminder").length})
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {loading ? (
          <div className="text-center py-20 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500">
            <div className="mb-6 inline-flex">
              <div className="h-24 w-24 rounded-3xl bg-gradient-to-br from-primary/15 to-chart-5/15 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-chart-3"></div>
              </div>
            </div>
            <h3 className="text-2xl font-semibold mb-2">Loading tasks...</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              Please wait while we fetch your reminders and tasks.
            </p>
          </div>
        ) : activeTasks.length === 0 && completedTasks.length === 0 && attentionTasks.length === 0 ? (
          <div className="text-center py-20 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500">
            <div className="mb-6 inline-flex">
              <div className="h-24 w-24 rounded-3xl bg-gradient-to-br from-primary/15 to-chart-5/15 flex items-center justify-center">
                <CheckCircle2 className="h-12 w-12 text-chart-3" />
              </div>
            </div>
            <h3 className="text-2xl font-semibold mb-2">No tasks found</h3>
            <p className="text-muted-foreground max-w-md mx-auto mb-6">
              Create your first task to get started with organizing your work!
            </p>
            <Button
              className="bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={() => setOpen(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Task
            </Button>
          </div>
        ) : (
          <div className="space-y-8">
            {activeTasks.length > 0 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-400">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-chart-1/20 to-chart-1/10 flex items-center justify-center">
                    <AlertCircle className="h-5 w-5 text-chart-1" />
                  </div>
                  <h2 className="text-2xl font-semibold">Active Tasks</h2>
                  <span className="px-3 py-1 rounded-full bg-chart-1/10 text-chart-1 text-sm font-medium">
                    {activeTasks.length}
                  </span>
                </div>
                <div className="grid gap-4">
                  {activeTasks.map((task, index) => (
                    <div 
                      key={task.id}
                      className="animate-in fade-in slide-in-from-left duration-500"
                      style={{ animationDelay: `${450 + index * 50}ms` }}
                    >
                      <TaskCard
                        task={task}
                        onToggle={handleToggle}
                        onDelete={handleDelete}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {attentionTasks.length > 0 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-amber-500/20 to-amber-600/10 flex items-center justify-center">
                    <AlertCircle className="h-5 w-5 text-amber-600" />
                  </div>
                  <h2 className="text-2xl font-semibold">Needs Review</h2>
                  <span className="px-3 py-1 rounded-full bg-amber-500/10 text-amber-700 text-sm font-medium">
                    {attentionTasks.length}
                  </span>
                </div>
                <div className="grid gap-4">
                  {attentionTasks.map((task, index) => (
                    <div
                      key={task.id}
                      className="animate-in fade-in slide-in-from-left duration-500"
                      style={{ animationDelay: `${550 + index * 50}ms` }}
                    >
                      <TaskCard
                        task={task}
                        onToggle={handleToggle}
                        onDelete={handleDelete}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {completedTasks.length > 0 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-600">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-chart-3/20 to-chart-3/10 flex items-center justify-center">
                    <CheckCircle2 className="h-5 w-5 text-chart-3" />
                  </div>
                  <h2 className="text-2xl font-semibold">Completed</h2>
                  <span className="px-3 py-1 rounded-full bg-chart-3/10 text-chart-3 text-sm font-medium">
                    {completedTasks.length}
                  </span>
                </div>
                <div className="grid gap-4">
                  {completedTasks.map((task, index) => (
                    <div 
                      key={task.id}
                      className="animate-in fade-in slide-in-from-left duration-500"
                      style={{ animationDelay: `${650 + index * 50}ms` }}
                    >
                      <TaskCard
                        task={task}
                        onToggle={handleToggle}
                        onDelete={handleDelete}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
