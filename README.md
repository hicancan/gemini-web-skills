# gemini-web skill

Claude Code skill for automating [Google Gemini Web](https://gemini.google.com) via Chrome DevTools MCP. Provides 12 tested flows covering the complete Gemini interaction lifecycle.

## Features

### Chat
- New chats with automatic Personal Intelligence disable
- Resume existing chats via sidebar or direct URL
- Model selection: 3.1 Flash-Lite / 3.5 Flash / 3.1 Pro + Standard / Extended thinking

### File Upload
- Bridge pattern bypasses Angular's hidden file input
- Single and multi-file upload (stash pattern)
- Supports any file type Gemini accepts

### Conversation
- Send prompts (Quill.js CSP-aware — uses `fill` tool)
- Read responses via accessibility tree
- Stop generation mid-response
- Edit prompt & resend (separate `textbox "Edit prompt"`)
- Redo with sub-options: Longer, Shorter, Don't personalize, Try again

### Notebooks (RAG)
- Create notebooks and add sources (files, Google Drive, websites, pasted text)
- Source-grounded Q&A
- Notebook management: rename, pin/unpin, delete

## Flows

| Flow | Description |
|------|-------------|
| A | New Chat + Personal Intelligence disable |
| B | Resume Chat (sidebar / direct URL) |
| C | Select Model + Thinking Level |
| D | Upload Files (bridge pattern) |
| E | Send Prompt & Read Response |
| F | Stop Response Mid-Generation |
| G | Edit Prompt & Resend |
| H | Redo / Regenerate |
| I | Create Notebook |
| J | Add Sources to Notebook |
| K | Chat in Notebook |
| L | Delete Notebook |

## Verified

All 12 flows tested end-to-end against `gemini.google.com` (Pro account) on 2026-05-26. Every locator string confirmed against the live DOM.

## Prerequisites

- Chrome DevTools MCP connected
- User logged into gemini.google.com
- Files to upload exist on local disk

## Installation

```bash
mkdir -p ~/.claude/skills/gemini-web
cp SKILL.md ~/.claude/skills/gemini-web/SKILL.md
```

Restart Claude Code or reload skills. The skill triggers on `/gemini-web` or when you ask about Gemini Web operations.

## License

MIT
