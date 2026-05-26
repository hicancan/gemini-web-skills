# gemini-web skill

Claude Code skill for automating Google Gemini Web via Chrome DevTools MCP.

## Features

- **Chats**: new/existing chats, model selection (3 models x 2 thinking levels)
- **File upload**: single/multi-file via bridge pattern (works around Angular hidden input)
- **Prompts**: send prompts (Quill.js CSP-aware), read responses, stop generation
- **Post-response**: edit & resend, redo/regenerate (Longer/Shorter/Try again)
- **Notebooks**: create, add sources (files/Drive/websites/text), chat, delete

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

All flows tested end-to-end against gemini.google.com (Pro account) on 2026-05-26.

## Installation

Copy `SKILL.md` to `~/.claude/skills/gemini-web/SKILL.md` and restart Claude Code.
