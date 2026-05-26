<p align="center">
  <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" width="64" alt="Gemini">
</p>

<h1 align="center">gemini-web</h1>
<p align="center">
  <b>Claude Code Skill · Automate Google Gemini Web via MCP</b>
</p>

<p align="center">
  <a href="#flows"><img src="https://img.shields.io/badge/flows-12-blue" alt="12 flows"></a>
  <a href="#watermark-removal"><img src="https://img.shields.io/badge/port-100%25-brightgreen" alt="100% port"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"></a>
  <a href="README_CN.md"><img src="https://img.shields.io/badge/中文-README_CN-red" alt="中文"></a>
</p>

---

A [Claude Code](https://claude.ai/code) skill that fully automates [Google Gemini Web](https://gemini.google.com) through Chrome DevTools MCP. Every locator string, every state transition, every edge case — tested against the live DOM.

Also includes a **100% faithful Python port** of [GargantuaX/gemini-watermark-remover](https://github.com/GargantuaX/gemini-watermark-remover) (4,225 stars) — the gold-standard Gemini invisible watermark removal tool. All 7 modules, all 50+ functions, all 200+ constants.

## Quick Start

```bash
# Install the skill
mkdir -p ~/.claude/skills/gemini-web
cp SKILL.md ~/.claude/skills/gemini-web/
cp -r references/ scripts/ ~/.claude/skills/gemini-web/

# Use in Claude Code
/gemini-web                    # interactive mode

# Generate + download + clean watermark
/gemini-web generate a cyberpunk wallpaper
# then:
uv run --with Pillow --with numpy scripts/remove_watermark.py ~/Desktop/output/original.png
```

**Prerequisites:** Chrome DevTools MCP connected · logged into gemini.google.com

## Flows

| # | Flow | Description |
|---|------|-------------|
| A | New Chat + PI disable | Fresh chat, auto-disable Personal Intelligence |
| B | Resume Chat | Sidebar or direct URL |
| C | Model + Thinking | 3.1 Flash-Lite / 3.5 Flash / 3.1 Pro × Standard / Extended |
| D | File Upload | Bridge pattern bypasses Angular hidden input |
| E | Send & Read | Quill.js CSP-aware prompt, response extraction |
| F | Stop | Interrupt mid-generation |
| G | Edit & Resend | Edit prompt in dedicated textbox |
| H | Redo | Longer / Shorter / Don't personalize / Try again |
| I | Image Generation | 20 templates, Nano Banana 2, download original |
| J | Video Generation | 18 templates, Omni, 16:9 aspect |
| K | Import Code | GitHub URL or upload folder |
| L | Notebooks (RAG) | Create, add sources, chat, delete |

## Watermark Removal

A **100% faithful Python port** of `GargantuaX/gemini-watermark-remover`. Every function, every constant, every branch from every source file.

### Module Coverage

| Original JS | Lines | Python | Status |
|-------------|-------|--------|--------|
| `blendModes.js` | 70 | ✓ | Complete |
| `geminiSizeCatalog.js` | 270 | ✓ | Complete (70+ known sizes) |
| `adaptiveDetector.js` | 488 | ✓ | Complete (NCC, Sobel, warp, interpolate) |
| `restorationMetrics.js` | 250 | ✓ | Complete (texture, halo, near-black) |
| `watermarkDecisionPolicy.js` | 80 | ✓ | Complete (direct-match / validated / insufficient) |
| `watermarkPresence.js` | 10 | ✓ | Complete |
| `watermarkConfig.js` | 146 | ✓ | Complete (48/96 config, catalog resolve) |
| `candidateSelector.js` | 1540 | ✓ | Complete (all 22 functions) |
| `multiPassRemoval.js` | 70 | ✓ | Complete |
| `watermarkProcessor.js` | 876 | ✓ | Complete (all 9 functions) |
| **Total** | **~3,800** | **~1,380** | **100%** |

### Pipeline Stages

```
┌─────────────────────────────────────────────────────┐
│ 1. Config Detection                                 │
│    detectWatermarkConfig → 48/96 logo + position    │
├─────────────────────────────────────────────────────┤
│ 2. Candidate Selection (150+ candidates evaluated)  │
│    ├─ Standard trials (catalog variants)            │
│    ├─ Template warp (5×5×3 = 75 combinations)       │
│    ├─ Alpha gain search (14 values)                 │
│    ├─ Nearby search (±12px grid, 49 positions)      │
│    ├─ Size jitter (±12px, 12 sizes)                 │
│    ├─ Preview anchor (exhaustive grid for small imgs)│
│    └─ Adaptive detection (NCC region search)        │
├─────────────────────────────────────────────────────┤
│ 3. Multi-Pass Removal (up to 4 passes)              │
├─────────────────────────────────────────────────────┤
│ 4. Alpha Gain Recalibration (14+14 refined gains)   │
├─────────────────────────────────────────────────────┤
│ 5. Sub-pixel Refinement (3×3×3×3 = 81 combinations) │
├─────────────────────────────────────────────────────┤
│ 6. Preview Edge Cleanup (4×2 presets, up to 3 passes)│
├─────────────────────────────────────────────────────┤
│ 7. Halo Assessment (alpha band luminance analysis)   │
└─────────────────────────────────────────────────────┘
```

### Algorithm

```
Gemini adds:    watermarked = α × 255 + (1-α) × original
Reverse:        original = (watermarked - α × 255) / (1-α)

where α ∈ [0,1] is a pre-calibrated 96×96 pixel-level alpha map.
```

### Usage

```bash
# Full pipeline (recommended)
uv run --with Pillow --with numpy scripts/remove_watermark.py input.png -o cleaned.png

# Simple mode (uniform alpha, no detection)
uv run --with Pillow --with numpy scripts/remove_watermark.py input.png --simple --alpha 0.01
```

## Related

- [Google Gemini](https://gemini.google.com) — the web UI this skill automates
- [GargantuaX/gemini-watermark-remover](https://github.com/GargantuaX/gemini-watermark-remover) — the original JS implementation (4,225★)
- [NotebookLM](https://notebooklm.google.com) — full-featured notebook product

## License

MIT
