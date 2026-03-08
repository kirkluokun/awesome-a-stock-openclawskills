# Fact Checker — 多 Agent 文档事实核查工具

## 概述

使用 **两阶段流水线架构** 对 Markdown 文档进行逐句事实核查。

- **Phase 1 (Splitter)**: `gemini-2.0-flash` → 拆句、分类(事实/主观)、提取声明
- **Phase 2 (Verifier)**: `gemini-2.5-flash + Google Search` → 逐句逐声明核查

## 快速开始

```bash
cd fact-checker

# 完整核查
python scripts/fact_checker.py article.md

# 仅查看拆句结果（不花搜索费用）
python scripts/fact_checker.py article.md --split-only

# 指定章节
python scripts/fact_checker.py article.md --chapters 2,3,4

# 预览文档结构
python scripts/fact_checker.py article.md --dry-run
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `{stem}_sentences.json` | Phase1: 全部句子 + 分类(factual/subjective) + 声明列表 |
| `{stem}_factcheck.json` | Phase2: 完整核查结果（包含 verified/incorrect/not_found） |
| `{stem}_issues.json` | 仅包含有问题的数据点（incorrect 或 not_found），用于后续修改 |

## 编号系统

每个声明都有唯一编号：`C{章}.S{节}.SS{小节}.P{段}.T{句}.K{声明}`

例：`C2.S1.P3.T2.K1` 
- C2 = 第一章
- S1 = 第一节  
- P3 = 第3段
- T2 = 第2个句子
- K1 = 第1个声明

## 分类规则

### Factual（需核查）
- 具体数字、金额、百分比
- 日期和时间点
- 法律法规名称及具体内容
- 组织/公司的具体行为
- 排名、市场份额、产量数据
- 具体政策参数

### Subjective（跳过）
- 主观判断、评论
- 未来预测、展望
- 比喻、类比、修辞
- 包含 "说白了"、"我认为"、"预计"、"意味着" 等标志词

## 参数说明

```
--split-model MODEL          Phase1 模型（默认 gemini-2.0-flash）
--verify-model MODEL         Phase2 模型（默认 gemini-2.5-flash）
--split-concurrency N        Phase1 并发数（默认 5）
--verify-concurrency N       Phase2 并发数（默认 3）
--chapters CHAPTERS          指定章节（逗号分隔，如 2,3,4）
--split-only                 仅执行拆句，不核查
--dry-run                    仅解析文档结构
-o, --output DIR             输出目录
```

## 工作流建议

1. **预览阶段**
   ```bash
   python scripts/fact_checker.py doc.md --dry-run
   ```
   确认文档结构和编号

2. **拆句检验**
   ```bash
   python scripts/fact_checker.py doc.md --split-only -o output/
   ```
   检查分类质量，不花搜索费用

3. **完整核查**
   ```bash
   python scripts/fact_checker.py doc.md -o output/
   ```
   查看 `_issues.json` 定位问题

4. **分批处理大文档**
   ```bash
   python scripts/fact_checker.py doc.md --chapters 2,3 -o output/
   python scripts/fact_checker.py doc.md --chapters 4,5 -o output/
   ```
   分散 API 调用压力

## 环境要求

- Python 3.10+
- `google-genai` 库
- `GOOGLE_API_KEY` 或 `GEMINI_API_KEY` 环境变量

## 核查结果解读

### Verdict 含义

| 状态 | 说明 |
|------|------|
| `verified` | 数据准确，搜索确认无误 |
| `incorrect` | 数据有误，提供了正确数据和来源 |
| `not_found` | 无法在搜索结果中找到确认 |

### 示例输出

```json
{
  "id": "C2.S1.P3.T2.K1",
  "sentence": "据财政部测算，若严守禁令，仅出口关税一项就将面临 10万亿印尼盾 的损失。",
  "claim": "出口关税损失为10万亿印尼盾",
  "verdict": "verified",
  "details": "根据印尼财政部海关总署司长 Askolani 的声明确认...",
  "sources": ["https://..."]
}
```

## 成本优化

- Phase1 使用 `gemini-2.0-flash`（更便宜），无搜索
- Phase2 使用 `gemini-2.5-flash`（需搜索），仅对事实句运行
- 主观句自动跳过，节省 30-40% 的搜索成本
- 使用 `--split-only` 先审查质量，再决定是否进行 Phase2

## 已知限制

- 不支持超过 100KB 的单个 Markdown 文件（建议分章节处理）
- 搜索结果依赖 Google Search API 的覆盖范围（冷门数据可能找不到）
- 并发数过高可能触发 API 限流（推荐 Phase1: 5，Phase2: 3）
