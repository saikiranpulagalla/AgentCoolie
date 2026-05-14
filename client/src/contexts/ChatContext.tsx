import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ChatMessage } from "@shared/schema";

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

// Fallback loader: scan localStorage for any matching conversation keys and return the first non-empty
function scanAnyStoredConversations(): Conversation[] {
  try {
    const keys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(STORAGE_PREFIX + ':')) keys.push(k);
    }
    // try keys in insertion order; prefer the last one set by iterating reverse
    for (let i = keys.length - 1; i >= 0; i--) {
      const raw = localStorage.getItem(keys[i]);
      if (!raw) continue;
      try {
        const parsed = JSON.parse(raw) as Conversation[];
        if (Array.isArray(parsed) && parsed.length > 0) return parsed.map((c) => ({ ...c }));
      } catch (e) {
        // ignore parse errors and continue
        continue;
      }
    }
    return [];
  } catch (e) {
    console.warn('Failed to scan localStorage for conversations', e);
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
  const currentConversationIdRef = useRef<string | null>(null);

  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    currentConversationIdRef.current = currentConversationId;
  }, [currentConversationId]);

  // Load conversations for the current user when user changes (or on mount for guest)
  useEffect(() => {
    try {
      // If a user just logged in, migrate any guest conversations to this user's key
      if (userId) {
        try {
          const userKey = `${STORAGE_PREFIX}:${userId}`;
          const guestKey = `${STORAGE_PREFIX}:guest`;
          const hasUser = localStorage.getItem(userKey);
          const hasGuest = localStorage.getItem(guestKey);
          if (!hasUser && hasGuest) {
            localStorage.setItem(userKey, hasGuest);
            localStorage.removeItem(guestKey);
          }
        } catch (e) {
          // ignore storage errors
        }
      }

      const loaded = loadFromStorageFor(userId ?? null);
      console.debug('ChatProvider: initializing conversations for user', userId ?? 'none', 'loadedCount', loaded.length);
      setConversations(loaded);
      const nextCurrent = loaded.length ? loaded[loaded.length - 1].id : null;
      currentConversationIdRef.current = nextCurrent;
      setCurrentConversationId(nextCurrent);
    } catch (e) {
      console.warn('Failed to initialize conversations from storage', e);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // persist when conversations or user changes
  useEffect(() => {
    saveToStorageFor(userId ?? null, conversations);
  }, [conversations, userId]);

  const newConversation = (title?: string) => {
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
        const id = targetConversationId || (typeof crypto !== 'undefined' && (crypto as any).randomUUID ? (crypto as any).randomUUID() : `${Date.now()}`);
        const now = new Date().toISOString();
        const conv: Conversation = { id, title: "New chat", messages: [message], createdAt: now, updatedAt: now };
        currentConversationIdRef.current = id;
        setCurrentConversationId(id);
        return [...prev, conv];
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
