import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ChatMessage } from "@shared/schema";
import { apiFetch } from "@/lib/api";

type Conversation = {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
};

interface ChatContextType {
  // current conversation messages (keeps compatibility with existing code)
  messages: ChatMessage[];
  addMessage: (message: ChatMessage, conversationId?: string | null) => void;
  clearMessages: () => void;
  isTyping: boolean;
  setIsTyping: (isTyping: boolean) => void;

  // conversations API
  conversations: Conversation[];
  currentConversationId: string | null;
  newConversation: (title?: string) => string; // returns id
  ensureConversation: (title?: string) => string;
  updateConversationTitle: (id: string, title: string) => void;
  loadConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const STORAGE_PREFIX = "coolie:conversations";
const debugLog = (...args: unknown[]) => {
  if (import.meta.env.DEV) {
    console.debug(...args);
  }
};

function storageKeyFor(uid?: string | null) {
  try {
    // Only trust the explicit uid from AuthContext. When not authenticated, always use 'guest'.
    const id = uid || "guest";
    return `${STORAGE_PREFIX}:${id}`;
  } catch (e) {
    return `${STORAGE_PREFIX}:guest`;
  }
}

function loadFromStorageFor(uid?: string | null): Conversation[] {
  try {
    const raw = localStorage.getItem(storageKeyFor(uid));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Conversation[];
    return parsed.map((c) => ({ ...c }));
  } catch (e) {
    console.warn("Failed to load conversations from storage:", e);
    return [];
  }
}

function saveToStorageFor(uid: string | null | undefined, conversations: Conversation[]) {
  try {
    localStorage.setItem(storageKeyFor(uid), JSON.stringify(conversations));
  } catch (e) {
    console.warn("Failed to save conversations to storage:", e);
  }
}

export function ChatProvider({
  children,
  userId,
}: {
  children: React.ReactNode;
  userId?: string | null;
}) {

  // start empty; we'll load from storage after auth state is known to avoid guest/uid race
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [loadedStorageOwner, setLoadedStorageOwner] = useState<string | null>(null);
  const currentConversationIdRef = useRef<string | null>(null);
  const activeChatLimitRef = useRef<number>(5);

  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    currentConversationIdRef.current = currentConversationId;
  }, [currentConversationId]);

  useEffect(() => {
    if (!userId) {
      activeChatLimitRef.current = 5;
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const response = await apiFetch("/api/billing/plan");
        if (!response.ok) return;
        const body = await response.json().catch(() => ({}));
        const limit = Number(body?.plan?.caps?.active_chats || 5);
        if (!cancelled && Number.isFinite(limit) && limit > 0) {
          activeChatLimitRef.current = limit;
          localStorage.setItem(`agentcoolie:active-chat-limit:${userId}`, String(limit));
        }
      } catch (e) {
        try {
          const cached = Number(localStorage.getItem(`agentcoolie:active-chat-limit:${userId}`) || "5");
          activeChatLimitRef.current = Number.isFinite(cached) && cached > 0 ? cached : 5;
        } catch {
          activeChatLimitRef.current = 5;
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  useEffect(() => {
    const handler = (event: Event) => {
      const summary = (event as CustomEvent<any>).detail;
      const limit = Number(summary?.plan?.caps?.active_chats || 0);
      if (Number.isFinite(limit) && limit > 0) {
        activeChatLimitRef.current = limit;
        if (userId) {
          localStorage.setItem(`agentcoolie:active-chat-limit:${userId}`, String(limit));
        }
      }
    };
    window.addEventListener("agentcoolie:plan-updated", handler);
    return () => window.removeEventListener("agentcoolie:plan-updated", handler);
  }, [userId]);

  // Load conversations for the current user when user changes (or on mount for guest)
  useEffect(() => {
    try {
      const owner = userId ?? "guest";
      setLoadedStorageOwner(null);
      const loaded = loadFromStorageFor(userId ?? null);
      debugLog('ChatProvider: initializing conversations', { signedIn: Boolean(userId), loadedCount: loaded.length });
      setConversations(loaded);
      const nextCurrent = loaded.length ? loaded[loaded.length - 1].id : null;
      currentConversationIdRef.current = nextCurrent;
      setCurrentConversationId(nextCurrent);
      setLoadedStorageOwner(owner);
    } catch (e) {
      console.warn('Failed to initialize conversations from storage', e);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // persist when conversations or user changes
  useEffect(() => {
    const owner = userId ?? "guest";
    if (loadedStorageOwner !== owner) return;
    saveToStorageFor(userId ?? null, conversations);
  }, [conversations, userId, loadedStorageOwner]);

  const newConversation = (title?: string) => {
    const limit = activeChatLimitRef.current || 5;
    if (conversations.length >= limit) {
      const fallbackId = currentConversationIdRef.current || conversations[conversations.length - 1]?.id || "";
      window.dispatchEvent(new CustomEvent("agentcoolie:plan-limit", {
        detail: `Your current AgentCoolie plan allows ${limit} active chats. Delete an old chat or upgrade to Autopilot.`,
      }));
      return fallbackId;
    }
    const id = (typeof crypto !== 'undefined' && (crypto as any).randomUUID ? (crypto as any).randomUUID() : `${Date.now()}`);
    const now = new Date().toISOString();
    const conv: Conversation = { id, title: title ?? "New chat", messages: [], createdAt: now, updatedAt: now };
    setConversations((prev) => [...prev, conv]);
    currentConversationIdRef.current = id;
    setCurrentConversationId(id);
    return id;
  };

  const ensureConversation = (title?: string) => {
    const existingId = currentConversationIdRef.current;
    if (existingId) return existingId;
    return newConversation(title);
  };

  const updateConversationTitle = (id: string, title: string) => {
    const cleanTitle = title.trim();
    if (!cleanTitle) return;
    setConversations((prev) => {
      const idx = prev.findIndex((c) => c.id === id);
      if (idx === -1) return prev;
      const conv = prev[idx];
      if (conv.title && conv.title !== "New chat") return prev;
      const next = [...prev];
      next[idx] = { ...conv, title: cleanTitle, updatedAt: new Date().toISOString() };
      return next;
    });
  };

  const loadConversation = (id: string) => {
    const exists = conversations.find((c) => c.id === id);
    if (!exists) return;
    currentConversationIdRef.current = id;
    setCurrentConversationId(id);
  };

  const deleteConversation = (id: string) => {
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      // if deleted current, switch to last
      if (currentConversationId === id) {
        const last = next.length ? next[next.length - 1].id : null;
        currentConversationIdRef.current = last;
        setCurrentConversationId(last);
      }
      return next;
    });
  };

  const addMessage = (message: ChatMessage, conversationId?: string | null) => {
    const targetConversationId = conversationId ?? currentConversationIdRef.current;
    setConversations((prev) => {
      let idx = prev.findIndex((c) => c.id === targetConversationId);
      // if no current conversation, create one
      if (idx === -1) {
        const limit = activeChatLimitRef.current || 5;
        if (prev.length >= limit) {
          const fallbackId = currentConversationIdRef.current || prev[prev.length - 1]?.id || null;
          window.dispatchEvent(new CustomEvent("agentcoolie:plan-limit", {
            detail: `Your current AgentCoolie plan allows ${limit} active chats. Delete an old chat or upgrade to Autopilot.`,
          }));
          if (!fallbackId) return prev;
          const fallbackIdx = prev.findIndex((c) => c.id === fallbackId);
          if (fallbackIdx === -1) return prev;
          currentConversationIdRef.current = fallbackId;
          setCurrentConversationId(fallbackId);
          idx = fallbackIdx;
        } else {
          const id = targetConversationId || (typeof crypto !== 'undefined' && (crypto as any).randomUUID ? (crypto as any).randomUUID() : `${Date.now()}`);
          const now = new Date().toISOString();
          const conv: Conversation = { id, title: "New chat", messages: [message], createdAt: now, updatedAt: now };
          currentConversationIdRef.current = id;
          setCurrentConversationId(id);
          return [...prev, conv];
        }
      }
      const conv = prev[idx];
      const updated: Conversation = { ...conv, messages: [...conv.messages, message], updatedAt: new Date().toISOString() };
      const next = [...prev];
      next[idx] = updated;
      return next;
    });
  };

  const clearMessages = () => {
    setConversations((prev) => {
      if (!currentConversationId) return prev;
      const idx = prev.findIndex((c) => c.id === currentConversationId);
      if (idx === -1) return prev;
      const conv = prev[idx];
      const updated: Conversation = { ...conv, messages: [], updatedAt: new Date().toISOString() };
      const next = [...prev];
      next[idx] = updated;
      return next;
    });
  };

  // export messages for current conversation to keep Chat.tsx compatibility
  const messages = useMemo(() => {
    const conv = conversations.find((c) => c.id === currentConversationId);
    return conv?.messages ?? [];
  }, [conversations, currentConversationId]);

  return (
    <ChatContext.Provider
      value={{
        messages,
        addMessage,
        clearMessages,
        isTyping,
        setIsTyping,

        conversations,
        currentConversationId,
        newConversation,
        ensureConversation,
        updateConversationTitle,
        loadConversation,
        deleteConversation,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
