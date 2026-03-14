# last30days（中文说明）

last30days 是一个“最近 30 天话题研究”工具，聚合 Reddit 与 X（Twitter）的讨论，并可在无 Key 时走 WebSearch 兜底。它会自动做去重、评分、日期过滤，并输出可直接复用的研究摘要与上下文片段。

## 功能亮点
- **多源聚合**：Reddit + X + WebSearch（可选/兜底）。
- **自动过滤**：只保留最近 30 天内容（有硬性日期过滤）。
- **结构化输出**：`report.json`、`report.md`、`last30days.context.md`。
- **弱依赖**：不配置 API Key 也能工作（WebSearch 模式）。

## 运行前准备
### 1) Python
本项目脚本使用 Python 3 标准库（无额外依赖）。

### 2) 可选 API Key（推荐）
在 `~/.config/last30days/.env` 中配置（也可用环境变量）：

```
# last30days API Configuration
# 两个 Key 都是可选的

# 用于 Reddit 搜索（OpenAI Responses API + web_search 工具）
OPENAI_API_KEY=

# 用于 X/Twitter 搜索（xAI Responses API + x_search 工具）
XAI_API_KEY=
```

推荐设置文件权限：
```
chmod 600 ~/.config/last30days/.env
```

## 使用方式
在 `last30days` 目录下执行：

```
python3 ./scripts/last30days.py "你的话题"
```

常用参数：
- `--quick`：更快，源更少（8–12）
- `--deep`：更全面（Reddit 50–70、X 40–60）
- `--emit=MODE`：输出格式（`compact|json|md|context|path`）
- `--sources=MODE`：指定来源（`auto|reddit|x|both`）
- `--include-web`：在有 Key 时也追加 WebSearch
- `--mock`：使用内置样例数据（无 API 调用）
- `--debug`：开启调试日志

示例：
```
python3 ./scripts/last30days.py "Claude Code skills" --quick --emit=md
```

## 模式说明
- **Full**：`OPENAI_API_KEY` + `XAI_API_KEY` → Reddit + X + 可选 WebSearch
- **Partial**：仅一个 Key → Reddit 或 X + 可选 WebSearch
- **Web-Only**：无 Key → WebSearch 兜底（脚本会提示由 Claude 侧执行）

## 输出位置
默认写入：
```
~/.local/share/last30days/out/
```
文件包含：
- `report.json`：结构化结果
- `report.md`：完整报告
- `last30days.context.md`：简短上下文片段
- `raw_openai.json` / `raw_xai.json`（仅当有 API 调用时）
- `raw_reddit_threads_enriched.json`（Reddit 线程富化数据）

## 常见问题
- **没有 API Key 能用吗？** 能，自动进入 WebSearch 兜底模式。
- **为什么有时结果很少？** 仅保留最近 30 天，且会做严格日期过滤。
- **如何加快速度？** 使用 `--quick`。

## 目录结构（简要）
- `scripts/last30days.py`：入口
- `scripts/lib/openai_reddit.py`：Reddit 搜索（OpenAI）
- `scripts/lib/xai_x.py`：X 搜索（xAI）
- `scripts/lib/websearch.py`：WebSearch 解析与过滤
- `scripts/lib/render.py`：报告输出

---
如需更深入的自定义或安全加固（例如禁用原始响应落盘），可以再告诉我你的需求。
