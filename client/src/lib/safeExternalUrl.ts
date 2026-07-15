const LOCAL_HTTP_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

/** Normalize destinations that AgentCoolie is allowed to open outside the app. */
export function safeExternalUrl(value: unknown, allowMailto = false): string | null {
  if (typeof value !== "string" || !value.trim()) return null;

  try {
    const parsed = new URL(value.trim());
    if (parsed.protocol === "https:") return parsed.href;
    if (allowMailto && parsed.protocol === "mailto:") return parsed.href;
    if (import.meta.env.DEV && parsed.protocol === "http:" && LOCAL_HTTP_HOSTS.has(parsed.hostname)) {
      return parsed.href;
    }
  } catch {
    return null;
  }

  return null;
}

export function safeAttachmentUrl(value: unknown, mime?: unknown): string | null {
  if (typeof value !== "string") return null;
  if (value.startsWith("blob:")) return value;
  const normalizedMime = typeof mime === "string" ? mime.toLowerCase().trim() : "";
  const safeDataMime = /^(image\/(png|jpeg|gif|webp)|audio\/(webm|mpeg|ogg|wav)|application\/pdf)$/;
  if (
    safeDataMime.test(normalizedMime)
    && value.startsWith(`data:${normalizedMime};base64,`)
    && /^data:[a-z0-9/+.-]+;base64,[a-z0-9+/=\s]+$/i.test(value)
  ) {
    return value;
  }
  return safeExternalUrl(value);
}
