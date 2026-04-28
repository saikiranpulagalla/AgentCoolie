# CoolieAssistant - Markdown Rendering Guide

Complete guide to markdown rendering in chat messages.

---

## ✨ What's Supported

The ChatBubble component now renders markdown with the following features:

### **Bold Text**
```
**bold text** or __bold text__
```
Renders as: **bold text**

### **Italic Text**
```
*italic text* or _italic text_
```
Renders as: *italic text*

### **Code**
```
`inline code`
```
Renders as: `inline code` (with background styling)

### **Links**
```
[Link text](https://example.com)
```
Renders as: [Link text](https://example.com) (clickable, opens in new tab)

### **Automatic URL Detection**
```
https://example.com
```
Renders as: https://example.com (clickable link)

### **Headers**
```
# Header 1
## Header 2
### Header 3
```
Renders with appropriate sizes and bold styling

### **Lists**
```
- Item 1
- Item 2
- Item 3

or

* Item 1
* Item 2
* Item 3
```
Renders as bullet list with proper indentation

### **Paragraphs**
Regular text is automatically wrapped in paragraphs with proper spacing

---

## 🎯 Examples

### Example 1: Task Creation Response
```
**Task Created!** ✓

I've created a task for you:
- **Title:** Call mom
- **Due Date:** Tomorrow at 3 PM
- **Priority:** Medium

Would you like me to set a reminder?
```

Renders as:
- **Task Created!** ✓ (bold)
- Regular paragraph
- Bullet list with bold items
- Regular paragraph

### Example 2: Feature Explanation
```
## How to Use Tasks

You can create tasks in several ways:

1. **Direct Creation:** Say "Create a task to..."
2. **From Messages:** I'll extract tasks from your messages
3. **From Emails:** Important emails become tasks

Here's an example: `Create a task to buy groceries`

For more info, visit: https://example.com/tasks
```

Renders as:
- Header 2
- Paragraph
- Numbered list with bold items
- Paragraph with inline code
- Paragraph with automatic link

### Example 3: Mixed Formatting
```
**Important:** Please read this carefully!

Here are the key points:
- Use **bold** for emphasis
- Use *italic* for secondary emphasis
- Use `code` for technical terms
- Use [links](url) for references

For questions, contact: support@example.com
```

---

## 🔧 Implementation Details

### How It Works

1. **Block-level parsing** - Content is split into lines
2. **Line classification** - Each line is classified as header, list, or paragraph
3. **Inline parsing** - Within each line, inline elements are parsed
4. **React rendering** - Elements are converted to React components

### Supported Patterns

| Pattern | Regex | Type |
|---------|-------|------|
| Bold | `**text**` or `__text__` | Inline |
| Italic | `*text*` or `_text_` | Inline |
| Code | `` `text` `` | Inline |
| Link | `[text](url)` | Inline |
| URL | `https://...` | Inline |
| Header 1 | `# text` | Block |
| Header 2 | `## text` | Block |
| Header 3 | `### text` | Block |
| List | `- item` or `* item` | Block |
| Paragraph | Regular text | Block |

### Styling

All markdown elements are styled with Tailwind CSS:

- **Bold:** `font-bold`
- **Italic:** `italic`
- **Code:** `bg-muted px-1.5 py-0.5 rounded text-sm font-mono`
- **Links:** `text-primary underline hover:text-primary/80`
- **Headers:** Appropriate font sizes and bold styling
- **Lists:** `list-disc list-inside my-2 space-y-1`

---

## 🚀 Usage in System Prompts

The system prompts can now use markdown formatting:

```python
SYSTEM_PROMPT = """You are CoolieAssistant...

## Your Core Purpose
- Help users create, organize, and track tasks
- Provide intelligent responses to user queries
- Extract actionable tasks from natural language

## How to Respond
- Be concise and actionable
- Use **bold** for emphasis
- Use `code` for technical terms
- Use [links](url) for references
"""
```

---

## 📝 Best Practices

### Do's ✅
- Use **bold** for important information
- Use *italic* for secondary emphasis
- Use `code` for technical terms or commands
- Use lists for multiple items
- Use headers to organize content
- Use links for references

### Don'ts ❌
- Don't overuse bold or italic
- Don't nest formatting (e.g., `**_text_**`)
- Don't use markdown for simple text
- Don't create deeply nested lists
- Don't use headers for regular text

### Examples

**Good:**
```
**Task Created!**

I've created a task:
- **Title:** Call mom
- **Due:** Tomorrow at 3 PM
- **Priority:** Medium
```

**Bad:**
```
***TASK CREATED!!!***

I've created a task:
- Title: Call mom
- Due: Tomorrow at 3 PM
- Priority: Medium
```

---

## 🔍 Testing Markdown

### Test in Chat

Send these messages to test markdown rendering:

1. **Test Bold:**
   ```
   This is **bold** text
   ```

2. **Test Italic:**
   ```
   This is *italic* text
   ```

3. **Test Code:**
   ```
   Use `npm run dev` to start
   ```

4. **Test Links:**
   ```
   Visit [our website](https://example.com)
   ```

5. **Test Lists:**
   ```
   Here are the steps:
   - First step
   - Second step
   - Third step
   ```

6. **Test Headers:**
   ```
   # Main Title
   ## Subtitle
   ### Details
   ```

---

## 🐛 Troubleshooting

### Markdown Not Rendering

**Check 1: Syntax**
- Ensure markdown syntax is correct
- Check for typos in markers (`**`, `*`, etc.)

**Check 2: Browser Cache**
- Clear browser cache (Ctrl+Shift+Delete)
- Refresh page (Ctrl+R)

**Check 3: Frontend Restart**
- Restart frontend: `npm run dev`
- Check browser console for errors

### Partial Rendering

**Issue:** Some markdown renders, some doesn't

**Solution:**
- Check for nested formatting
- Verify syntax is correct
- Check for special characters

### Styling Issues

**Issue:** Markdown renders but styling looks wrong

**Solution:**
- Check Tailwind CSS is loaded
- Verify CSS classes are applied
- Check browser DevTools for CSS conflicts

---

## 📊 Markdown Support Matrix

| Feature | Status | Notes |
|---------|--------|-------|
| Bold | ✅ | `**text**` or `__text__` |
| Italic | ✅ | `*text*` or `_text_` |
| Code | ✅ | `` `text` `` |
| Links | ✅ | `[text](url)` |
| URLs | ✅ | Automatic detection |
| Headers | ✅ | `#`, `##`, `###` |
| Lists | ✅ | `-` or `*` |
| Blockquotes | ❌ | Not yet supported |
| Tables | ❌ | Not yet supported |
| Images | ❌ | Use attachments instead |
| Strikethrough | ❌ | Not yet supported |
| Horizontal Rule | ❌ | Not yet supported |

---

## 🚀 Future Enhancements

Potential markdown features to add:

- [ ] Blockquotes: `> quote`
- [ ] Strikethrough: `~~text~~`
- [ ] Horizontal rules: `---`
- [ ] Inline HTML: `<span>text</span>`
- [ ] Emoji support: `:smile:`
- [ ] Syntax highlighting for code blocks
- [ ] Tables: `| col1 | col2 |`
- [ ] Task lists: `- [ ] task`

---

## 📚 Related Documentation

- **ChatBubble.tsx** - Component implementation
- **SYSTEM_PROMPTS.md** - System prompt documentation
- **TESTING_GUIDE.md** - Testing guide

---

**Last Updated:** April 28, 2026  
**Version:** 2.0.0
