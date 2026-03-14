# 架构说明

## 三层职责

| 层级 | 目录 | 职责 | 输入 → 输出 |
|------|------|------|-------------|
| 获取层 | `fetchers/` | 从外部 API 拉取原始数据 | API 参数 → DB/CSV |
| 分析层 | `analyzers/` | 数据处理、计算、对比 | DB → 结构化结果 |
| 解释层 | `interpreters/` | 生成人类可读报告 | JSON/DB → 文字/CSV |

## 数据流

```
Tushare API → fetchers/ → data/finance.db → analyzers/ → interpreters/ → output/
```

## 分析域

| 域 | 目录 | 模块文档 |
|----|------|----------|
| 财务分析 | `analyzers/earnings/` `balancesheet/` `cashflow/` `fina_indicator/` | `modules/fundamental/` |
| 通用数据 | `analyzers/research/` `broker_recommend/` `stk_surv/` | `modules/data/` |
| 技术分析 | TODO | `modules/technical/` |
| 舆情分析 | TODO | `modules/sentiment/` |

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 获取脚本 | `{数据类型}.py` | `balancesheet.py` |
| 分析目录 | `{业务场景}/` | `earnings/`, `cashflow/` |
| 共用模块 | `_shared/` | 下划线前缀，区分业务脚本 |
| 流程入口 | `pipeline.py` | 每个分析场景的统一入口 |
| 表结构 | `schema.sql` | 每个分析目录内 |

## 扩展步骤

1. `fetchers/` 新建 `{数据类型}.py`
2. `analyzers/` 对应域下新建目录，含 `_shared/db.py` + `schema.sql` + `pipeline.py`
3. 需要报告输出时，`interpreters/` 新建对应目录
4. `modules/{域}/` 新建模块文档
5. `sync_registry.json` 追加同步条目
6. SKILL.md 模块索引表追加一行

## 全量同步

`full_sync.py` 读取 `sync_registry.json` 注册表，顺序执行所有 `enabled: true` 的步骤。

注册表支持变量：`{today}` `{first_period}` `{last_period}`（由 Period 自适应规则自动计算）。
