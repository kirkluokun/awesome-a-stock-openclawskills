---
name: search-x
description: 使用 Grok 实时搜索 X/Twitter，查找帖子、热门话题和讨论，并附带引用来源。
homepage: https://docs.x.ai
triggers:
  - search x
  - search twitter
  - find tweets
  - what's on x about
  - x search
  - twitter search
metadata:
  clawdbot:
    emoji: "🔍"
---

# 搜索 X

由 Grok 的 x_search 工具驱动的实时 X/Twitter 搜索，返回带引用来源的真实推文。

## 配置

设置 xAI API 密钥：

```bash
clawdbot config set skills.entries.search-x.apiKey "xai-YOUR-KEY"
```

或使用环境变量：
```bash
export XAI_API_KEY="xai-YOUR-KEY"
```

获取 API 密钥：https://console.x.ai

## 命令

### 基础搜索
```bash
node {baseDir}/scripts/search.js "AI video editing"
```

### 按时间过滤
```bash
node {baseDir}/scripts/search.js --days 7 "breaking news"
node {baseDir}/scripts/search.js --days 1 "trending today"
```

### 按账号过滤
```bash
node {baseDir}/scripts/search.js --handles @elonmusk,@OpenAI "AI announcements"
node {baseDir}/scripts/search.js --exclude @bots "real discussions"
```

### 输出选项
```bash
node {baseDir}/scripts/search.js --json "topic"        # 完整 JSON 响应
node {baseDir}/scripts/search.js --compact "topic"     # 仅推文内容，无冗余信息
node {baseDir}/scripts/search.js --links-only "topic"  # 仅 X 链接
```

## 对话示例

**用户：**"搜索 X 上关于 Claude Code 的讨论"
**操作：** 以"Claude Code"为关键词执行搜索

**用户：**"查找 @remotion_dev 过去一周的推文"
**操作：** 执行 `--handles @remotion_dev --days 7`

**用户：**"今天 Twitter 上关于 AI 的热门话题是什么？"
**操作：** 执行 `--days 1 "AI trending"`

**用户：**"搜索 X 上过去30天关于 Remotion 最佳实践的内容"
**操作：** 执行 `--days 30 "Remotion best practices"`

## 工作原理

使用 xAI 的 Responses API（`/v1/responses`）调用 `x_search` 工具：
- 模型：`grok-4-1-fast-non-reasoning`（针对智能体搜索优化）
- 返回带 URL 的真实推文
- 包含可核实的引用来源
- 支持日期和账号过滤

## 返回格式

每条结果包含：
- **@用户名**（显示名称）
- 推文内容
- 发布日期/时间
- 推文直链

## 环境变量

- `XAI_API_KEY` — xAI API 密钥（必填）
- `SEARCH_X_MODEL` — 模型覆盖（默认：grok-4-1-fast）
- `SEARCH_X_DAYS` — 默认搜索天数（默认：30）
