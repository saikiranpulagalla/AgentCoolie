import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Bot, User } from "lucide-react";
import type { ChatMessage } from "@shared/schema";

interface ChatBubbleProps {
  message: ChatMessage;
  userName?: string;
  userAvatar?: string;
}

export function ChatBubble({ message, userName, userAvatar }: ChatBubbleProps) {
  const isUser = message.role === "user";
  const time = new Date(message.timestamp).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  const displayContent = isUser
    ? message.content
    : message.content?.replace(/\bCoolieAssistant\b/g, "AgentCoolie");

  return (
    <div
      className={cn(
        "flex gap-4 max-w-[85%] animate-in fade-in slide-in-from-bottom-2 duration-500",
        isUser ? "ml-auto flex-row-reverse" : "mr-auto"
      )}
      data-testid={`message-${message.role}-${message.id}`}
    >
      <Avatar className={cn(
        "h-10 w-10 shrink-0 shadow-lg transition-transform duration-300 hover:scale-110",
        isUser ? "border-2 border-primary/20" : "border-2 border-chart-2/20"
      )}>
        {isUser ? (
          <>
            <AvatarImage src={userAvatar} alt={userName} />
            <AvatarFallback className="bg-gradient-to-br from-primary to-chart-1 text-primary-foreground">
              <User className="h-5 w-5" />
            </AvatarFallback>
          </>
        ) : (
          <AvatarFallback className="bg-gradient-to-br from-chart-2 to-primary text-primary-foreground">
            <Bot className="h-5 w-5" />
          </AvatarFallback>
        )}
      </Avatar>
      <div className={cn("flex flex-col gap-2", isUser ? "items-end" : "items-start")}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">
            {isUser ? userName : "AgentCoolie"}
          </span>
          {/* show model badge for assistant messages when available */}
          {!isUser && (message as any).model && (
            <span className="text-xs px-2 py-0.5 rounded bg-muted/10 text-muted-foreground border">{(message as any).model}</span>
          )}
          <span className="text-xs text-muted-foreground/60" data-testid={`text-time-${message.id}`}>
            {time}
          </span>
        </div>
        <div
          className={cn(
            "rounded-2xl px-5 py-3 shadow-md transition-all duration-300 hover:shadow-lg relative overflow-hidden group",
            isUser
              ? "bg-gradient-to-br from-primary to-chart-1 text-primary-foreground rounded-tr-sm"
              : "bg-card border-2 text-foreground rounded-tl-sm"
          )}
        >
          {isUser && (
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          )}
          {!isUser && (
            <div className="absolute inset-0 bg-gradient-to-br from-chart-2/5 to-primary/5 opacity-50" />
          )}
          <div className="relative z-10">
            <div className="text-[15px] leading-relaxed whitespace-pre-wrap break-words prose prose-sm dark:prose-invert max-w-none">
                {renderMarkdown(displayContent)}
              </div>
            {message.attachments && message.attachments.length > 0 && (
              <div className="mt-3 grid grid-cols-1 gap-2">
                {message.attachments.map((a, i) => (
                  <div key={i} className="flex items-center gap-3">
                    {a.mime.startsWith('image/') ? (
                      <img src={a.url} alt={a.name} className="h-24 w-24 object-cover rounded-md border" />
                    ) : a.mime === 'application/pdf' ? (
                      <a href={a.url} target="_blank" rel="noreferrer" className="text-sm underline">
                        {a.name}
                      </a>
                    ) : a.mime.startsWith('audio/') ? (
                      <div className="flex items-center gap-2">
                        <audio controls src={a.url} className="max-w-[260px]" />
                        <span className="text-xs text-muted-foreground">{a.name}</span>
                      </div>
                    ) : (
                      <a href={a.url} target="_blank" rel="noreferrer" className="text-sm underline">
                        {a.name}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Parse and render markdown content with support for:
 * - Bold: **text** or __text__
 * - Italic: *text* or _text_
 * - Code: `text`
 * - Links: [text](url)
 * - Lists: - item or * item
 * - Headers: # Header
 */
function renderMarkdown(content: string | undefined | null) {
  if (!content) return null;

  // Split content into lines for processing
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];
  let inList = false;

  lines.forEach((line, lineIndex) => {
    const trimmedLine = line.trim();

    // Handle list items
    if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
      inList = true;
      listItems.push(trimmedLine.substring(2));
      return;
    }

    // If we were in a list and now we're not, render the list
    if (inList && !trimmedLine.startsWith('- ') && !trimmedLine.startsWith('* ')) {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`list-${lineIndex}`} className="list-disc list-inside my-2 space-y-1">
            {listItems.map((item, idx) => (
              <li key={idx} className="text-sm">
                {renderInlineMarkdown(item)}
              </li>
            ))}
          </ul>
        );
        listItems = [];
      }
      inList = false;
    }

    // Handle headers
    if (trimmedLine.startsWith('# ')) {
      elements.push(
        <h1 key={`h1-${lineIndex}`} className="text-lg font-bold my-2">
          {renderInlineMarkdown(trimmedLine.substring(2))}
        </h1>
      );
      return;
    }
    if (trimmedLine.startsWith('## ')) {
      elements.push(
        <h2 key={`h2-${lineIndex}`} className="text-base font-bold my-2">
          {renderInlineMarkdown(trimmedLine.substring(3))}
        </h2>
      );
      return;
    }
    if (trimmedLine.startsWith('### ')) {
      elements.push(
        <h3 key={`h3-${lineIndex}`} className="text-sm font-bold my-2">
          {renderInlineMarkdown(trimmedLine.substring(4))}
        </h3>
      );
      return;
    }

    // Handle empty lines
    if (!trimmedLine) {
      elements.push(<div key={`empty-${lineIndex}`} className="h-2" />);
      return;
    }

    // Handle regular paragraphs
    elements.push(
      <p key={`p-${lineIndex}`} className="my-1">
        {renderInlineMarkdown(trimmedLine)}
      </p>
    );
  });

  // Don't forget remaining list items
  if (inList && listItems.length > 0) {
    elements.push(
      <ul key="final-list" className="list-disc list-inside my-2 space-y-1">
        {listItems.map((item, idx) => (
          <li key={idx} className="text-sm">
            {renderInlineMarkdown(item)}
          </li>
        ))}
      </ul>
    );
  }

  return elements.length > 0 ? elements : content;
}

/**
 * Render inline markdown elements (bold, italic, code, links)
 */
function renderInlineMarkdown(text: string): React.ReactNode {
  if (!text) return null;

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  // Pattern to match: **bold**, __bold__, *italic*, _italic_, `code`, [link](url)
  const patterns = [
    { regex: /\*\*(.+?)\*\*/g, type: 'bold' },
    { regex: /__(.+?)__/g, type: 'bold' },
    { regex: /\*(.+?)\*/g, type: 'italic' },
    { regex: /_(.+?)_/g, type: 'italic' },
    { regex: /`(.+?)`/g, type: 'code' },
    { regex: /\[(.+?)\]\((.+?)\)/g, type: 'link' },
    { regex: /(https?:\/\/[^\s]+)/g, type: 'url' },
  ];

  // Process all patterns
  let result = text;
  
  // Handle bold
  result = result.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  result = result.replace(/__(.+?)__/g, '<strong>$1</strong>');
  
  // Handle italic (but not inside bold)
  result = result.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
  result = result.replace(/(?<!_)_(?!_)(.+?)(?<!_)_(?!_)/g, '<em>$1</em>');
  
  // Handle code
  result = result.replace(/`(.+?)`/g, '<code>$1</code>');
  
  // Handle links
  result = result.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  
  // Handle URLs
  result = result.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');

  // Convert HTML to React elements
  return <MarkdownHTML html={result} />;
}

/**
 * Component to render HTML safely as React elements
 */
function MarkdownHTML({ html }: { html: string }) {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  // Simple regex to find HTML tags
  const tagRegex = /<(\w+)(?:\s+[^>]*)?>([^<]*)<\/\1>|<a\s+href="([^"]+)"[^>]*>([^<]+)<\/a>/g;
  let match;

  while ((match = tagRegex.exec(html)) !== null) {
    // Add text before the tag
    if (match.index > lastIndex) {
      parts.push(html.substring(lastIndex, match.index));
    }

    if (match[0].startsWith('<a')) {
      // Link
      parts.push(
        <a
          key={`link-${parts.length}`}
          href={match[3]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline hover:text-primary/80"
        >
          {match[4]}
        </a>
      );
    } else if (match[1] === 'strong') {
      // Bold
      parts.push(
        <strong key={`strong-${parts.length}`} className="font-bold">
          {match[2]}
        </strong>
      );
    } else if (match[1] === 'em') {
      // Italic
      parts.push(
        <em key={`em-${parts.length}`} className="italic">
          {match[2]}
        </em>
      );
    } else if (match[1] === 'code') {
      // Code
      parts.push(
        <code
          key={`code-${parts.length}`}
          className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
        >
          {match[2]}
        </code>
      );
    }

    lastIndex = tagRegex.lastIndex;
  }

  // Add remaining text
  if (lastIndex < html.length) {
    parts.push(html.substring(lastIndex));
  }

  return <>{parts}</>;
}
