---
name: 抓取youtube文字稿
description: "YouTube 视频全能工具。支持六种模式：摘要、问答、逐字稿、视频搜索、频道追踪、文字稿提纯（用 Gemini CLI 对原始字幕做结构化提纯，支持播客按问答拆解、讲座按知识点分章、访谈按话题整理）。检测到 YouTube URL、视频搜索请求、频道追踪需求、文字稿提纯/整理需求时触发。"
version: 2.1.0
metadata: {"clawdbot":{"emoji":"📺","requires":{"env":["GEMINI_API_KEY","SERPER_API_KEY"],"bins":["python3","yt-dlp","gemini"]}}}
---

# YouTube 工具

## 意图路由

| 用户请求 | 模式 | 执行方式 |
|---------|------|---------| 
| 总结视频 / 视频说了什么 | **摘要** | `get_transcript.py` → Claude 生成结构化摘要 |
| 问视频里的内容 | **问答** | `get_transcript.py` → 基于字幕回答 |
| 要完整文字稿 / 逐字转录 | **逐字稿** | `youtube_transcript.py`（Gemini，含说话人标注） |
| 搜索某主题的视频 / 找视频 | **视频搜索** | `video_search.py` → 选择 → `get_transcript.py` → 摘要 |
| 追踪频道 / 关注博主 / 检查更新 | **频道追踪** | `channel_tracker.py` |
| 提纯文字稿 / 整理播客 / 拆解问答 | **文字稿提纯** | `refine_transcript.sh`（Gemini CLI 结构化提纯） |

---

## 模式一：摘要 / 问答

```bash
python3 {baseDir}/scripts/get_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

- 依赖 `yt-dlp`
- 输出字幕文本后，由 Claude 生成摘要或回答用户问题
- 适合有 CC 字幕或自动生成字幕的视频

**摘要格式：**
```
📹 标题 | 👤 频道 | 📅 发布日期

🎯 核心观点：[1-2句]

💡 关键要点：
- ...

🔑 结论：[行动建议]
```

---

## 模式二：逐字稿

```bash
# 短视频（≤10分钟）—— 单次调用
python3 {baseDir}/scripts/youtube_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 长视频 —— 自动分段转录（默认每 10 分钟一段）
# 如果无法自动检测时长，手动指定：
python3 {baseDir}/scripts/youtube_transcript.py "URL" --duration 2:30:45

# 指定输出路径：
python3 {baseDir}/scripts/youtube_transcript.py "URL" --out /path/to/output.txt

# 自定义分段长度（如每 5 分钟一段）：
python3 {baseDir}/scripts/youtube_transcript.py "URL" --duration 1:20:00 --segment-minutes 5

# 禁用分段，强制单次调用（可能截断）：
python3 {baseDir}/scripts/youtube_transcript.py "URL" --no-segment
```

- 依赖 `GEMINI_API_KEY`
- **自动分段**：视频 > 10 分钟时自动分段转录，每段独立调用 Gemini，最后拼接
- 内置速率限制处理和重试机制
- 输出格式：`说话人: 文字`，无时间码
- 第一行为视频标题
- 完成后作为附件发送给用户

---

## 模式三：视频搜索闭环

当用户想搜索某个主题的视频并获取内容总结时，执行以下闭环流程：

### 第一步：搜索视频

```bash
python3 {baseDir}/scripts/video_search.py -q "搜索关键词" --num 5
# 中文搜索加上语言参数：
python3 {baseDir}/scripts/video_search.py -q "搜索关键词" --gl cn --hl zh --num 5
# 仅返回 YouTube 视频：
python3 {baseDir}/scripts/video_search.py -q "搜索关键词" --youtube-only
```

依赖 `SERPER_API_KEY`（在 .env 文件中配置）。返回 JSON 包含视频标题、URL、频道、时长、描述等。

### 第二步：展示结果供选择

将搜索结果以表格形式展示给用户：

```
| # | 标题 | 频道 | 时长 | 日期 |
|---|------|------|------|------|
| 1 | ... | ... | ... | ... |
```

让用户选择需要深入了解的视频，或基于相关性自动选择最佳结果。

### 第三步：获取文字稿

对选定的 YouTube 视频获取文字稿：

```bash
# 优先方式：通过字幕获取（速度快）
python3 {baseDir}/scripts/get_transcript.py "YOUTUBE_URL"

# 如果无字幕：切换到 Gemini 直接转录
python3 {baseDir}/scripts/youtube_transcript.py "YOUTUBE_URL"
```

### 第四步：生成摘要

基于获取的文字稿，使用标准摘要格式生成结构化总结。如果搜索了多个视频，合并生成对比分析报告。

**多视频对比格式：**
```
📊 主题：[搜索关键词]
📹 分析了 N 个视频

---

🎬 视频 1：[标题] | 👤 [频道]
🎯 核心观点：...
💡 关键要点：...

🎬 视频 2：[标题] | 👤 [频道]
🎯 核心观点：...
💡 关键要点：...

---

🔀 对比分析：
- 共识：...
- 分歧：...

🔑 综合结论：[行动建议]
```

### 视频搜索 CLI 参数

| 参数 | 说明 |
|------|------|
| `-q, --query` | 搜索关键词（必需） |
| `-n, --num` | 返回数量（默认 10） |
| `--gl` | 国家代码（如 cn, us），默认 world |
| `--hl` | 语言代码（如 zh, en），默认 en |
| `--youtube-only` | 仅返回 YouTube 链接 |

---

## 模式四：频道追踪

追踪重要 YouTube 频道/博主的视频更新。频道数据持久化存储在 `data/` 目录。

### 添加追踪频道

```bash
# 通过 @handle 添加
python3 {baseDir}/scripts/channel_tracker.py add "@3blue1brown" --alias "3B1B数学"

# 通过频道 URL 添加
python3 {baseDir}/scripts/channel_tracker.py add "https://www.youtube.com/@lexfridman" --alias "Lex"

# 通过频道 ID 添加
python3 {baseDir}/scripts/channel_tracker.py add "UCxxxxxx"
```

### 查看追踪列表

```bash
python3 {baseDir}/scripts/channel_tracker.py list
```

### 检查更新

```bash
# 检查所有频道更新
python3 {baseDir}/scripts/channel_tracker.py check

# 检查指定频道（可通过名称、别名或 URL）
python3 {baseDir}/scripts/channel_tracker.py check "3B1B数学"
python3 {baseDir}/scripts/channel_tracker.py check "@3blue1brown"

# 指定获取数量
python3 {baseDir}/scripts/channel_tracker.py check --count 10
```

返回 JSON 包含新视频列表。对于新视频可以自动执行摘要 / 文字稿流程。

### 移除频道

```bash
python3 {baseDir}/scripts/channel_tracker.py remove "3B1B数学"
```

### 追踪更新 + 摘要闭环

当用户要求"检查频道更新"并总结新内容时：

1. 执行 `channel_tracker.py check` 获取新视频列表
2. 对每个新视频调用 `get_transcript.py` 获取字幕
3. 生成新视频摘要报告

**更新报告格式：**
```
📡 频道更新报告 | 📅 检查时间

---

📺 [频道名] — N 个新视频

🆕 1. [标题] (时长)
🎯 核心观点：...
💡 关键要点：...

🆕 2. [标题] (时长)
🎯 核心观点：...

---

📊 总计：检查了 X 个频道，发现 Y 个新视频
```

---

## 模式五：文字稿提纯

通过 Gemini CLI 对原始字幕进行结构化提纯。特别适合播客、讲座、访谈等长内容。

### 四种提纯子模式

| 子模式 | 适用场景 | 特点 |
|--------|---------|------|
| `general` | 通用视频 | 去重去噪 + 分段 + 提取要点 |
| `podcast` | 播客/对话 | **按问答拆解**，识别主持人/嘉宾，每个议题独立总结 |
| `lecture` | 讲座/教程 | 按知识点分章，提取概念和定义 |
| `interview` | 访谈/采访 | 按话题轮次，标注发言人立场 |

### 直接从 YouTube URL 提纯（一步到位）

```bash
# 播客模式 — 自动获取字幕 + 按问答拆解
bash {baseDir}/scripts/refine_transcript.sh --url "YOUTUBE_URL" --mode podcast

# 讲座模式
bash {baseDir}/scripts/refine_transcript.sh --url "YOUTUBE_URL" --mode lecture

# 访谈模式
bash {baseDir}/scripts/refine_transcript.sh --url "YOUTUBE_URL" --mode interview
```

### 从已有文字稿提纯

```bash
# 对已保存的文字稿文件提纯
bash {baseDir}/scripts/refine_transcript.sh --input /path/to/raw_transcript.txt --mode podcast

# 指定输出路径和语言
bash {baseDir}/scripts/refine_transcript.sh --input raw.txt --mode podcast --output refined.md --lang zh
```

### 提纯 CLI 参数

| 参数 | 说明 |
|------|------|
| `--input <文件>` | 原始文字稿文件路径 |
| `--url <URL>` | YouTube URL（自动获取字幕后提纯） |
| `--output <文件>` | 输出路径（默认自动命名到 out/ 目录） |
| `--mode <模式>` | `general` / `podcast` / `lecture` / `interview`（默认 general） |
| `--model <模型>` | Gemini 模型（默认 gemini-3-pro-preview） |
| `--title <标题>` | 视频标题（可选，增强提纯效果） |
| `--lang <语言>` | 输出语言：`zh` / `en` / `auto`（默认 auto） |

### 与搜索/追踪的完整闭环

**搜索 → 提纯闭环：**
1. `video_search.py` 搜索视频
2. `get_transcript.py` 获取字幕
3. `refine_transcript.sh --input <字幕文件> --mode podcast` 提纯

**追踪 → 提纯闭环：**
1. `channel_tracker.py check` 发现新视频
2. 对新视频 URL 执行 `refine_transcript.sh --url <URL> --mode podcast`

---

## 备用方案（yt-dlp 失败时）

使用 MCP YouTube Transcript server（需安装于 `/root/clawd/mcp-server-youtube-transcript`）：

```bash
cd /root/clawd/mcp-server-youtube-transcript && node --input-type=module -e "
import { getSubtitles } from './dist/youtube-fetcher.js';
const result = await getSubtitles({ videoID: 'VIDEO_ID', lang: 'en' });
console.log(JSON.stringify(result, null, 2));
" > /tmp/yt-transcript.json
```

---

## 错误处理

- 视频无字幕 → 告知用户，建议使用逐字稿模式（Gemini 可处理无字幕视频）
- `yt-dlp` 不可用 → 切换备用方案
- `GEMINI_API_KEY` 未设置 → 提示用户配置环境变量
- `SERPER_API_KEY` 未设置 → 视频搜索功能不可用，提示配置
- 频道追踪数据文件损坏 → 自动重建空列表

## 环境变量

| 变量 | 用途 | 必需 |
|------|------|------|
| `GEMINI_API_KEY` | Gemini 逐字稿转录 | 逐字稿模式必需 |
| `SERPER_API_KEY` | 视频搜索 | 搜索模式必需 |

在技能目录下创建 `.env` 文件配置：
```
GEMINI_API_KEY="your-gemini-key"
SERPER_API_KEY="your-serper-key"
```
