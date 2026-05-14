import { getFirebaseAuth } from "@/lib/firebase";

/**
 * API client for FastAPI backend communication
 * Endpoints: http://localhost:8000 (development) or configured VITE_API_URL
 */

export function getApiBase(): string {
  const envBase = (import.meta as any)?.env?.VITE_API_URL as string | undefined;
  // Ensure no trailing slash for consistency
  const base = envBase ? envBase.replace(/\/$/, '') : '';
  return base || "http://localhost:8000"; // default to localhost:8000
}

export function apiUrl(path: string): string {
  const base = getApiBase();
  if (!path.startsWith('/')) path = '/' + path;
  return `${base}${path}`;
}

export async function apiFetch(inputPath: string, init?: RequestInit): Promise<Response> {
  const url = apiUrl(inputPath);

  // Add Firebase auth token if available
  const headers = new Headers(init?.headers || {});
  headers.set("Content-Type", "application/json");

  try {
    const auth = getFirebaseAuth();
    const token = await auth?.currentUser?.getIdToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  } catch (e) {
    // Continue without auth; protected routes will return 401.
  }

  const request: RequestInit = {
    ...init,
    headers,
  };

  return fetch(url, request);
}

// ============ Authentication ============

export async function verifyToken(token: string) {
  const response = await apiFetch("/api/auth/verify", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ token }),
  });
  return response.json();
}

// ============ Chat ============

export async function sendChatMessage(content: string, attachments?: any[], conversationId?: string) {
  const response = await apiFetch("/api/chat/message", {
    method: "POST",
    body: JSON.stringify({ content, attachments, conversationId }),
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function getChatHistory(limit: number = 50) {
  const response = await apiFetch(`/api/chat/history?limit=${limit}`);
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function analyzeSentiment(content: string) {
  const response = await apiFetch("/api/chat/analyze-sentiment", {
    method: "POST",
    body: JSON.stringify({ content }),
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

// ============ Tasks ============

export async function createTask(taskData: {
  title: string;
  description?: string;
  type: "general" | "gmail" | "whatsapp" | "reminder" | "youtube";
  priority?: "low" | "medium" | "high";
  due_date?: string;
}) {
  const response = await apiFetch("/api/tasks", {
    method: "POST",
    body: JSON.stringify(taskData),
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function createTaskFromText(text: string) {
  const response = await apiFetch("/api/tasks/from-text", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function getTasks() {
  const response = await apiFetch("/api/tasks");
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function getTask(taskId: string) {
  const response = await apiFetch(`/api/tasks/${taskId}`);
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function updateTask(taskId: string, updates: Record<string, any>) {
  const response = await apiFetch(`/api/tasks/${taskId}`, {
    method: "PUT",
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function deleteTask(taskId: string) {
  const response = await apiFetch(`/api/tasks/${taskId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

// ============ WhatsApp ============

export async function sendWhatsappMessage(to: string, message: string) {
  const response = await apiFetch("/api/whatsapp/send", {
    method: "POST",
    body: JSON.stringify({ to, message }),
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

// ============ Gmail ============

export async function processEmail(emailData: {
  email_id: string;
  subject: string;
  body: string;
  from: string;
}) {
  const response = await apiFetch("/api/gmail/process-email", {
    method: "POST",
    body: JSON.stringify(emailData),
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function authorizeGmail() {
  const response = await apiFetch("/api/gmail/oauth/authorize", {
    method: "POST",
  });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

// ============ Health Check ============

export async function healthCheck() {
  const response = await apiFetch("/health");
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}


