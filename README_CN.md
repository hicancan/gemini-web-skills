# gemini-web 技能

通过 Chrome DevTools MCP 自动化操作 [Google Gemini Web](https://gemini.google.com) 的 Claude Code 技能。提供 12 个已测试流程，覆盖完整的 Gemini 交互生命周期。

## 功能

### 聊天
- 新建聊天，自动禁用 Personal Intelligence
- 通过侧栏或直接 URL 恢复已有聊天
- 模型选择：3.1 Flash-Lite / 3.5 Flash / 3.1 Pro + Standard / Extended 思维等级

### 文件上传
- 桥接模式绕过 Angular 隐藏文件输入框
- 单文件和多文件上传（暂存模式）
- 支持 Gemini 接受的任何文件类型

### 对话
- 发送提示词（兼容 Quill.js CSP — 使用 `fill` 工具）
- 通过无障碍树读取回复
- 中途停止生成
- 编辑提示词并重新发送（使用独立的 `textbox "Edit prompt"`）
- 重新生成，附带子选项：更长、更短、不个性化、重试

### Notebooks（RAG）
- 创建 Notebook 并添加资料源（文件、Google Drive、网页、粘贴文本）
- 基于资料源的问答
- Notebook 管理：重命名、固定/取消固定、删除

## 流程清单

| Flow | 描述 |
|------|------|
| A | 新建聊天 + 禁用 Personal Intelligence |
| B | 恢复聊天（侧栏 / 直接 URL） |
| C | 选择模型与思维等级 |
| D | 上传文件（桥接模式） |
| E | 发送提示词并读取回复 |
| F | 中途停止生成 |
| G | 编辑提示词并重新发送 |
| H | 重新生成 |
| I | 创建 Notebook |
| J | 添加资料源到 Notebook |
| K | 在 Notebook 中对话 |
| L | 删除 Notebook |

## 验证状态

全部 12 个流程于 2026-05-26 在 `gemini.google.com`（Pro 账户）上端到端测试通过。每个元素定位字符串均在真实 DOM 上确认。

## 前置条件

- Chrome DevTools MCP 已连接
- 用户已登录 gemini.google.com
- 待上传文件存在于本地磁盘

## 安装

```bash
mkdir -p ~/.claude/skills/gemini-web
cp SKILL.md ~/.claude/skills/gemini-web/SKILL.md
```

重启 Claude Code 或重新加载技能。输入 `/gemini-web` 或提及 Gemini Web 操作时自动触发。

## 许可证

MIT
