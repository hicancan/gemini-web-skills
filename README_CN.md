<p align="center">
  <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" width="64" alt="Gemini">
</p>

<h1 align="center">gemini-web</h1>
<p align="center">
  <b>Claude Code 技能 · 通过 MCP 自动化 Google Gemini Web</b>
</p>

<p align="center">
  <a href="#-功能"><img src="https://img.shields.io/badge/flows-12-blue" alt="12 个流程"></a>
  <a href="#-验证状态"><img src="https://img.shields.io/badge/测试于-2026--05--26-brightgreen" alt="测试日期"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/English-README-blue" alt="英文"></a>
</p>

---

一个 [Claude Code](https://claude.ai/code) 技能，通过 Chrome DevTools MCP 完全自动化 [Google Gemini Web](https://gemini.google.com)。每个元素定位字符串、每个状态转换、每个边界情况——全部在真实 DOM 上测试验证。可以把它理解为运行在终端里的可编程 Gemini 客户端。

## 为什么需要它

Gemini 的 Web 界面是一个复杂的 Angular SPA：元素是动态生成的、Quill.js 限制了 CSP、文件输入框被隐藏、UID 每次加载都变化。这个技能处理了所有这些复杂性，让 Claude Code 能像人一样驱动 Gemini——只是更快，且可编程。

## 能做什么

<table>
<tr><td width="50%">

### 聊天
- 新建聊天（自动禁用 Personal Intelligence）
- 通过侧栏或 URL 恢复已有聊天
- 3 个模型 × 2 种思维等级

### 文件
- 桥接模式绕过 Angular 隐藏的 `<input>`
- 单文件 / 多文件上传（暂存模式）

</td><td width="50%">

### 对话
- 发送提示词（兼容 Quill.js CSP）
- 读取回复、中途停止生成
- 编辑重发、重新生成（更长 / 更短 / 重试）

### Notebooks（RAG）
- 创建、添加资料源（文件、Drive、网址、文本）
- 基于资料源的问答、重命名、固定、删除

</td></tr>
</table>

## 快速开始

```bash
# 安装
mkdir -p ~/.claude/skills/gemini-web
cp SKILL.md ~/.claude/skills/gemini-web/

# 使用
/gemini-web                    # 交互模式
/gemini-web upload paper.pdf   # 上传并提问
```

**前置条件：** Chrome DevTools MCP 已连接 · 已登录 gemini.google.com

## 流程清单

| # | 流程 | 步数 |
|---|------|------|
| A | 新建聊天 + 禁用 Personal Intelligence | 7 |
| B | 恢复聊天（侧栏或 URL） | 3 |
| C | 选择模型与思维等级 | 6 |
| D | 上传文件（桥接 → DataTransfer） | 5 |
| E | 发送提示词并读取回复 | 4 |
| F | 中途停止生成 | 3 |
| G | 编辑提示词并重新发送 | 5 |
| H | 重新生成（含子选项） | 3 |
| I | 创建 Notebook | 4 |
| J | 添加资料源到 Notebook | 4 |
| K | 在 Notebook 中对话（资料来源加持） | 3 |
| L | 删除 Notebook | 3 |

每一步都是具体的 MCP 工具调用（`click`、`fill`、`evaluate_script`、`wait_for`、`take_snapshot`）。

## 架构

```
┌──────────────┐     MCP      ┌──────────────────┐
│  Claude Code │ ───────────→ │ Chrome DevTools   │
│  (SKILL.md)  │ ←─────────── │ (gemini.google)   │
└──────────────┘   snapshots  └──────────────────┘
       │
       ▼
  桥接模式：
  upload_file → #mcp-bridge → DataTransfer → input[name="Filedata"]
```

桥接模式是核心创新：Gemini 的 Angular 动态创建文件输入框并将其隐藏，MCP 的 `upload_file` 无法直接操作。一个可见的桥接元素先接收文件，然后通过 JavaScript 将文件传输到 Gemini 的隐藏输入框。

## 验证状态

全部 12 个流程于 **2026-05-26** 在 `gemini.google.com`（**Pro** 账户）上端到端测试通过。每个元素定位器均在真实无障碍树上确认。

| 类别 | 验证项 |
|------|--------|
| 导航 | `/app`、`/app/<id>`、`/notebook/<uuid>`、`/notebooks/create`、`/notebooks/view` |
| 表单 | `textbox "Enter a prompt for Gemini"`、`textbox "Edit prompt"`、`textbox "Name of the notebook"` |
| 按钮状态 | `"Send message"` → `"Stop response"` → `"Send message"` 状态转换 |
| 文件上传 | 桥接创建 → `upload_file` → DataTransfer → 文件标签 → 发送按钮启用 |
| 响应检测 | `wait_for ["Good response", "Bad response"]` — 可靠的赞/踩按钮信号 |
| 模型选择 | 3 个模型 + 2 种思维等级，带 `"Selected "` 前缀的子串匹配 |
| Notebook 资料源 | 上传文件、Drive、网址对话框（`textbox "Paste any links"`）、文本对话框（`textbox "Pasted text"`） |

### 测试中发现并修复的 Bug

| Bug | 原始 | 修复后 |
|-----|------|--------|
| URL 前缀 | `c_<chat_id>` | `<chat_id>`（无前缀） |
| 模型菜单关闭 | 未文档化 | 选模型后重新打开选择器 |
| 菜单混淆 | "More tools" vs "More uploads" | 两者均已区分并文档化 |

## 相关链接

- [Google Gemini](https://gemini.google.com) — 本技能自动化的 Web 界面
- [NotebookLM](https://notebooklm.google.com) — 完整功能版 Notebook（Gemini Notebooks 可链接过去）
- [Claude Code](https://claude.ai/code) — 运行此技能的 CLI
- [Chrome DevTools MCP](https://github.com/anthropics/claude-code) — 提供浏览器自动化的 MCP 服务器

## 许可证

MIT — 随便用，随便改，随便发。
