<p align="center">
  <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" width="64" alt="Gemini">
</p>

<h1 align="center">gemini-web</h1>
<p align="center">
  <b>Claude Code Skill · Automate Google Gemini Web via MCP</b>
</p>

<p align="center">
  <a href="#-features"><img src="https://img.shields.io/badge/flows-12-blue" alt="12 flows"></a>
  <a href="#-verified"><img src="https://img.shields.io/badge/tested-2026--05--26-brightgreen" alt="tested"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"></a>
  <a href="README_CN.md"><img src="https://img.shields.io/badge/中文-README_CN-red" alt="中文"></a>
</p>

---

A [Claude Code](https://claude.ai/code) skill that fully automates [Google Gemini Web](https://gemini.google.com) through Chrome DevTools MCP. Every locator string, every state transition, every edge case — tested against the live DOM. Think of it as a programmable Gemini client that lives inside your terminal.

## Why

Gemini's web UI is a complex Angular SPA with dynamically generated elements, Quill.js CSP restrictions, hidden file inputs, and volatile UIDs. This skill handles all of that so Claude Code can drive Gemini as naturally as a human would — just faster and programmatically.

## What It Does

<table>
<tr><td width="50%">

### Chat
- New chats (auto-disable Personal Intelligence)
- Resume via sidebar or direct URL
- 3 models × 2 thinking levels

### Files
- Bridge pattern bypasses Angular's hidden `<input>`
- Single / multi-file upload (stash pattern)

</td><td width="50%">

### Conversation
- Send prompts (Quill.js CSP-aware)
- Read responses, stop mid-generation
- Edit & resend, redo (Longer / Shorter / Try again)

### Notebooks (RAG)
- Create, add sources (files, Drive, URLs, text)
- Source-grounded Q&A, rename, pin, delete

</td></tr>
</table>

## Quick Start

```bash
# Install
mkdir -p ~/.claude/skills/gemini-web
cp SKILL.md ~/.claude/skills/gemini-web/

# Use
/gemini-web                    # interactive mode
/gemini-web upload paper.pdf   # upload + ask
```

**Prerequisites:** Chrome DevTools MCP connected · logged into gemini.google.com

## Flows

| # | Flow | Turns |
|---|------|-------|
| A | New Chat + disable Personal Intelligence | 7 |
| B | Resume Chat (sidebar or URL) | 3 |
| C | Select Model + Thinking Level | 6 |
| D | Upload Files (bridge → DataTransfer) | 5 |
| E | Send Prompt & Read Response | 4 |
| F | Stop Response Mid-Generation | 3 |
| G | Edit Prompt & Resend | 5 |
| H | Redo / Regenerate (with sub-options) | 3 |
| I | Create Notebook | 4 |
| J | Add Sources to Notebook | 4 |
| K | Chat in Notebook (source-grounded) | 3 |
| L | Delete Notebook | 3 |

Each "turn" is a concrete MCP tool call (`click`, `fill`, `evaluate_script`, `wait_for`, `take_snapshot`).

## Architecture

```
┌──────────────┐     MCP      ┌──────────────────┐
│  Claude Code │ ───────────→ │ Chrome DevTools   │
│  (SKILL.md)  │ ←─────────── │ (gemini.google)   │
└──────────────┘   snapshots  └──────────────────┘
       │
       ▼
  Bridge Pattern:
  upload_file → #mcp-bridge → DataTransfer → input[name="Filedata"]
```

The bridge pattern is the key innovation: Gemini's Angular creates file inputs dynamically and hides them. MCP's `upload_file` can't reach them. A visible bridge element captures the file, then JavaScript transfers it to Gemini's hidden input.

## Verified

All 12 flows tested end-to-end on **2026-05-26** against `gemini.google.com` with a **Pro** account. Every element locator confirmed against the live accessibility tree.

| Category | Validated |
|----------|-----------|
| Navigation | `/app`, `/app/<id>`, `/notebook/<uuid>`, `/notebooks/create`, `/notebooks/view` |
| Forms | `textbox "Enter a prompt for Gemini"`, `textbox "Edit prompt"`, `textbox "Name of the notebook"` |
| Buttons | `"Send message"` → `"Stop response"` → `"Send message"` state transitions |
| File upload | Bridge creation → `upload_file` → DataTransfer → chips → Send enabled |
| Response detection | `wait_for ["Good response", "Bad response"]` — reliable thumbs-up/down signal |
| Model selection | 3 models + 2 thinking levels, substring matching with `"Selected "` prefix handling |
| Notebook sources | Upload files, Drive, websites dialog (`textbox "Paste any links"`), text dialog (`textbox "Pasted text"`) |

### Bugs Found & Fixed During Testing

| Bug | Original | Fixed |
|-----|----------|-------|
| URL prefix | `c_<chat_id>` | `<chat_id>` (no prefix) |
| Model menu closure | Not documented | Reopen picker after model select |
| Menu confusion | "More tools" vs "More uploads" | Both documented with distinction |

## Related

- [Google Gemini](https://gemini.google.com) — the web UI this skill automates
- [NotebookLM](https://notebooklm.google.com) — full-featured notebook product (Gemini Notebooks link to it)
- [Claude Code](https://claude.ai/code) — the CLI that runs this skill
- [Chrome DevTools MCP](https://github.com/anthropics/claude-code) — the MCP server enabling browser automation

## License

MIT — use it, fork it, ship it.
