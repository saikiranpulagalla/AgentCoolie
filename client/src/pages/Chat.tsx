import { useEffect, useRef, useState } from "react";
import { ChatBubble } from "@/components/ChatBubble";
import { TypingIndicator } from "@/components/TypingIndicator";
import { ChatInput } from "@/components/ChatInput";
import { useAuth } from "@/contexts/AuthContext";
import { useChat } from "@/contexts/ChatContext";
import { Button } from "@/components/ui/button";
import { Trash2, PlusCircle, Archive, Search, Brain, Radio, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiFetch, getApiBase } from "@/lib/api";
import { safeExternalUrl } from "@/lib/safeExternalUrl";

const WEBHOOK_URL = import.meta.env.VITE_CLIENT_WEBHOOK_URL || `${getApiBase()}/api/webhook/proxy`;

const debugLog = (...args: unknown[]) => {
  if (import.meta.env.DEV) {
    console.debug(...args);
  }
};

export default function Chat() {
  const { user, getIdToken } = useAuth();
  const {
    messages,
    addMessage,
    clearMessages,
    isTyping,
    setIsTyping,
    conversations,
    newConversation,
    ensureConversation,
    updateConversationTitle,
    loadConversation,
    deleteConversation,
    currentConversationId,
  } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastYoutubeByConversationRef = useRef<Record<string, { url: string; title?: string; channel?: string }>>({});
  const [error, setError] = useState<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<string>).detail;
      if (detail) setError(detail);
    };
    window.addEventListener("agentcoolie:plan-limit", handler);
    return () => window.removeEventListener("agentcoolie:plan-limit", handler);
  }, []);

  const deleteConversationMemory = async (conversationId: string) => {
    try {
      const response = await apiFetch(`/api/chat/conversations/${encodeURIComponent(conversationId)}/memory`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body?.detail || "Failed to delete remote chat memory.");
      }
      return true;
    } catch (e) {
      console.warn('Failed to delete remote chat memory:', e);
      return false;
    }
  };

  const recordConversationExchange = async (
    conversationId: string,
    userMessage: string,
    assistantMessage: string,
  ) => {
    try {
      await apiFetch(`/api/chat/conversations/${encodeURIComponent(conversationId)}/memory/exchange`, {
        method: 'POST',
        body: JSON.stringify({ userMessage, assistantMessage }),
      });
    } catch (e) {
      console.warn('Failed to record chat-scoped memory:', e);
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    const deletedRemote = await deleteConversationMemory(conversationId);
    if (!deletedRemote) {
      setError("Could not delete this chat from the server. Please try again.");
      return;
    }
    delete lastYoutubeByConversationRef.current[conversationId];
    deleteConversation(conversationId);
  };

  const handleClearMessages = async () => {
    if (currentConversationId) {
      const deletedRemote = await deleteConversationMemory(currentConversationId);
      if (!deletedRemote) {
        setError("Could not clear this chat on the server. Please try again.");
        return;
      }
      delete lastYoutubeByConversationRef.current[currentConversationId];
    }
    clearMessages();
  };

  const handleSendMessage = async (content: string) => {
    // ChatInput may send structured payloads (JSON) containing message and attachments.
    let messageText = content;
    let attachments: any = undefined;

    try {
      const parsed = JSON.parse(content);
      if (parsed && typeof parsed === 'object' && 'message' in parsed) {
        messageText = String(parsed.message ?? "");
        attachments = parsed.attachments;
      }
    } catch (e) {
      // not JSON; treat content as plain text
    }

    const makeChatTitle = (text: string) => {
      const cleaned = text
        .replace(/\s+/g, " ")
        .replace(/^[^\w]+|[^\w?!.]+$/g, "")
        .trim();
      if (!cleaned) return "New chat";
      const words = cleaned.split(" ").slice(0, 7).join(" ");
      return words.length > 42 ? `${words.slice(0, 39).trim()}...` : words;
    };

    const targetConversationId = ensureConversation(makeChatTitle(messageText));
    if (messages.length === 0) {
      updateConversationTitle(targetConversationId, makeChatTitle(messageText));
    }

    const shouldTryVideoQuickPath = (() => {
      if (!messageText || typeof messageText !== 'string') return false;
      const t = messageText.trim().toLowerCase();
      if (!t) return false;
      if (lastYoutubeByConversationRef.current[targetConversationId] && /\b(play|open|watch)\s+(it|that)\b/.test(t)) return true;
      if (/youtube\.com|youtu\.be/.test(t)) return true;
      return /\b(open|play|show|find|search|watch)\b/.test(t) && /\b(video|youtube|song|trailer|clip)\b/.test(t);
    })();

    const openUrlInNewTab = (url: string, preOpenedWindow?: Window | null): "new-tab" | "unknown" => {
      const safeUrl = safeExternalUrl(url);
      if (!safeUrl) return "unknown";
      try {
        if (preOpenedWindow && !preOpenedWindow.closed) {
          try { preOpenedWindow.opener = null; } catch (e) { /* ignore opener hardening errors */ }
          preOpenedWindow.location.href = safeUrl;
          try { preOpenedWindow.focus(); } catch (e) { /* ignore focus errors */ }
          return "new-tab";
        }
        // Passing "noopener" as a feature can make Chromium return null even
        // when the tab opens. Use a normal open, then harden opener manually.
        const w = window.open(safeUrl, '_blank');
        if (w) {
          try { w.opener = null; } catch (e) { /* ignore opener hardening errors */ }
          try { w.focus(); } catch (e) { /* ignore focus errors */ }
          return "new-tab";
        }
      } catch (e) {
        console.warn('window.open failed:', e);
      }
      return "unknown";
    };

    const readResponseError = async (response: Response) => {
      try {
        const body = await response.json();
        return body?.detail || body?.message || body?.error || JSON.stringify(body);
      } catch (e) {
        try {
          return await response.text();
        } catch {
          return response.statusText || "Request failed";
        }
      }
    };

    const youtubeSearchUrl = (() => {
      const cleaned = messageText
        .replace(/\b(can|could|would)\s+u\b/gi, '')
        .replace(/\b(can|could|would)\s+you\b/gi, '')
        .replace(/\b(open|play|show|find|search|watch|in|on|youtube|video)\b/gi, ' ')
        .replace(/[?!.]+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      const query = cleaned || messageText.trim();
      return `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
    })();

    if (shouldTryVideoQuickPath) {
      const t = messageText.trim().toLowerCase();
      const lastYoutubeForChat = lastYoutubeByConversationRef.current[targetConversationId];
      if (lastYoutubeForChat && /\b(play|open|watch)\s+(it|that)\b/.test(t)) {
        const openTarget = openUrlInNewTab(lastYoutubeForChat.url);
        const assistantContent = openTarget === "new-tab"
          ? `Opening ${lastYoutubeForChat.title || "the last YouTube result"} now.`
          : `I opened or attempted to open ${lastYoutubeForChat.title || "the last YouTube result"}. If it did not appear, open it here:\n\n${lastYoutubeForChat.url}`;
        addMessage({
          id: Date.now().toString(),
          content: messageText,
          role: "user" as const,
          timestamp: new Date(),
          attachments,
        }, targetConversationId);
        addMessage({
          id: (Date.now() + 1).toString(),
          content: assistantContent,
          role: "assistant" as const,
          timestamp: new Date(),
        }, targetConversationId);
        void recordConversationExchange(targetConversationId, messageText, assistantContent);
        setIsTyping(false);
        return;
      }

      let videoPreOpenedWindow: Window | null = null;
      try {
        videoPreOpenedWindow = window.open('about:blank', '_blank');
        if (videoPreOpenedWindow) {
          videoPreOpenedWindow.document.write('<!doctype html><title>AgentCoolie</title><body style="font-family: system-ui; padding: 24px;">Finding your video...</body>');
          videoPreOpenedWindow.document.close();
        }
      } catch (e) {
        videoPreOpenedWindow = null;
      }

      try {
        const resp = await apiFetch('/api/youtube/open', {
          method: 'POST',
          body: JSON.stringify({ query: messageText }),
        });

        if (!resp.ok) {
          const detail = await readResponseError(resp);
          if ([402, 413, 429].includes(resp.status)) {
            const assistantContent = detail || "This action is not available on your current AgentCoolie plan.";
            addMessage({
              id: Date.now().toString(),
              content: messageText,
              role: "user" as const,
              timestamp: new Date(),
              attachments,
            }, targetConversationId);
            addMessage({
              id: (Date.now() + 1).toString(),
              content: assistantContent,
              role: "assistant" as const,
              timestamp: new Date(),
            }, targetConversationId);
            void recordConversationExchange(targetConversationId, messageText, assistantContent);
            try { videoPreOpenedWindow?.close(); } catch (e) { /* ignore */ }
            setIsTyping(false);
            return;
          }
          try { videoPreOpenedWindow?.close(); } catch (e) { /* ignore */ }
        }
        
        if (resp.ok) {
          const json = await resp.json();

          // If it's a video request with high confidence, handle it
          if (json?.status === 'success' && json.isVideoRequest && json.confidence > 0.7 && json.video?.url) {
            const { video } = json;
            lastYoutubeByConversationRef.current[targetConversationId] = {
              url: video.url,
              title: video.title,
              channel: video.channel,
            };

            const openTarget = openUrlInNewTab(video.url, videoPreOpenedWindow);

            // Craft assistant message: include fallback link only when both methods indicate failure
            addMessage({
              id: Date.now().toString(),
              content: messageText,
              role: "user" as const,
              timestamp: new Date(),
              attachments,
            }, targetConversationId);
            const assistantMsg = {
              id: (Date.now() + 1).toString(),
              content: openTarget === "new-tab"
                ? `I found a video that matches your request.\n\nTitle: ${video.title}\nChannel: ${video.channel}\n\nI've opened it in a new tab for you.`
                : `I found a video that matches your request.\n\nTitle: ${video.title}\nChannel: ${video.channel}\n\nI opened or attempted to open it in a new tab. If it did not appear, open it here:\n\n${video.url}`,
              role: 'assistant' as const,
              timestamp: new Date(),
            };

            addMessage(assistantMsg, targetConversationId);
            void recordConversationExchange(targetConversationId, messageText, assistantMsg.content);
            setIsTyping(false);
            // Stop further processing (don't send webhook) since we've handled the video
            return;
          }

          const openTarget = openUrlInNewTab(youtubeSearchUrl, videoPreOpenedWindow);
          const assistantContent = openTarget === "new-tab"
            ? `I opened YouTube search results for your request.\n\n${youtubeSearchUrl}`
            : `I opened or attempted to open YouTube search results. If they did not appear, open them here:\n\n${youtubeSearchUrl}`;
          addMessage({
            id: Date.now().toString(),
            content: messageText,
            role: "user" as const,
            timestamp: new Date(),
            attachments,
          }, targetConversationId);
            addMessage({
              id: (Date.now() + 1).toString(),
              content: assistantContent,
              role: "assistant" as const,
              timestamp: new Date(),
            }, targetConversationId);
          void recordConversationExchange(targetConversationId, messageText, assistantContent);
          setIsTyping(false);
          return;
          
          // If we got here, either:
          // 1. Not a video request (continue with normal chat)
          // 2. Low confidence (continue with normal chat)
          // 3. No video found (continue with normal chat)
        }
      } catch (e) {
        try { videoPreOpenedWindow?.close(); } catch (closeError) { /* ignore */ }
        console.warn('YouTube/video handling failed:', e);
        // Continue with normal chat flow on error
      }
    }

    let payload: any;
    
    // Regular chat mode
    payload = {
      message: messageText,
      userName: user?.displayName || "Anonymous",
      userId: user?.uid,
      conversationId: targetConversationId,
    };

    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      role: "user" as const,
      timestamp: new Date(),
      attachments: attachments,
    };

    addMessage(userMessage, targetConversationId);
    setIsTyping(true);
    setError(null);

    try {
      // prepare request
      const hasAudio = Array.isArray(attachments) && attachments.some((a: any) => typeof a?.mime === 'string' && a.mime.startsWith('audio/'));
      const token = await getIdToken();
      const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

      const dataUrlToBlob = (dataUrl: string): Blob => {
        const [meta, base64] = dataUrl.split(',');
        const mimeMatch = /data:(.*?);base64/.exec(meta || '');
        const mime = mimeMatch?.[1] || 'application/octet-stream';
        const binStr = atob(base64 || '');
        const len = binStr.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) bytes[i] = binStr.charCodeAt(i);
        return new Blob([bytes], { type: mime });
      };

  let response: Response;
  let didSendWebhook = false;
  let data: any = null;
  let rawText: string | null = null;
      // Ensure this handler only triggers the external webhook for recent user messages
      // userMessage.timestamp was just created above so this should normally pass; this
      // protects against delayed/replicated sends where the webhook should not be invoked.
      const now = Date.now();
      const sentAt = userMessage.timestamp instanceof Date ? userMessage.timestamp.getTime() : now;
      const twoMinutes = 2 * 60 * 1000;
      if ((now - sentAt) > twoMinutes) {
        debugLog('Message too old to send to webhook (skipping)', { now, sentAt });
      } else {
      // QUICK-PATH: try website opener before sending to external webhook.
      // Only run this quick-path for explicit website-opening requests or when a URL is present.
      // This prevents generic statements from triggering site opens (e.g., "I am a student in cbit").
      const shouldTrySiteQuickPath = (() => {
        if (!messageText || typeof messageText !== 'string') return false;
        const t = messageText.trim().toLowerCase();
        if (shouldTryVideoQuickPath || /youtube\.com|youtu\.be/.test(t)) return false;
        // Quick URL checks
        if (/https?:\/\//.test(t) || /\bwww\./.test(t)) return true;
        // Explicit action phrases that indicate the user wants to open/visit a site
        const triggers = [
          'open',
          'go to',
          'visit',
          'navigate to',
          'launch',
          'open website',
          'open the website',
          'open site',
          'visit site',
          'open link'
        ];
        for (const ph of triggers) {
          if (t.includes(ph)) return true;
        }
        return false;
      })();

      let handled = false;
      if (shouldTrySiteQuickPath) {
        let sitePreOpenedWindow: Window | null = null;
        try {
          sitePreOpenedWindow = window.open('about:blank', '_blank');
          if (sitePreOpenedWindow) {
            sitePreOpenedWindow.document.write('<!doctype html><title>AgentCoolie</title><body style="font-family: system-ui; padding: 24px;">Opening the website...</body>');
            sitePreOpenedWindow.document.close();
          }
        } catch (e) {
          sitePreOpenedWindow = null;
        }
        try {
          const siteResp = await apiFetch('/api/website/open', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: messageText }),
          });
          if (!siteResp.ok) {
            const detail = await readResponseError(siteResp);
            if ([402, 413, 429].includes(siteResp.status)) {
              const assistantMsg = {
                id: (Date.now() + 1).toString(),
                content: detail || "This action is not available on your current AgentCoolie plan.",
                role: 'assistant' as const,
                timestamp: new Date(),
              };
              addMessage(assistantMsg, targetConversationId);
              void recordConversationExchange(targetConversationId, messageText, assistantMsg.content);
              try { sitePreOpenedWindow?.close(); } catch (e) { /* ignore */ }
              setIsTyping(false);
              return;
            }
            try { sitePreOpenedWindow?.close(); } catch (e) { /* ignore */ }
          }
          if (siteResp.ok) {
            const siteJson = await siteResp.json();
            // If we get any indication of success from the website endpoint, don't forward to webhook
            const success = Boolean(
              siteJson?.opened_in_system_browser ||
              siteJson?.opened ||
              siteJson?.final_url ||
              siteJson?.data?.screenshot_url
            );
            
            if (success) {
              handled = true;
              // If the server returned a final URL, open it in the user's browser (client-side).
              // Never redirect the app's current tab as a popup fallback; that can double-open
              // in browsers that partially allow window.open and makes the chat page disappear.
              if (siteJson?.final_url) {
                const openTarget = openUrlInNewTab(siteJson.final_url, sitePreOpenedWindow);
                const assistantMsg = {
                  id: (Date.now() + 1).toString(),
                  content: `I found the website you're looking for.\n\n${
                    siteJson?.data?.title 
                      ? `Title: ${siteJson.data.title}\n` 
                      : ''
                  }${
                    siteJson?.data?.description 
                      ? `Description: ${siteJson.data.description}\n` 
                      : ''
                  }\n${openTarget === "new-tab" ? "I've opened it in a new tab for you." : "I opened or attempted to open it in a new tab. If it did not appear, open it here:"} ${siteJson.final_url}`,
                  role: 'assistant' as const,
                  timestamp: new Date(),
                };
                addMessage(assistantMsg, targetConversationId);
                void recordConversationExchange(targetConversationId, messageText, assistantMsg.content);
                setIsTyping(false);
                return; // handled - don't forward to webhook
              }
              try { sitePreOpenedWindow?.close(); } catch (e) { /* ignore */ }
              // If the tool returned a screenshot URL, show a message with link
              if (siteJson?.data?.screenshot_url) {
                const assistantMsg = {
                  id: (Date.now() + 1).toString(),
                  content: `I found and captured the website for you.\n\n${
                    siteJson?.data?.title 
                      ? `Title: ${siteJson.data.title}\n` 
                      : ''
                  }${
                    siteJson?.data?.description 
                      ? `Description: ${siteJson.data.description}\n` 
                      : ''
                  }\nHere's a screenshot of the page: ${siteJson.data.screenshot_url}`,
                  role: 'assistant' as const,
                  timestamp: new Date(),
                };
                addMessage(assistantMsg, targetConversationId);
                void recordConversationExchange(targetConversationId, messageText, assistantMsg.content);
                setIsTyping(false);
                return; // handled
              }
            }
          }
          try { sitePreOpenedWindow?.close(); } catch (e) { /* ignore */ }
        } catch (e) {
          try { sitePreOpenedWindow?.close(); } catch (closeError) { /* ignore */ }
          // ignore and fall back to webhook forwarding
          console.warn('Website quick-path failed:', e);
        }

        // Don't proceed with webhook if website was handled successfully
        if (handled) {
          setIsTyping(false);
          return;
        }
      }

      if (hasAudio) {
        const form = new FormData();
        form.append('message', messageText);
        form.append('conversationId', targetConversationId);
        if (user?.uid) form.append('userId', String(user.uid));
        if (user?.displayName) form.append('userName', String(user.displayName));

        // attach files: send all attachments as files for consistency
        if (Array.isArray(attachments)) {
          attachments.forEach((a: any, idx: number) => {
            try {
              if (typeof a?.url === 'string' && a.url.startsWith('data:')) {
                const blob = dataUrlToBlob(a.url);
                const file = new File([blob], a?.name || `attachment-${idx}`, { type: a?.mime || blob.type || 'application/octet-stream' });
                form.append('files', file, file.name);
              } else if (typeof a?.url === 'string') {
                // Non data-URL; include as JSON field for server to fetch if needed
                form.append(`attachment_${idx}_url`, a.url);
                if (a?.mime) form.append(`attachment_${idx}_mime`, a.mime);
                if (a?.name) form.append(`attachment_${idx}_name`, a.name);
              }
            } catch (e) {
              console.warn('Failed to append attachment', {
                hasName: Boolean(a?.name),
                type: a?.type,
                error: e,
              });
            }
          });
        }

        debugLog("Sending multipart webhook POST", {
          url: WEBHOOK_URL,
          attachmentCount: Array.isArray(attachments) ? attachments.length : 0,
        });
        response = await fetch(WEBHOOK_URL, {
          method: 'POST',
          headers: authHeaders,
          body: form,
        });
        didSendWebhook = true;
      } else {
        const jsonPayload: any = {
          message: messageText,
          userId: user?.uid,
          userName: user?.displayName || "Anonymous",
          conversationId: targetConversationId,
          attachments: attachments ?? undefined,
        };

        debugLog("Sending JSON webhook POST", {
          url: WEBHOOK_URL,
          hasAttachments: Array.isArray(attachments) && attachments.length > 0,
          attachmentCount: Array.isArray(attachments) ? attachments.length : 0,
        });
        response = await fetch(WEBHOOK_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify(jsonPayload),
        });
        didSendWebhook = true;
      }
    }

      if (!didSendWebhook) {
        // No webhook was sent (message was too old); treat as no response
        data = null;
        rawText = null;
      } else {
        // We did send a webhook and have a response object
        if (!response!) {
          // defensive: if response is somehow missing, treat as no content
          data = null;
          rawText = null;
        } else {
          if (!response!.ok) {
            let errorBody: string | undefined;
            try {
              const json = await response!.json();
              errorBody = json?.detail || json?.message || json?.error || JSON.stringify(json);
            } catch (e) {
              try {
                errorBody = await response!.text();
              } catch (e) {
                errorBody = undefined;
              }
            }
            throw new Error(errorBody || `Request failed with status ${response!.status}`);
          }

          // Try to read response as text first, then parse JSON if possible.
          try {
            rawText = await response!.text();
            try {
              data = rawText ? JSON.parse(rawText) : rawText;
            } catch (e) {
              data = rawText;
            }
          } catch (e) {
            console.warn('Failed to read response body', e);
            data = null;
            rawText = null;
          }
        }
      }

      // Derive assistant content from common fields or fallbacks
      let assistantContent = "I received your message!";
      let assistantModel: string | undefined = undefined;

      // helper to extract message string from an object, including nested JSON strings
      const extractText = (obj: any): string | null => {
        if (obj === null || obj === undefined) return null;
        // if it's a string that looks like JSON, try parse it
        if (typeof obj === 'string') {
          const s = obj.trim();
          if (!s) return null;
          if ((s.startsWith('{') && s.endsWith('}')) || (s.startsWith('[') && s.endsWith(']'))) {
            try {
              const parsed = JSON.parse(s);
              return extractText(parsed);
            } catch (e) {
              return s;
            }
          }
          return s;
        }
        if (typeof obj === 'object') {
          // common fields
          const keys = ['output', 'response', 'message', 'reply', 'text', 'result', 'answer', 'body', 'data'];
          // try direct keys (case-sensitive)
          for (const k of keys) {
            const v = obj[k];
            if (typeof v === 'string' && v.trim()) return v.trim();
            if (Array.isArray(v) && v.length > 0) {
              const first = v[0];
              const extracted = extractText(first);
              if (extracted) return extracted;
            }
          }
          // try case-insensitive keys
          const lowerMap: Record<string, any> = {};
          for (const kk of Object.keys(obj)) {
            lowerMap[kk.toLowerCase()] = (obj as any)[kk];
          }
          for (const k of keys) {
            const v = lowerMap[k.toLowerCase()];
            if (typeof v === 'string' && v.trim()) return v.trim();
            if (Array.isArray(v) && v.length > 0) {
              const first = v[0];
              const extracted = extractText(first);
              if (extracted) return extracted;
            }
          }
          // OpenAI-like
          const choices = obj.choices;
          if (Array.isArray(choices) && choices.length > 0) {
            const first = choices[0];
            const textFromChoice = first?.text || first?.message?.content || first?.delta?.content || first?.output?.text;
            if (typeof textFromChoice === 'string' && textFromChoice.trim()) return textFromChoice.trim();
            const deep = extractText(first);
            if (deep) return deep;
          }
          // also if object looks like an array-like container (has 0 key)
          if ('0' in obj) {
            const maybe = (obj as any)[0];
            const deep = extractText(maybe);
            if (deep) return deep;
          }
        }
        return null;
      };

      // If response is an array like [{"output":"..."}] or ['{"output":"..."}'] prefer the first element
      let top: any = data;
      if (Array.isArray(data) && data.length > 0) {
        const first = data[0];
        if (typeof first === 'string') {
          try {
            top = JSON.parse(first);
          } catch (e) {
            top = first;
          }
        } else {
          top = first;
        }
      }
      if (top && typeof top === 'object' && top.tool_used === 'preferences' && top.preferences) {
        try {
          const normalizedPreferences = {
            tone: top.preferences.tone,
            responseLength: top.preferences.response_length,
            formality: top.preferences.formality,
            includeEmojis: top.preferences.include_emojis,
          };
          if (user?.uid) {
            localStorage.setItem(`agentcoolie:preferences:${user.uid}`, JSON.stringify(normalizedPreferences));
          }
          window.dispatchEvent(new CustomEvent('agentcoolie:preferences-updated', {
            detail: normalizedPreferences,
          }));
        } catch (e) {
          console.warn('Failed to publish preference update:', e);
        }
      }
      const txt = extractText(top);
      if (txt) assistantContent = txt;

      // try to capture model info from various fields
      if (top && typeof top === 'object') {
        assistantModel = top.model || top.modelName || top.engine || top.provider || top.source || undefined;
        if (!assistantModel && Array.isArray(top.choices) && top.choices[0]) {
          assistantModel = top.choices[0].model || top.choices[0].engine || assistantModel;
        }
      }

  // fallback to rawText if we still don't have content
      if ((!assistantContent || assistantContent === 'I received your message!') && rawText && rawText.trim()) {
        // try JSON parse then extract
        try {
          const parsedRaw = JSON.parse(rawText);
          const candidate = extractText(Array.isArray(parsedRaw) ? parsedRaw[0] : parsedRaw);
          if (candidate) assistantContent = candidate;
          else assistantContent = String(parsedRaw);
        } catch (e) {
          // regex fallback: look for "output" or "message" fields inside rawText
          const rx = /"(?:output|message|response)"\s*:\s*"([\s\S]*?)"/i;
          const m = rx.exec(rawText);
          if (m && m[1]) {
            // unescape simple escaped quotes and newlines
            assistantContent = m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"').trim();
          } else {
            assistantContent = rawText.trim();
          }
        }
      }

      // If the webhook indicates it handled the message (e.g., handled: 'youtube'), skip adding its response
      try {
        const maybeHandled = (typeof data === 'object' && data && (data.handled || (Array.isArray(data) && data[0]?.handled))) || (typeof rawText === 'string' && rawText.includes('"handled"'));
        if (maybeHandled) {
          // If the webhook already returned the youtube video object, we prefer the client-side handling (which already showed the video)
          debugLog('Webhook response indicated handled action, skipping assistant message to avoid duplicate');
          return;
        }
      } catch (e) {
        // ignore errors in handled detection
      }

      // If we still ended up with the default message, fall back to rawText or a JSON dump so user sees something useful.
      if (assistantContent === 'I received your message!') {
        try {
          const fallback = (rawText && rawText.trim()) || (data ? JSON.stringify(data) : undefined) || (top ? JSON.stringify(top) : undefined) || '';
          if (fallback && fallback.trim()) {
            assistantContent = String(fallback).trim();
          } else {
            // final fallback: explicit empty-response note
            assistantContent = '(empty response)';
          }
        } catch (e) {
          assistantContent = '(empty response)';
        }
        debugLog('Unable to extract structured assistant text; using fallback response shape', {
          hasRawText: Boolean(rawText && rawText.trim()),
          dataType: Array.isArray(data) ? 'array' : typeof data,
          topType: Array.isArray(top) ? 'array' : typeof top,
        });
      }

      // normalize whitespace/newlines (strip trailing newlines)
      if (typeof assistantContent === 'string') {
        assistantContent = assistantContent.replace(/\n+$/g, '').trim();
      }

      const assistantMessage: any = {
        id: (Date.now() + 1).toString(),
        content: assistantContent,
        role: "assistant" as const,
        timestamp: new Date(),
      };
      if (assistantModel) assistantMessage.model = assistantModel;
      // Avoid adding noisy empty responses
      if (assistantMessage.content && assistantMessage.content !== '(empty response)') {
        addMessage(assistantMessage, targetConversationId);
      } else {
        debugLog('Filtered out empty assistant response');
      }
    } catch (err) {
      console.error("Error sending message:", err);
      const rawMessage = err instanceof Error ? err.message : String(err || "");
      const friendly = rawMessage && rawMessage !== "Failed to fetch"
        ? rawMessage
        : "Server unreachable - please check your connection and try again.";
      setError(friendly);

      const errorMessage = {
        id: (Date.now() + 1).toString(),
        content: friendly,
        role: "assistant" as const,
        timestamp: new Date(),
      };
      addMessage(errorMessage, targetConversationId);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="h-full flex app-surface relative page-enter">
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />
      <aside className="hidden xl:block w-80 border-r glass-panel p-4 z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary agent-mark flex items-center justify-center">
              <Bot className="h-5 w-5 text-primary-foreground relative z-10" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Chats</h2>
              <p className="text-xs text-muted-foreground">Conversation history</p>
            </div>
          </div>
          <Button size="sm" variant="ghost" onClick={() => newConversation()}>
            <PlusCircle className="h-4 w-4 mr-2" /> New
          </Button>
        </div>

        <div className="space-y-2 overflow-auto max-h-[70vh]">
          {conversations.length === 0 && (
            <div className="text-sm text-muted-foreground p-3">No conversations yet. Click New to start.</div>
          )}
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`flex items-center justify-between p-2 rounded-md cursor-pointer interactive-card ${currentConversationId === c.id ? 'bg-primary/10 border border-primary/20' : 'hover:bg-primary/5'}`}
              onClick={() => loadConversation(c.id)}
            >
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-md bg-primary/10 text-primary flex items-center justify-center text-sm font-medium">{c.title?.charAt(0) ?? 'A'}</div>
                <div className="text-sm">
                  <div className="font-medium truncate max-w-[180px]">{c.title || 'New chat'}</div>
                  <div className="text-xs text-muted-foreground">{new Date(c.updatedAt).toLocaleString()}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); handleDeleteConversation(c.id); }}>
                  <Archive className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        <div className="border-b bg-card/80 backdrop-blur-xl p-6 relative z-10 shadow-sm">
          <div className="max-w-4xl mx-auto flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4 min-w-0">
              <div className="h-12 w-12 rounded-lg bg-primary agent-mark flex items-center justify-center shadow-md shadow-primary/20">
                <Bot className="h-6 w-6 text-primary-foreground relative z-10" />
              </div>
              <div className="min-w-0">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-chart-2 bg-clip-text text-transparent" data-testid="text-page-title">
                  Chat with AgentCoolie
                </h1>
                <p className="text-sm text-muted-foreground">Memory-aware chat with live web search</p>
              </div>
            </div>
            <div className="flex items-center gap-4 justify-between sm:justify-end">
              <div className="hidden lg:flex items-center gap-2 text-xs">
                <span className="inline-flex items-center gap-1 rounded-md border bg-primary/10 px-2.5 py-1 text-primary">
                  <Search className="h-3.5 w-3.5" /> Web
                </span>
                <span className="inline-flex items-center gap-1 rounded-md border bg-chart-3/10 px-2.5 py-1 text-chart-3">
                  <Brain className="h-3.5 w-3.5" /> Memory
                </span>
                <span className="inline-flex items-center gap-1 rounded-md border bg-chart-4/10 px-2.5 py-1 text-chart-4">
                  <Radio className="h-3.5 w-3.5" /> Live
                </span>
              </div>
              {messages.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearMessages}
                  data-testid="button-clear-chat"
                  className="hover:bg-destructive/10 hover:text-destructive transition-all duration-300"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear Chat
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-6 relative z-10">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.length === 0 && (
              <div className="text-center py-20 animate-in fade-in slide-in-from-bottom-4 duration-700">
                <div className="mb-6 inline-flex">
                  <div className="h-20 w-20 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
                    <Bot className="h-10 w-10 text-primary soft-pulse rounded-lg" />
                  </div>
                </div>
                <h3 className="text-2xl font-semibold mb-2">Start a Conversation</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Ask AgentCoolie for current news, task planning, remembered context, or workflow help.
                </p>
                <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  <button
                    type="button"
                    onClick={() => handleSendMessage("What can you help me with?")}
                    className="p-4 rounded-xl bg-card border hover:border-primary/50 transition-all duration-300 cursor-pointer hover:shadow-lg group text-left hover-lift"
                  >
                    <p className="text-sm font-medium group-hover:text-primary transition-colors">What can you help me with?</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSendMessage("Search web for recent Tamil Nadu politics news")}
                    className="p-4 rounded-xl bg-card border hover:border-primary/50 transition-all duration-300 cursor-pointer hover:shadow-lg group text-left hover-lift"
                  >
                    <p className="text-sm font-medium group-hover:text-primary transition-colors">Search web for recent Tamil Nadu politics news</p>
                  </button>
                </div>
              </div>
            )}
            {messages.map((message) => (
              <ChatBubble
                key={message.id}
                message={message}
                userName={user?.displayName || "You"}
                userAvatar={user?.photoURL || ""}
              />
            ))}
            {isTyping && <TypingIndicator />}
            {error && (
              <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm p-4 rounded-xl backdrop-blur-xl animate-in fade-in slide-in-from-bottom-2 duration-300">
                <p className="font-medium">Connection Error</p>
                <p className="text-xs mt-1 opacity-80">{error}</p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <ChatInput 
          onSend={handleSendMessage} 
          disabled={isTyping} 
        />
      </main>
    </div>
  );
}
