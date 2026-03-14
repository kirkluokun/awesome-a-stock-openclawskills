---
name: stock-cross-verify
description: 股票信息多源交叉验证系统。针对用户的股票问题，自动并行调度多个信息源（券商研报、专家纪要、外资行报告、机构热议、新闻、社交舆情），由主 Agent 执行 capture 采集，Gemini 负责信息梳理组织，最终通过 War Room 多智能体辩论完成交叉验证——对比信息异同、逻辑异同、数据异同、结论异同，输出结构化验证报告。触发词："交叉验证"、"多源验证"、"帮我验证一下[话题]"、"各方怎么看[股票]"、"[股票]的消息可靠吗"。
---

# 股票信息多源交叉验证

针对股票/行业/宏观问题，自动调度 11 个信息源并行采集，用 Gemini 梳理，用 War Room 辩论验证，输出**共识 / 分歧 / 待验证**三区报告。

---

## 信息源路由表

### 第一层：核心投研（主 Agent 执行 capture）

| 信息源 | 擅长领域 | 技能 | 典型命令 |
|--------|---------|------|---------|
| **岗底斯** | 快速全面获取市场边际信息（研报/公告/纪要/指标） | `capture-gangtise` | `python3 {gangtise}/scripts/query_kb.py "{query}"` |
| **AlphaPAI** | A股全面信息（机构热议/路演纪要/点评/AI问答） | `capture-alphapai` | `python3 {alphapai}/scripts/alphapai_api.py search "{query}" --save` |
| **AceCamp** | 市场核心专家纪要内容 | `capture-acecamp` | `python3 {acecamp}/scripts/acecamp_fetch.py fetch "{query}" --limit 5` |
| **AlphaEngine** | 外资行报告（大摩/高盛/瑞银等） | `capture-alphaengine` | `python3 {alphaengine}/scripts/alphaengine_api.py search "{query}" --save` |

### 第二层：舆情（Gemini CLI 可执行）

| 信息源 | 擅长领域 | 技能 | 典型命令 |
|--------|---------|------|---------|
| **Reddit** | 海外投资者讨论、科技政治舆情 | `capture-reddit-search` | `{reddit}/scripts/reddit-search search "{query}" 10` |
| **X/Twitter** | 实时舆论、KOL观点 | `capture-search-x` | `node {searchx}/scripts/search.js --days 7 "{query}"` |

### 第三层：新闻（Gemini CLI 可执行）

| 信息源 | 擅长领域 | 技能 | 典型命令 |
|--------|---------|------|---------|
| **NewsAPI** | 全球5000+新闻源搜索 | `news-newsapi-search` | `node {newsapi}/scripts/search.js "{query}" --days 7` |
| **新闻聚合** | HN/36Kr/华尔街见闻/微博等8源 | `news-aggregator-skill` | `python3 {aggregator}/scripts/fetch_news.py --source all --limit 10 --keyword "{query}" --deep` |

> **路径说明**：`{gangtise}` 等为各技能的 `{skillDir}` 路径，实际执行时替换为技能安装的绝对路径。

---

## Phase 1：意图解析

**在做任何事之前**，先解析用户问题：

```
输入："贵州茅台最近怎么了"
拆解：
  SUBJECT = "贵州茅台"
  TICKER = "600519.SH"（如能识别）
  DIMENSIONS = [基本面, 市场情绪, 行业动态]
  QUERY_KEYWORDS = ["贵州茅台", "茅台", "白酒行业"]
  ENGLISH_KEYWORDS = ["Kweichow Moutai", "baijiu"]（用于海外源）
  URGENCY = normal | urgent（影响信息源选取数量）
```

**维度映射规则：**

| 问题类型 | 核心维度 | 优先信息源 |
|---------|---------|----------|
| 个股基本面 | 财报、估值、业务 | gangtise + alphapai + acecamp |
| 行业趋势 | 行业格局、政策 | gangtise + aggregator + newsapi |
| 事件驱动 | 并购、政策、危机 | newsapi + X + alphapai |
| 海外视角 | 外资观点、全球配置 | alphaengine + reddit + X |
| 舆情评估 | 市场情绪、散户/机构分歧 | X + reddit + alphapai(hot-stock) |

---

## Phase 2：并行信息采集

### 分工原则

- **主 Agent（Claude）执行**：需要认证 token 的 capture 任务（gangtise / alphapai / acecamp / alphaengine）
- **Gemini CLI 执行**：无认证要求的简单搜索（reddit / X / newsapi / news-aggregator）

### Wave A：核心投研（Claude 执行）

按维度选择性执行，不需要每次全部调用：

```bash
# 1. 岗底斯——快速获取边际信息
python3 {gangtise}/scripts/query_kb.py "{QUERY_KEYWORDS[0]}" --top 10
# 如有 ticker，补充盈利预测
python3 {gangtise}/scripts/forecast.py {TICKER}

# 2. AlphaPAI——机构视角
python3 {alphapai}/scripts/alphapai_api.py search "{QUERY_KEYWORDS[0]}" --save
python3 {alphapai}/scripts/alphapai_api.py roadshow-search "{QUERY_KEYWORDS[0]}" --save --limit 5

# 3. AceCamp——专家纪要
python3 {acecamp}/scripts/acecamp_fetch.py fetch "{QUERY_KEYWORDS[0]}" --limit 3

# 4. AlphaEngine——外资行（仅海外视角维度时）
python3 {alphaengine}/scripts/alphaengine_api.py search "{ENGLISH_KEYWORDS[0]}" --save
```

**每个 capture 命令执行后**，将返回的内容保存到工作目录：

```
output/sources/
├── gangtise_kb.md          # 岗底斯知识库搜索结果
├── gangtise_forecast.md    # 盈利预测（如有）
├── alphapai_search.md      # AlphaPAI 综合搜索
├── alphapai_roadshow.md    # 路演纪要
├── acecamp_articles/       # AceCamp 纪要全文
│   ├── 001_标题.md
│   └── 002_标题.md
└── alphaengine_reports.md  # 外资行报告摘要
```

### Wave B：舆情+新闻（Gemini CLI 执行）

通过 Gemini CLI 或 `mcp__gemini__gemini-query` 驱动执行，适合简单任务：

```bash
# 方式一：直接用 gemini CLI
gemini -m gemini-2.5-flash "
请帮我执行以下搜索命令，并将结果整理为 markdown：

1. Reddit 搜索：
   运行 {reddit}/scripts/reddit-search search '{ENGLISH_KEYWORDS[0]}' 10
   
2. X/Twitter 搜索：
   运行 node {searchx}/scripts/search.js --days 7 '{ENGLISH_KEYWORDS[0]}'

3. 新闻搜索：
   运行 node {newsapi}/scripts/search.js '{QUERY_KEYWORDS[0]}' --days 7

将每个来源的结果整理成以下格式保存到 output/sources/sentiment.md：
## [来源名]
- 主要观点 1（附来源链接）
- 主要观点 2
...
"

# 方式二：通过 Gemini MCP（更可控）
# 用 mcp__gemini__gemini-query，model=flash，thinkingLevel=low
```

**Gemini 无法执行 capture 时的降级方案**：由主 Agent 串行执行 Wave B 的命令。

---

## Phase 3：信息梳理（Gemini 执行）

所有采集完成后，通过 Gemini 对 `output/sources/` 下的全部文件进行阅读和结构化整理：

```
通过 Gemini MCP（mcp__gemini__gemini-query，model=pro，thinkingLevel=high）：

prompt: |
  你是一名资深卖方分析师助理。请阅读以下多个信息源的原始内容，
  按以下维度整理成结构化摘要。

  信息源文件：
  [将 output/sources/ 下所有文件内容粘贴]

  请按以下结构输出：

  ## 一、事实层（各源的客观数据）
  | 数据点 | gangtise | alphapai | acecamp | alphaengine | 新闻 | 舆情 |
  |--------|---------|---------|---------|------------|------|------|
  | 最新营收 | ... | ... | - | ... | - | - |
  | 估值水平 | ... | ... | - | ... | - | - |
  | ... | | | | | | |

  ## 二、观点层（各源的判断和推理）
  | 议题 | 看多观点（来源） | 看空观点（来源） | 中性/不确定（来源） |
  |------|--------------|--------------|----------------|
  | ... | | | |

  ## 三、信号层（异常/分歧/矛盾）
  - 数据矛盾：...
  - 逻辑分歧：...
  - 信息缺口：...

  ## 四、信息源可信度权重
  | 来源 | 类型 | 时效性 | 独立性 | 建议权重 |
  |------|------|--------|--------|---------|
  | gangtise | 券商研报 | 高 | 中 | 0.25 |
  | ... | | | | |
```

梳理结果保存到 `output/organized/structured_summary.md`。

---

## Phase 4：War Room 交叉验证

**核心环节**。调用 `swarm-war-room` 进行多智能体辩论，对比孰真孰假。

### 初始化 War Room

```bash
bash {warroom}/scripts/init_war_room.sh cross-verify-{SUBJECT}
```

### BRIEF.md 填写

```markdown
# 交叉验证任务

## 标的：{SUBJECT}（{TICKER}）
## 核心问题：{用户原始问题}
## 信息源摘要：见 output/organized/structured_summary.md
## 验证目标：
1. 各信息源的事实是否一致？数据冲突如何解释？
2. 各方的推理逻辑是否自洽？有无逻辑谬误？
3. 看多/看空的结论分歧根源是什么？
4. 哪些信息可以交叉确认为高可信度？哪些存疑？
```

### 角色配置

| 角色 | 职责 | 重点维度 |
|------|------|---------|
| **BULL**（多方立论者） | 从信息中提取所有支持看多的证据链 | 增长逻辑、催化剂、低估证据 |
| **BEAR**（空方立论者） | 从信息中提取所有支持看空的证据链 | 风险因素、高估证据、逻辑缺陷 |
| **FACT-CHECKER**（事实核查员） | 逐条核对各源数据是否吻合，标注矛盾 | 数据一致性、时间戳、来源可靠性 |
| **CHAOS**（魔鬼代言人） | 攻击所有角色的论点，找致命盲点 | 反共识思维、黑天鹅、信息操纵可能 |

### 执行 Wave 协议

```
Wave 1：BULL + BEAR 并行——各自从 structured_summary.md 提取己方证据链
       → CHAOS 影子审查（攻击双方逻辑薄弱环节）

Wave 2：FACT-CHECKER 逐条核对 Wave 1 中 BULL 和 BEAR 引用的数据点
       → CHAOS 影子审查（质疑核查标准是否足够严格）

Consolidation：合并四方输出，生成交叉验证报告
```

### 对比维度（FACT-CHECKER 逐项检查）

```
┌─ 信息异同 ────────────────────────────┐
│ 哪些事实各源都报道了（高可信度）？        │
│ 哪些事实仅单一源提及（需二次验证）？      │
│ 哪些重要信息某些源有意/无意遗漏？         │
└─────────────────────────────────────┘

┌─ 数据异同 ────────────────────────────┐
│ 同一数据点各源报告值是否一致？            │
│ 不一致时，偏差来源是什么（口径/时间/计算）？│
│ 哪些数字可交叉确认？                     │
└─────────────────────────────────────┘

┌─ 逻辑异同 ────────────────────────────┐
│ 各源的推理链条是否自洽？                  │
│ 是否存在"用结论推数据"的循环论证？        │
│ 各方假设的前提条件是否明确？              │
└─────────────────────────────────────┘

┌─ 结论异同 ────────────────────────────┐
│ 看多/看空/中性各有几个源支持？            │
│ 分歧的根源是事实分歧还是框架分歧？        │
│ 是否存在信息不对称导致的结论差异？         │
└─────────────────────────────────────┘
```

---

## Phase 5：输出交叉验证报告

最终报告模板：

```markdown
# {SUBJECT} 交叉验证报告

**验证时间**：{datetime}
**核心问题**：{用户原始问题}
**信息源数量**：{N} 个（{列出实际使用的源}）

---

## 🟢 共识区（高可信度）

各信息源交叉确认的事实和结论：
1. [事实/结论]（来源：gangtise + alphapai + acecamp，3源确认）
2. ...

## 🟡 分歧区（需判断）

各信息源存在不同观点或数据的领域：

### 分歧 1：[议题]
| 立场 | 核心论据 | 来源 | CHAOS 评估 |
|------|---------|------|-----------|
| 多方 | ... | ... | SURVIVE / WOUNDED / KILLED |
| 空方 | ... | ... | SURVIVE / WOUNDED / KILLED |

**FACT-CHECKER 判定**：数据[一致/有X%偏差]，逻辑[自洽/存在Y缺陷]

### 分歧 2：...

## 🔴 待验证区（信息不足）

单一来源提及、尚无法交叉确认的信息：
1. [信息]（仅来源：X）——建议验证方式：...
2. ...

## 📊 信息源可信度矩阵

| 来源 | 本次覆盖 | 时效性 | 独立性 | 与其他源一致率 | 综合权重 |
|------|---------|--------|--------|-------------|---------|
| ... | ✅/❌ | 高/中/低 | 高/中/低 | X% | 0.XX |

## 💡 结论与建议

[基于共识区和分歧区的综合研判，以及后续应关注的催化剂/风险点]
```

报告保存至 `output/report_{SUBJECT}_{date}.md`。

---

## 快速模式 vs 深度模式

| 模式 | 跳过 | 耗时 | 适用场景 |
|------|------|------|---------|
| **快速模式**（`--quick`） | 跳过 War Room，P3 梳理后直接输出初步综合 | 3-5分钟 | 日常快速验证 |
| **深度模式**（默认） | 完整 P1→P5 | 10-20分钟 | 重要投资决策 |
| **聚焦模式**（`--focus [源]`） | 仅用指定信息源 | 1-3分钟 | 快速查单一视角 |

快速模式下跳过 Phase 4，Phase 3 输出即为最终报告（无辩论验证）。

---

## 执行示例

```
用户：帮我交叉验证一下贵州茅台最近的情况

Agent：
  P1 → 解析：SUBJECT=贵州茅台, TICKER=600519.SH, DIMENSIONS=[基本面, 市场情绪]
  P2 → 并行执行：
       [Claude] gangtise 搜索"贵州茅台" + 盈利预测
       [Claude] alphapai 搜索"贵州茅台" + 路演纪要
       [Claude] acecamp 搜索"贵州茅台"
       [Gemini] newsapi 搜索"贵州茅台"
       [Gemini] X 搜索"Kweichow Moutai"
  P3 → Gemini 读取 output/sources/ 全部文件，输出 structured_summary.md
  P4 → War Room: BULL+BEAR+FACT-CHECKER+CHAOS 辩论
  P5 → 输出交叉验证报告
```

---

## 注意事项

- **Token 管理**：各 capture 技能的认证状态独立管理，执行前无需在本技能中处理
- **降级策略**：若某信息源 API 报错，标注为"本次未覆盖"继续执行，不中断流程
- **Gemini 调用**：优先用 `mcp__gemini__gemini-query`（model=pro），降级用 `gemini` CLI
- **信息时效**：所有信息标注获取时间，超过 7 天的数据在报告中标注 ⚠️
- **安全**：本技能不存储任何凭证，所有认证由各子技能自行管理
