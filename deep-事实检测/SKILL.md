---
name: fact-checker
description: 使用 Gemini 多 Agent 架构对 Markdown 文档进行逐句事实核查。Phase1 用 gemini-2.0-flash 拆句+分类(事实/主观)+提取声明；Phase2 用 gemini-2.5-flash + Google Search 逐句核查每个数据点。当用户要求核查文章数据准确性、验证文档中的事实声明、检查报告中的数字/日期/政策引用是否正确时触发。
---

# Fact Checker — 多 Agent 文档事实核查

两阶段流水线架构：
- **Phase 1 (Splitter)**: gemini-2.0-flash → 拆句、分类(factual/subjective)、提取声明
- **Phase 2 (Verifier)**: gemini-2.5-flash + Google Search → 逐句逐声明核查

## 使用方法

```bash
# 完整核查
python {SKILL_DIR}/scripts/fact_checker.py <file.md>

# 指定章节
python {SKILL_DIR}/scripts/fact_checker.py <file.md> --chapters 2,3

# 仅拆句（检查 Phase1 质量，不花搜索费用）
python {SKILL_DIR}/scripts/fact_checker.py <file.md> --split-only

# 预览文档结构
python {SKILL_DIR}/scripts/fact_checker.py <file.md> --dry-run
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出目录 | 文件同目录 |
| `--split-model` | Phase1 模型 | gemini-2.0-flash |
| `--verify-model` | Phase2 模型 | gemini-2.5-flash |
| `--split-concurrency` | Phase1 并发 | 5 |
| `--verify-concurrency` | Phase2 并发 | 3 |
| `--chapters` | 章节过滤 | 全部 |
| `--split-only` | 仅拆句 | false |
| `--dry-run` | 仅解析 | false |

## 输出文件

| 文件 | 说明 |
|------|------|
| `{stem}_sentences.json` | Phase1: 全部句子 + 分类 + 声明 |
| `{stem}_factcheck.json` | Phase2: 完整核查结果 |
| `{stem}_issues.json` | 仅 incorrect / not_found 条目 |

## 编号规则

`C{章}.S{节}.SS{小节}.P{段落}.T{句子}.K{声明}`

示例：`C2.S1.P3.T2.K1` = 第1章(C2) > 第1节 > 第3段 > 第2句 > 第1个声明

## 工作流建议

1. `--dry-run` → 确认文档结构和章节编号
2. `--split-only` → 检查拆句和分类质量
3. 完整核查 → 查看 `_issues.json` 定位问题
4. 对大文档按章节分批核查（`--chapters 2,3` + `--chapters 4,5`）
