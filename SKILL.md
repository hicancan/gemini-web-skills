---
name: gemini-web
description: Use when user needs Google Gemini (gemini.google.com) — upload files, ask questions, get AI responses. Handles: new/existing chats, model selection (3 models x 2 thinking levels), single/multi-file upload via bridge, prompts, response extraction, stop/edit/redo, notebooks with sources (RAG).
---

# Gemini Web Interface

Automates Google Gemini Web via Chrome DevTools MCP.

## Prerequisites

- Chrome DevTools MCP connected
- User logged into gemini.google.com
- Files to upload exist on local disk

## URL Patterns

| Action | URL |
|--------|-----|
| New chat | `https://gemini.google.com/app` |
| Specific chat | `https://gemini.google.com/app/<chat_id>` |
| Search chats | `https://gemini.google.com/search` |

Extract chat_id from sidebar recents link: `href="/app/<chat_id>"`. The link text is Gemini's auto-generated title. Do NOT use `c_` prefix — it loads a new chat, not the existing one.

## Dynamic UIDs

Every element UID changes on each page load. After ANY click or navigation, take a fresh snapshot. Never cache UIDs.

## Core Elements

| Element | Locator |
|---------|---------|
| New chat | `link "New chat"` in `navigation "Main actions menu"` (shortcut: `Ctrl+Shift+O`) |
| Recent chats | Links in expanded `button "Toggle Recents"` section |
| Textbox | `textbox "Enter a prompt for Gemini"` (Quill.js, multiline) |
| Send button | `button "Send message"` (disabled until text + uploads ready; becomes `"Stop response"` during generation) |
| Upload & tools | `button "Upload & tools"` (the "+" button near textbox) |
| Mode picker | `button` whose label starts with `"Open mode picker"` |
| Upload files menuitem | `menuitem "Upload files. Documents, data, code files"` — inside `menu "Upload file options"` |
| Conversation menu | `button "Open menu for conversation actions."` (appears after first message) |
| Temporary chat | `button "Temporary chat"` (disappears after first message in conversation) |

## Upload & Tools Menu Structure

Clicking `button "Upload & tools"` opens `menu "Menu options"` containing:

**Upload section:**
- `menu "Upload file options"`:
  - `menuitem "Upload files. Documents, data, code files"` — opens file dialog, creates `input[name="Filedata"]`
  - `menuitem "Add from Drive. Sheets, Docs, Slides"`
- `button "More uploads"` — additional upload sources (differs from `"More tools"`!)

**Creation section:**
- `menuitemcheckbox "Create image" description="Visualize and edit"`
- `menuitemcheckbox "Create video" description="Bring ideas to life"`
- `menuitemcheckbox "Canvas" description="Code, write, or make slides"`

**Tools section:**
- `button "More tools"` — expands submenu with:
  - `menuitemcheckbox "Deep research" description="Get detailed reports"`
  - `menuitemcheckbox "Create music" description="Make audio tracks"`
  - `menuitemcheckbox "Guided learning" description="Study and learn new things"`
  - `switch "Personal Intelligence"` — **must be unchecked** for clean responses

## Models & Thinking Levels

Click mode picker -> select model -> select thinking level. Use **substring matching** for all menuitems — the `"Selected "` prefix varies.

| Model | Substring to match |
|-------|--------------------|
| 3.1 Flash-Lite | `"Flash-Lite"` |
| 3.5 Flash | `"3.5 Flash"` |
| 3.1 Pro | `"3.1 Pro"` |

**Important:** Selecting a model closes the menu. To change thinking level after model selection, reopen the mode picker.

Thinking level menuitem starts with `"Thinking level"`. Submenu:
- `"Standard"` (in `"Selected Standard Best for most questions"`)
- `"Extended"` (in `"Extended Complex problem solving"`)

**Default:** 3.1 Pro + Extended unless user specifies otherwise.

Mode picker label updates to reflect selection: `"Open mode picker, currently Pro"`, `"Open mode picker, currently Flash"`, `"Open mode picker, currently Flash Extended"`, etc.

## Response Completion Detection

After sending a prompt, the UI transitions through 3 states. Use these reliable markers:

| State | Send/Stop button | Edit button | Response area | Key indicators |
|-------|-----------------|-------------|---------------|----------------|
| **Idle** | `"Send message"` (enabled when text present) | N/A | N/A | Textbox has content |
| **Generating** | `"Stop response"` | `disableable disabled` | `generic busy` | User heading appears, Gemini heading appears |
| **Complete** | `"Send message"` (disabled, empty textbox) | enabled | `live="polite"` | `button "Good response"` + `button "Bad response"` appear |

**`wait_for` pattern** (reliable, tested):
```
wait_for -> text: ["Good response", "Bad response"]
```
These are the thumbs-up/down feedback buttons that ONLY appear after generation finishes.

Alternative: wait for `"Send message"` to reappear after `"Stop response"` disappears.

## Response Page Structure

After a completed exchange (with file upload example):

```
[Page title: "<auto-title> - Google Gemini"]
button "Open menu for conversation actions."
heading "Conversation with Gemini"

[Optional: button "<filename>" — uploaded file chip]

heading "You said <prompt>"
  button "Copy prompt"
  button "Edit"              <- disabled during generation

heading "Gemini said"
  generic live="polite"
    StaticText "<response>"
  button "Good response"     <- thumbs up (wait_for target)
  button "Bad response"      <- thumbs down (wait_for target)
  button "Redo"              <- has submenu (see Flow H)
  button "Copy"
  button "Show more options"

textbox "Enter a prompt for Gemini"    <- for follow-up
button "Send message" (disabled)
StaticText "Gemini is AI and can make mistakes."
```

Chat is auto-titled by Gemini (e.g., "Test File Content Identification", "A Simple Greeting").

## Flows

### Flow A: New Chat

```
navigate_page -> https://gemini.google.com/app
take_snapshot -> verify textbox + sidebar present
```

Before starting any conversation, disable Personal Intelligence:

```
click -> button "Upload & tools"
take_snapshot -> find button "More tools" and click
                 (NOT "More uploads" — they are different buttons)
take_snapshot -> find switch "Personal Intelligence"
If checked -> click to disable
Press Escape to close menu
```

The switch must appear without `checked` attribute.

### Flow B: Resume Chat

**Sidebar (preferred):**
```
navigate_page -> https://gemini.google.com/app
If "Recents" collapsed -> click button "Toggle Recents"
take_snapshot -> click matching chat link
```

**Direct URL:**
```
navigate_page -> https://gemini.google.com/app/<chat_id>
```
Note: chat_id is used directly, NOT with `c_` prefix. `c_<chat_id>` loads a new empty chat.

### Flow C: Select Model + Thinking

```
take_snapshot -> click button whose label starts with "Open mode picker"
take_snapshot -> click model menuitem (substring match)
  NOTE: menu closes after model selection — reopen for thinking level
take_snapshot -> click button "Open mode picker" again
take_snapshot -> click menuitem whose label starts with "Thinking level"
take_snapshot -> click menuitem containing "Standard" or "Extended"
Press Escape to close
```

### Flow D: Upload Files

Bridge pattern — Gemini's real file input is hidden, dynamically created by Angular.

**Step 1: Create bridge**
```
evaluate_script:
() => {
  let bridge = document.getElementById('mcp-bridge');
  if (!bridge) {
    bridge = document.createElement('input');
    bridge.type = 'file';
    bridge.id = 'mcp-bridge';
    bridge.multiple = true;
    bridge.setAttribute('aria-label', 'MCP bridge');
    bridge.style.cssText = 'position:fixed;top:60px;left:200px;z-index:99999;width:100px;height:30px;display:block;opacity:1;';
    document.body.appendChild(bridge);
  }
  return 'Bridge ready';
}
```

**Step 2: Upload to bridge**
```
take_snapshot -> find bridge by label "MCP bridge"
upload_file -> uid=<bridge_uid>, filePath=<absolute_path>

IMPORTANT: upload_file REPLACES bridge.files on each call.
For multi-file, use Stash Pattern (see below).
```

**Step 3: Open Gemini upload dialog**
```
click -> button "Upload & tools"
take_snapshot -> find menuitem "Upload files. Documents, data, code files"
click -> that menuitem
```
This creates `input[name="Filedata"]` in the DOM and opens native file picker (ignore it).

**Step 4: Transfer bridge -> Gemini**
```
evaluate_script:
async () => {
  const bridge = document.getElementById('mcp-bridge');
  if (!bridge || !bridge.files.length) return 'No files on bridge';
  const names = Array.from(bridge.files).map(f => f.name).join(', ');

  const geminiInput = document.querySelector('input[name="Filedata"]');
  if (!geminiInput) return 'Gemini input not found — click "Upload files" first';

  const dt = new DataTransfer();
  for (const file of bridge.files) dt.items.add(file);
  geminiInput.files = dt.files;
  geminiInput.dispatchEvent(new Event('change', { bubbles: true }));

  return 'OK: ' + names;
}
```

Files appear as chips above textbox. Send button enables after ~1-2s.

### Flow E: Send Prompt & Read Response

```
fill -> uid=<textbox_uid>, value=<prompt>
  Must use fill tool — evaluate_script blocked by Quill.js CSP

click -> button "Send message"

wait_for -> text: ["Good response", "Bad response"]

take_snapshot -> extract response text from generic live="polite" after "Gemini said" heading
```

To send with uploaded files: files must be attached first (Flow D), textbox filled, then Send clicked.

### Flow F: Stop Response Mid-Generation

```
wait_for -> text: ["Stop response"]
click -> button "Stop response"
wait_for -> text: ["Good response", "Bad response", "Send message"]
take_snapshot -> partial response in generic live="polite"
```

After stopping, partial response is shown with full feedback buttons (Good/Bad/Redo).

### Flow G: Edit Prompt & Resend

```
take_snapshot -> click button "Edit" on the user message
take_snapshot -> find textbox "Edit prompt" (NOT the main textbox)
fill -> uid=<edit_textbox_uid>, value=<revised prompt>
click -> button "Update"
wait_for -> text: ["Good response", "Bad response"]
```

Edit mode creates a dedicated `textbox "Edit prompt"` above the response, with `button "Cancel"` and `button "Update"`. Update is disabled until text changes from original.

### Flow H: Redo / Regenerate

```
take_snapshot -> click button "Redo"
take_snapshot -> Redo submenu appears with:
  - menuitem "Longer"
  - menuitem "Shorter"
  - menuitem "Don't personalize"
  - menuitem "Try again"
click desired option
wait_for -> text: ["Good response", "Bad response"]
```

For simple regeneration without options, click "Try again".

## Multi-File Upload (Stash Pattern)

`upload_file` replaces bridge files on each call. For multiple files:

```
evaluate_script -> create bridge
evaluate_script -> window._stash = []
upload_file -> file 1
evaluate_script -> window._stash = Array.from(bridge.files)
upload_file -> file 2 (replaces bridge.files)
evaluate_script ->
  const dt = new DataTransfer();
  for (const f of [...window._stash, ...bridge.files]) dt.items.add(f);
  bridge.files = dt.files;
Then proceed with Flow D steps 3-4 as usual.
```

**Stash cleanup:** After successful transfer, run `delete window._stash` to avoid stale state.

## Cleanup

After use, remove bridge to keep DOM clean:
```
evaluate_script:
() => {
  const bridge = document.getElementById('mcp-bridge');
  if (bridge) { bridge.remove(); return 'Bridge removed'; }
  return 'No bridge';
}
```

## Error Recovery

| Symptom | Fix |
|---------|-----|
| "Gemini input not found" | Upload dialog not open. Re-click "Upload & tools" -> "Upload files" |
| Send button still disabled | Files processing. Wait 2-3s, take_snapshot |
| Bridge empty after navigation | SPA nav preserves bridge, full nav kills it. Recreate bridge and re-upload |
| Mode picker closed | Click again (model selection closes the menu automatically) |
| Model/thinking menuitem not found | Use substring match, not exact match |
| Upload files menuitem invisible | The menuitem is inside `menu "Upload file options"` — may need re-snapshot |
| "Update" disabled in edit mode | Text must differ from original; fill with modified text |
| Wrong chat loaded via URL | Use `app/<chat_id>` not `app/c_<chat_id>` — `c_` prefix loads a new chat |

## Notebooks

Gemini Notebooks are RAG containers that organize source-grounded conversations. Each notebook contains sources (documents, websites, text) and linked chats that answer questions grounded in those sources.

### URL Patterns

| Action | URL |
|--------|-----|
| All notebooks | `https://gemini.google.com/notebooks/view` |
| Specific notebook | `https://gemini.google.com/notebook/<notebook_id>` |
| Create notebook | `https://gemini.google.com/notebooks/create` |

Notebook IDs are UUIDs (e.g., `7b030296-780c-44c1-a839-8d16d4188c6b`).

### Sidebar

The `button "Toggle Notebooks"` section in the sidebar lists all notebooks. Each notebook link shows its title. Active notebooks have an `button "Open notebook actions menu"` next to them. The "All notebooks" link navigates to the full list view showing each notebook's source count and emoji icon.

### Notebook Page Structure

```
link "NotebookLM button"        <- opens in notebooklm.google.com
button "Notebook settings"      <- menu: Notebook settings, Pin/Unpin, Rename, Delete

heading "<notebook name>"
button "Add sources"            <- opens Sources dialog

[Navigate to a recent chat in a notebook]  <- one button per chat in this notebook

textbox "Enter a prompt for Gemini"        <- same chat interface
button "Send message"
button "Open mode picker, ..."
```

### Notebook Settings Menu

Clicking `button "Notebook settings"` opens:
- `menuitem "Notebook settings"`
- `menuitem "Pin"` or `"Unpin"` (toggles pinned state)
- `menuitem "Rename"`
- `menuitem "Delete"` — opens `dialog "Delete this notebook?"` with `button "Delete everywhere"`

### Flow I: Create Notebook

```
navigate_page -> https://gemini.google.com/notebooks/create
take_snapshot -> find heading "Name your notebook"
fill -> textbox "Name of the notebook", value=<name>
take_snapshot -> find button (unlabeled, appears after text entry) and click
wait_for -> text: ["Add sources"]
```
Notebook is created and appears in sidebar.

### Flow J: Add Sources to Notebook

```
click -> button "Add sources"
take_snapshot -> dialog appears with heading "Sources" and 4 options:
  - menuitem "Upload files. Documents, data, code files"   <- same bridge pattern as Flow D
  - menuitem "Add from Drive. Sheets, Docs, Slides"
  - menuitem "Add websites"                                 <- opens "Website URLs" sub-dialog
  - menuitem "Copied text"                                  <- opens "Add text" sub-dialog
click desired option
```

**Add websites sub-dialog:**
```
dialog "Website URLs"
  textbox "Paste any links" multiline
  button "Insert" (disabled until URLs entered)
  button "Cancel"
```

**Copied text sub-dialog:**
```
dialog
  textbox "Pasted text" multiline
  button "Add text" (disabled until text entered)
  button "Cancel"
```

### Flow K: Chat in Notebook

Sending a prompt in a notebook creates a linked chat. The behavior differs based on whether sources exist:

**With sources:** Gemini answers grounded in the notebook's sources. Response stays in the notebook context.

**Without sources:** Gemini redirects to a regular chat (`/app/<chat_id>`). The chat appears in the notebook as a `button "Navigate to a recent chat in a notebook"`. Each subsequent prompt creates a new linked chat.

The response structure is identical to regular chat (Flow E) — "You said" heading, "Gemini said" heading, Good/Bad response buttons, Edit, Redo, etc.

### Flow L: Delete Notebook

```
click -> button "Notebook settings"
click -> menuitem "Delete"
take_snapshot -> dialog "Delete this notebook?"
click -> button "Delete everywhere"
```

Deletion is permanent and removes all chats and files from both Gemini and NotebookLM. The page redirects to `notebooks/view`.

## Limitations

- **Quill.js CSP**: prompt text MUST use `fill` tool, not evaluate_script
- **Bridge per-page**: bridge dies on full-page navigation; SPA navigation preserves it
- **upload_file replaces**: each call overwrites bridge.files; use stash for multi-file
- **UID volatility**: always take_snapshot after any click before finding new UIDs
- **Model menu closes on select**: reopen picker to change thinking level after model selection
- **Edit uses separate textbox**: `textbox "Edit prompt"` is distinct from `textbox "Enter a prompt for Gemini"`
- **Model list hardcoded**: models may change over time; verify with snapshot if selections fail
- **Temporary chat button disappears**: after first message in a conversation, the button is removed
