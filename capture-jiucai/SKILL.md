---
name: jiucai-capture
description: A股主题跟踪 — 从韭菜公社抓取市场热点、产业链、异动板块、最新段子，AI 结构化提取后进行多维分析。
author: kirk
version: 0.2.0
allowed-tools: Bash(uv:*), Bash(python3:*), Bash(gemini:*)
metadata: {"openclaw":{"requires":{"bins":["uv"]},"install":[{"id":"uv","kind":"uv","label":"Install dependencies (uv)","script":"cd {skillDir} && uv sync && uv run playwright install chromium"}]}}
triggers:
  - "韭菜公社"
  - "市场热点"
  - "产业链"
  - "异动板块"
  - "最新段子"
  - "A股主题"
  - "看看韭菜"
  - "热门板块"
  - "市场关注"
  - "有什么异动"
  - "最新市场"
---

# A股主题跟踪（韭菜公社数据源）

从**韭菜公社**（jiuyangongshe.com）实时抓取 A 股市场数据，通过 Gemini AI 结构化提取股票、主题、投资逻辑，帮助用户快速掌握市场动态。

## 首次安装

```bash
cd {skillDir} && uv sync && uv run playwright install chromium
```

## 环境要求

API Key 存储在 `{skillDir}/.env`。所有抓取命令统一使用以下前缀：
```bash
cd {skillDir} && source .env && export GEMINI_API_KEY
```

---

## 数据获取策略（先查库，再抓取）

> **核心原则：不要每次都去网站抓取。优先查数据库。**

1. **默认行为** — 先查数据库（`data/themes.db`），直接使用 `scripts/query_*.py` 查询
2. **触发抓取的条件**（满足任一即可）：
   - 用户明确说"**最新**"、"**帮我抓**"、"**更新一下**"、"**去网站看看**"
   - 数据库中**没有当天**的数据（查询结果为空）
3. **判断数据库是否有当天数据**：
   ```bash
   cd {skillDir} && uv run python -c "
   import sqlite3; conn = sqlite3.connect('data/themes.db')
   cur = conn.cursor()
   cur.execute(\"SELECT COUNT(*), GROUP_CONCAT(DISTINCT source) FROM articles WHERE publish_date = date('now', 'localtime')\")
   count, sources = cur.fetchone()
   print(f'今日数据: {count} 条, 来源: {sources or \"无\"}')
   "
   ```
4. **如果需要抓取**，再执行对应场景的 fetch 命令

---

## 意图识别与任务路由

根据用户的自然语言提问，判断属于以下哪种场景，然后执行对应的操作流程。
**注意**：每个场景的"抓取"步骤仅在需要时执行（见上方数据获取策略）。

### 场景 1：市场热点 / 产业链关注度

**触发词**：市场热点、热门板块、产业链、关注度最高、当前什么主题火

**操作流程**：
1. 抓取最新产业链数据：
   ```bash
   cd {skillDir} && source .env && export GEMINI_API_KEY && uv run python -m a_stock_watcher.cli fetch --source industry_chain
   ```
2. 查询产业链排名 + 关联股票：
   ```bash
   cd {skillDir} && uv run python scripts/query_industry_chain.py
   ```
3. **汇报格式**：按排名列出产业链名称、热度标记、核心逻辑、关联股票

---

### 场景 2：异动板块

**触发词**：有什么异动、异动板块、涨停分析、今天异动、板块异动

**操作流程**：
1. 抓取最新异动数据：
   ```bash
   cd {skillDir} && source .env && export GEMINI_API_KEY && uv run python -m a_stock_watcher.cli fetch --source action
   ```
2. 查询异动板块（按日期分组）：
   ```bash
   cd {skillDir} && uv run python scripts/query_action.py
   ```
3. **汇报格式**：按日期分组，列出每天的异动板块标题、涉及个股、解析文字

---

### 场景 3：最新段子 / 市场资讯

**触发词**：最新段子、最新市场、有什么新的、看看韭菜公社、市场怎么样、最近有什么

**操作流程**：
1. 拉取 5 页最新内容：
   ```bash
   cd {skillDir} && source .env && export GEMINI_API_KEY && uv run python -m a_stock_watcher.cli fetch --source study_hot
   ```
   > **注意**：此命令需启动 Playwright 浏览器逐篇渲染，耗时约 5-15 分钟。请提前告知用户需要等待。
2. 查询近2天段子 + 主题热度统计：
   ```bash
   cd {skillDir} && uv run python scripts/query_latest.py
   ```
3. **汇报格式**：
   - 先列出近2天的文章标题、投资逻辑、关联股票
   - 最后附上 Top 10 主题热度统计
   - 用自然语言总结市场情绪和热点方向

---

### 场景 4：查询特定股票 / 主题

**触发词**：XX 股票怎么样、关于 XX 的文章、XX 主题有哪些股票

**操作流程**（无需抓取，直接查数据库）：
```bash
cd {skillDir} && uv run python scripts/query_stock.py <股票名称或代码>
```

示例：
```bash
uv run python scripts/query_stock.py 贵州茅台
uv run python scripts/query_stock.py 600519
```

---

### 场景 5：查看数据库统计

**触发词**：数据库状态、有多少数据、统计信息

```bash
cd {skillDir} && source .env && export GEMINI_API_KEY && uv run python -m a_stock_watcher.cli stats
```

---

## 脚本清单

| 脚本                              | 用途                   | 需要抓取？              |
| --------------------------------- | ---------------------- | ----------------------- |
| `scripts/query_industry_chain.py` | 产业链排名 + 关联股票  | 先 fetch industry_chain |
| `scripts/query_action.py`         | 异动板块（按日期分组） | 先 fetch action         |
| `scripts/query_latest.py`         | 近2天段子 + 主题热度   | 先 fetch study_hot      |
| `scripts/query_stock.py <关键词>` | 按股票名/代码查文章    | 否（直接查库）          |

## 数据库结构

位置：`{skillDir}/data/themes.db`（SQLite）

| 表名             | 关键字段                                                           | 用途             |
| ---------------- | ------------------------------------------------------------------ | ---------------- |
| `articles`       | id, source, title, content, publish_date, logic_summary, relevance | 文章主表         |
| `stocks`         | id, code, name                                                     | 股票实体（去重） |
| `themes`         | id, name, category                                                 | 主题实体（去重） |
| `article_stocks` | article_id, stock_id, context, logic                               | 文章↔股票关联    |
| `article_themes` | article_id, theme_id                                               | 文章↔主题关联    |

- `source` 字段值：`study_hot` / `industry_chain` / `action`
- `relevance` 字段：0-10，AI 评估的 A 股相关性（<5 已被过滤不入库）

## 汇报原则

1. **先数据后观点**：先呈现客观数据（标题、股票、逻辑），再给出总结
2. **按热度排序**：优先展示出现频率高的主题和股票
3. **时间敏感**：段子和异动强调时效性，产业链关注长期趋势
4. **中文汇报**：所有输出使用中文
5. **精简有力**：避免大段引用原文，提炼核心信息

## 注意事项

- 每次抓取 study_hot 约需 5~15 分钟（Playwright 浏览器渲染 + AI 解析），请提前告知用户等待
- 如果登录态过期（抓取失败），运行：`cd {skillDir} && uv run python -m a_stock_watcher.auth`
- 数据库查询脚本是即时的，不需要 GEMINI_API_KEY
- 抓取命令必须 source .env 加载环境变量
