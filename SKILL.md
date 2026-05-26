---
name: gemini-web
description: Use when user needs Google Gemini (gemini.google.com) — upload files, ask questions, get AI responses. Handles: chats, model selection, file upload via bridge, prompts, response extraction, stop/edit/redo, notebooks (RAG), image/video generation, code import, Deep research, Canvas, Settings.
---

# Gemini Web Interface

Automates gemini.google.com via Chrome DevTools MCP. Every locator tested against live DOM. Every state transition verified.

## Prerequisites

- Chrome DevTools MCP connected
- Logged into gemini.google.com

## URL Patterns

| Action | URL |
|--------|-----|
| New chat | `https://gemini.google.com/app` |
| Specific chat | `https://gemini.google.com/app/<chat_id>` (NOT `c_<id>`) |
| Search chats | `https://gemini.google.com/search` |
| All notebooks | `https://gemini.google.com/notebooks/view` |
| Specific notebook | `https://gemini.google.com/notebook/<uuid>` |
| Create notebook | `https://gemini.google.com/notebooks/create` |

## Dynamic UIDs

Every UID changes on each page load. After ANY click or navigation, snapshot. Never cache UIDs.

## Core Elements

| Element | Locator |
|---------|---------|
| New chat | `link "New chat"` in `navigation "Main actions menu"` (Ctrl+Shift+O) |
| Textbox | `textbox "Enter a prompt for Gemini"` (Quill.js, multiline) |
| Send button | `button "Send message"` → becomes `"Stop response"` during generation |
| Upload & tools | `button "Upload & tools"` (the + button) |
| Mode picker | `button` label starts `"Open mode picker"` |
| Temporary chat | `button "Temporary chat"` (vanishes after 1st message in conversation) |
| Conversation menu | `button "Open menu for conversation actions."` (after 1st message) |
| Edit textbox | `textbox "Edit prompt"` (NOT the main textbox) |

## Complete "+" Menu Tree

```
button "Upload & tools"
└── menu "Menu options"
    ├── menu "Upload file options"
    │   ├── menuitem "Upload files. Documents, data, code files"    → opens file picker
    │   └── menuitem "Add from Drive. Sheets, Docs, Slides"        → Drive picker dialog
    ├── button "More uploads"                                       → expands submenu:
    │   └── group "More upload options"
    │       ├── menuitem "Google Photos"                            → Photos picker
    │       ├── menuitem "Avatar"                                   → likeness page
    │       ├── menuitem "Import code"                              → dialog: GitHub URL + Upload folder
    │       └── menuitem "Notebooks"                                → import from notebook
    ├── menuitemcheckbox "Create image"     → image gen mode (20 templates, Nano Banana 2)
    ├── menuitemcheckbox "Create video"     → video gen mode (18 templates, Omni, 16:9)
    ├── menuitemcheckbox "Canvas"           → coding/prototyping mode
    └── button "More tools"                 → expands submenu:
        ├── menuitemcheckbox "Deep research"
        ├── menuitemcheckbox "Create music"
        ├── menuitemcheckbox "Guided learning"
        └── switch "Personal Intelligence"  → disable for clean responses
```

**Mode toggles:** Each menuitemcheckbox toggles a mode. When active, a `button "Deselect <Mode>"` appears. Click it to exit. Create image also shows a `button "Deselect Images"`, Create video shows `button "Deselect Videos"`, Canvas shows `button "Deselect Canvas"`.

**"Import code" dialog:**
```
dialog
  heading "Import code"
  textbox "GitHub repository or branch URL"
  button "Upload folder"
  button "Import"
  button "Cancel code import"
```

## Complete Settings Menu

```
button "Settings" (bottom of sidebar, haspopup="menu")
└── menu (orientation="vertical")
    ├── menuitem "Activity"
    ├── menuitem "Personal Intelligence"
    ├── menuitem "Import memory to Gemini"
    ├── menuitem "Avatar"
    ├── menuitem "Usage Limits"
    ├── menuitem "Scheduled actions"
    ├── menuitem "Gems"
    ├── menuitem "Your public links"
    ├── menuitem "Theme"                    → submenu: System / Light / Dark (menuitemradio)
    ├── menuitem "Manage subscription"
    ├── menuitem "Upgrade to Google AI Ultra"
    ├── menuitem "NotebookLM"
    ├── menuitem "Send feedback"
    ├── menuitem "Help"                     → has submenu
    ├── menuitem "Portland, OR, USA ..."   → location indicator
    └── menuitem "Update location"
```

## Models & Thinking

Substring match — `"Selected "` prefix varies. Selecting a model closes the menu; reopen for thinking level.

| Model | Match |
|-------|-------|
| 3.1 Flash-Lite | `"Flash-Lite"` |
| 3.5 Flash | `"3.5 Flash"` |
| 3.1 Pro | `"3.1 Pro"` |

Thinking: menuitem starts with `"Thinking level"` → `"Standard"` / `"Extended"`. Default: 3.1 Pro + Extended.

## Response State Machine

| State | Button | Edit btn | Response area |
|-------|--------|----------|---------------|
| Idle | `"Send message"` enabled | N/A | N/A |
| Generating | `"Stop response"` | disabled | `generic busy` |
| Complete | `"Send message"` disabled | enabled | `live="polite"`, `button "Good response"` + `"Bad response"` |

**wait_for completion:** `["Good response", "Bad response"]` — thumbs buttons, only appear when done.

## Response Page Structure

```
heading "You said <prompt>"
  button "Copy prompt"   button "Edit"
heading "Gemini said"
  generic live="polite" → StaticText <response>
  button "Good response"   button "Bad response"
  button "Redo" → submenu: Longer / Shorter / Don't personalize / Try again
  button "Copy"   button "Show more options"
```

## Flows

### A: New Chat
```
navigate → /app → snapshot (verify textbox+sidebar)
click "Upload & tools" → snapshot → click "More tools" (NOT "More uploads")
snapshot → if switch "Personal Intelligence" checked → click to disable
Escape
```

### B: Resume Chat
```
Sidebar: navigate /app → if Recents collapsed click "Toggle Recents" → click chat link
URL: navigate /app/<chat_id>
```

### C: Model + Thinking
```
click "Open mode picker, ..." → snapshot → click model menuitem
(reopen picker — model selection closes menu)
click "Open mode picker, ..." → click "Thinking level ..." → click "Standard"/"Extended"
Escape
```

### D: File Upload (Bridge)
```
1. evaluate_script: create <input id="mcp-bridge" type="file" multiple> (idempotent)
2. snapshot → find "MCP bridge" → upload_file to bridge uid
3. click "Upload & tools" → snapshot → click "Upload files. Documents, data, code files"
   (creates input[name="Filedata"] in DOM, file picker opens — ignore it)
4. evaluate_script: DataTransfer bridge.files → input[name="Filedata"] → dispatch change event
```
Files appear as chips. Send enables ~1-2s. Multi-file: stash pattern (see below).

### E: Send & Read
```
fill textbox (must use fill — Quill.js CSP blocks evaluate_script)
click "Send message" → wait_for ["Good response", "Bad response"]
snapshot → extract text from generic live="polite" after "Gemini said"
```

### F: Stop Mid-Generation
```
wait_for ["Stop response"] → click "Stop response"
wait_for ["Good response", "Bad response", "Send message"]
```

### G: Edit & Resend
```
click "Edit" on user message → fill textbox "Edit prompt" → click "Update"
Update disabled until text differs from original.
wait_for ["Good response", "Bad response"]
```

### H: Redo
```
click "Redo" → submenu: "Longer" / "Shorter" / "Don't personalize" / "Try again"
click option → wait_for ["Good response", "Bad response"]
```

### I: Image Generation
```
click "Upload & tools" → click menuitemcheckbox "Create image"
Mode activates: 20 style templates, "Create with Nano Banana 2"
fill textbox with image description → send
Exit: click "Deselect Images"
```

### J: Video Generation
```
click "Upload & tools" → click menuitemcheckbox "Create video"
Mode activates: 18 templates, "Create with Omni", aspect ratio "Landscape (16:9)"
fill textbox with video description → send
Exit: click "Deselect Videos"
```

### K: Canvas
```
click "Upload & tools" → click menuitemcheckbox "Canvas"
Mode for coding, writing, slides.
Exit: click "Deselect Canvas"
```

### L: Import Code
```
click "Upload & tools" → click "More uploads" → click "Import code"
dialog with: textbox "GitHub repository or branch URL" + button "Upload folder" + button "Import"
```

### M: Notebooks

**Create:**
```
navigate /notebooks/create → snapshot → fill textbox "Name of the notebook"
snapshot → click unlabeled button (appears after text) → wait_for ["Add sources"]
```

**Add sources:**
```
click "Add sources" → dialog "Sources" with 4 options:
  - menuitem "Upload files. Documents, data, code files"  (bridge, same as Flow D)
  - menuitem "Add from Drive. Sheets, Docs, Slides"
  - menuitem "Add websites" → sub-dialog "Website URLs" with textbox "Paste any links"
  - menuitem "Copied text" → sub-dialog with textbox "Pasted text"
```

**Chat:** Sending prompt in a notebook redirects to /app/<chat_id>. Chat appears as `button "Navigate to a recent chat in a notebook"` in the notebook view. Without sources, it's a regular chat.

**Delete:**
```
click "Notebook settings" → click "Delete" → dialog "Delete this notebook?"
click "Delete everywhere" → redirects to /notebooks/view
```

**Notebook settings menu:** Notebook settings / Pin|Unpin / Rename / Delete

## Multi-File Upload (Stash)

upload_file replaces bridge.files each call. For N files:
```
create bridge → window._stash = []
upload file1 → window._stash = Array.from(bridge.files)
upload file2 →
  dt = new DataTransfer()
  for (f of [...stash, ...bridge.files]) dt.items.add(f)
  bridge.files = dt.files
proceed with Flow D steps 3-4. Cleanup: delete window._stash
```

## Bridge Cleanup

```
evaluate_script: document.getElementById('mcp-bridge')?.remove()
```

## Error Recovery

| Symptom | Fix |
|---------|-----|
| "Gemini input not found" | Re-click "Upload & tools" → "Upload files" |
| Send disabled after upload | Wait 2-3s, files still processing |
| Bridge empty after navigation | SPA preserves, full nav kills. Recreate. |
| Mode picker closed | Reopen (model selection auto-closes menu) |
| Menuitem not found | Substring match, not exact |
| "Update" disabled in edit | Text must differ from original |
| Wrong chat via URL | Use `/app/<id>` not `/app/c_<id>` |
| Menu click off-target | Close menus first with Escape, re-snapshot |

## Limitations

- Quill.js CSP: prompt MUST use `fill`, not evaluate_script
- Bridge dies on full-page nav; SPA nav preserves it
- upload_file replaces bridge.files; use stash for multi
- UIDs volatile: snapshot after every click
- Model menu closes on select: reopen for thinking level
- Edit uses dedicated `textbox "Edit prompt"` separate from main textbox
- Model list hardcoded; verify with snapshot if selection fails
- Temporary chat button disappears after first message in conversation
- "More uploads" submenu items (Google Photos, Avatar, Notebooks) not deeply tested
