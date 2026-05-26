<p align="center">
  <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" width="64" alt="Gemini">
</p>

<h1 align="center">gemini-web</h1>
<p align="center">
  <b>Claude Code 技能 · 通过 MCP 自动化 Google Gemini Web</b>
</p>

<p align="center">
  <a href="#流程清单"><img src="https://img.shields.io/badge/flows-12-blue" alt="12 个流程"></a>
  <a href="#水印去除"><img src="https://img.shields.io/badge/复刻-100%25-brightgreen" alt="100% 复刻"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/English-README-blue" alt="English"></a>
</p>

---

一个 [Claude Code](https://claude.ai/code) 技能，通过 Chrome DevTools MCP 完全自动化 [Google Gemini Web](https://gemini.google.com)。所有元素定位器、状态转换、边界情况均在真实 DOM 上验证。

同时包含 [GargantuaX/gemini-watermark-remover](https://github.com/GargantuaX/gemini-watermark-remover)（4,225 星）的 **100% 忠实 Python 复刻**——Gemini 隐形水印去除的黄金标准工具。全部 7 个模块、50+ 个函数、200+ 个常量，逐行对照移植。

## 快速开始

```bash
# 安装
mkdir -p ~/.claude/skills/gemini-web
cp SKILL.md ~/.claude/skills/gemini-web/
cp -r references/ scripts/ ~/.claude/skills/gemini-web/

# 使用
/gemini-web                    # 交互模式

# 生成图片 + 下载 + 去水印
/gemini-web generate a cyberpunk wallpaper
# 然后：
uv run --with Pillow --with numpy scripts/remove_watermark.py ~/Desktop/output/original.png
```

**前置条件：** Chrome DevTools MCP 已连接 · 已登录 gemini.google.com

## 流程清单

| # | 流程 | 描述 |
|---|------|------|
| A | 新建聊天 + 禁用 PI | 新对话，自动禁用 Personal Intelligence |
| B | 恢复聊天 | 侧栏或直接 URL |
| C | 模型 + 思维 | 3.1 Flash-Lite / 3.5 Flash / 3.1 Pro × Standard / Extended |
| D | 文件上传 | 桥接模式绕过 Angular 隐藏输入 |
| E | 发送 & 读取 | 兼容 Quill.js CSP，提取响应文本 |
| F | 停止生成 | 中断进行中的生成 |
| G | 编辑 & 重发 | 在独立文本框中编辑后重新发送 |
| H | 重新生成 | 更长 / 更短 / 不个性化 / 重试 |
| I | 图片生成 | 20 种模板，Nano Banana 2，原图下载 |
| J | 视频生成 | 18 种模板，Omni，16:9 比例 |
| K | 导入代码 | GitHub URL 或上传文件夹 |
| L | Notebooks (RAG) | 创建、添加资料源、对话、删除 |

## 水印去除

**100% 忠实 Python 复刻** `GargantuaX/gemini-watermark-remover`。每个函数、每个常量、每个分支均来自对应源文件。

### 模块覆盖

| 原始 JS | 行数 | Python | 状态 |
|---------|------|--------|------|
| `blendModes.js` | 70 | ✓ | 完整 |
| `geminiSizeCatalog.js` | 270 | ✓ | 完整（70+ 已知尺寸） |
| `adaptiveDetector.js` | 488 | ✓ | 完整（NCC、Sobel、warp、插值） |
| `restorationMetrics.js` | 250 | ✓ | 完整（纹理、光晕、近黑） |
| `watermarkDecisionPolicy.js` | 80 | ✓ | 完整（direct-match / validated / insufficient） |
| `watermarkPresence.js` | 10 | ✓ | 完整 |
| `watermarkConfig.js` | 146 | ✓ | 完整（48/96 配置、catalog 解析） |
| `candidateSelector.js` | 1540 | ✓ | 完整（全部 22 个函数） |
| `multiPassRemoval.js` | 70 | ✓ | 完整 |
| `watermarkProcessor.js` | 876 | ✓ | 完整（全部 9 个函数） |
| **合计** | **~3,800** | **~1,380** | **100%** |

### Pipeline 阶段

```
┌─────────────────────────────────────────────────────┐
│ 1. 配置检测                                         │
│    detectWatermarkConfig → 48/96 logo + 位置        │
├─────────────────────────────────────────────────────┤
│ 2. 候选选择（评估 150+ 候选）                        │
│    ├─ 标准候选（catalog 变体）                       │
│    ├─ 模板对齐（5×5×3 = 75 组合）                   │
│    ├─ Alpha 增益搜索（14 个值）                      │
│    ├─ 附近搜索（±12px 网格，49 个位置）              │
│    ├─ 尺寸变化（±12px，12 个尺寸）                   │
│    ├─ 预览锚点（小图全网格搜索）                      │
│    └─ 自适应检测（NCC 区域搜索）                     │
├─────────────────────────────────────────────────────┤
│ 3. 多轮去除（最多 4 轮）                             │
├─────────────────────────────────────────────────────┤
│ 4. Alpha 增益重校准（14+14 精调增益）                │
├─────────────────────────────────────────────────────┤
│ 5. 亚像素精调（3×3×3×3 = 81 组合）                  │
├─────────────────────────────────────────────────────┤
│ 6. 预览边缘清理（4×2 预设，最多 3 轮）               │
├─────────────────────────────────────────────────────┤
│ 7. 光晕评估（alpha 带亮度分析）                       │
└─────────────────────────────────────────────────────┘
```

### 算法

```
Gemini 添加水印:  watermarked = α × 255 + (1-α) × original
反向求解:         original = (watermarked - α × 255) / (1-α)

其中 α ∈ [0,1] 是预校准的 96×96 像素级 alpha 映射
```

### 使用

```bash
# 完整 pipeline（推荐）
uv run --with Pillow --with numpy scripts/remove_watermark.py input.png -o cleaned.png

# 简单模式（均匀 alpha，无检测）
uv run --with Pillow --with numpy scripts/remove_watermark.py input.png --simple --alpha 0.01
```

## 相关链接

- [Google Gemini](https://gemini.google.com) — 本技能自动化的 Web 界面
- [GargantuaX/gemini-watermark-remover](https://github.com/GargantuaX/gemini-watermark-remover) — 原始 JS 实现（4,225★）
- [NotebookLM](https://notebooklm.google.com) — 完整功能版 Notebook

## 许可证

MIT
