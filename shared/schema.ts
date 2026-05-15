export type ChatMessage = {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
  // attachments: array of objects with name, mime and data URL (base64) or remote URL
  attachments?: { name: string; mime: string; url: string }[];
  // optional model identifier that produced the assistant message
  model?: string;
};

export type Task = {
  id: string;
  title: string;
  description?: string;
  type: "general" | "gmail" | "whatsapp" | "reminder" | "youtube" | "website";
  priority: "low" | "medium" | "high";
  completed: boolean;
  status?: "pending" | "calling" | "sent" | "missed_offline" | "failed";
  executionMessage?: string;
  lastAttemptAt?: Date;
  notifyByCall?: boolean;
  callStatus?: string;
  callErrorCode?: string;
  dueDate?: Date;
  createdAt: Date;
};

export type PersonalizationSettings = {
  tone: "professional" | "casual" | "friendly" | "formal";
  responseLength: "brief" | "moderate" | "detailed";
  formality: "low" | "medium" | "high";
  includeEmojis: boolean;
};

export type UserPreferences = {
  theme: "light" | "dark" | "system";
  notifications: boolean;
  language: string;
};
