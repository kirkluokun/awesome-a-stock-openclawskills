---
name: stock-research-group
description: 股票研究组，提供业绩监控（预期对比）、券商研报搜索与解析（Gemini 提取观点）、券商月度金股统计、机构调研检索、资产负债表查询与分析、主营业务构成分析、技术面因子、神奇九转
triggers:
  - A股
  - 沪深
  - 科创板
  - 创业板
  - 券商研报
  - 机构调研
  - 资产负债表
  - 主营业务
  - 技术面因子
  - 技术分析
  - 神奇九转
  - 九转序列
  - 抄底
  - 逃顶
---

# Stock Research Group

股票研究工具集：业绩预期对比告警、券商研报搜索下载与 AI 解析、券商月度金股统计、机构调研检索、资产负债表查询与分析。

## 数据源

| 接口 | 说明 | 拉取方式 |
|------|------|----------|
| `forecast_vip` | 业绩预告 | `period` 按报告期全量 |
| `express_vip` | 业绩快报 | `period` 按报告期全量 |
| `income_vip` | 正式业绩 | `period` 按报告期全量 |
| `report_rc` | 券商盈利预测 | `start_date` + `end_date` 按日期范围（支持分页） |

## Period 自适应规则

`ingest.py` 根据当前日期**自动计算** period，无需手动指定：

| 时间窗口 | 自动拉取的 period | 说明 |
|----------|------------------|------|
| 1月1日 - 4月30日 | `上年1231` + `当年0331` | 年报 + Q1 披露季 |
| 5月1日 - 8月31日 | `当年0630` | 中报披露季 |
| 9月1日 - 10月31日 | `当年0930` | Q3 披露季 |
| 11月1日 - 12月31日 | `当年1231` | 年报预披露期 |

**示例**：2026年2月3日自动拉取 `20251231` + `20260331`

## 模块索引

| 域 | 模块 | 关键词 | 说明 | 参考文档 |
|----|------|--------|------|----------|
| 财务分析 | 业绩监控 | 业绩预告/快报/超预期/符合预期 | 实际业绩 vs 券商预测，生成告警 | `modules/fundamental/earnings.md` |
| 财务分析 | 资产负债表 | 资产负债表/资产 | 拉取查询资产负债表数据 | `modules/fundamental/balancesheet.md` |
| 财务分析 | 财务指标 | 财务指标/ROE/ROA | 拉取查询财务指标数据 | `modules/fundamental/fina_indicator.md` |
| 财务分析 | 现金流量表 | 现金流量表/现金流 | 拉取查询现金流量表数据 | `modules/fundamental/cashflow.md` |
| 财务分析 | 主营业务构成 | 主营业务/产品构成/地区构成 | 按产品/地区/行业拆分主营收入 | `modules/fundamental/fina_mainbz.md` |
| 通用数据 | 券商研报 | 研报/解析/PDF | 搜索下载+Gemini提取观点 | `modules/data/research_report.md` |
| 通用数据 | 券商金股 | 金股/月度金股 | 拉取统计券商月度金股 | `modules/data/broker_recommend.md` |
| 通用数据 | 机构调研 | 机构调研/调研 | 按公司/机构/人员检索调研 | `modules/data/stk_surv.md` |
| 技术分析 | 技术面因子 | 技术面因子/MACD/KDJ/RSI/布林带/均线 | 日频261维因子，含前复权/后复权/不复权 | `modules/technical/stk_factor_pro.md` |
| 技术分析 | 神奇九转 | 神奇九转/九转序列/抄底/逃顶 | TD序列反转信号，日线+60min | `modules/technical/stk_nineturn.md` |
| 舆情分析 | — | 新闻/舆情/股吧 | TODO | `modules/sentiment/_index.md` |

---

## 全量数据刷新

`full_sync.py` 一次性拉取所有数据源并更新数据库。Period 自动计算，日志保存到 `logs/full_sync_YYYYMMDD_HHMMSS.log`。

```bash
cd stock-research-group

# 执行全量刷新（自动计算 period）
python full_sync.py

# 指定基准日期
python full_sync.py --date 20260208

# 预览步骤（不执行）
python full_sync.py --dry-run
```

步骤由 `sync_registry.json` 注册表驱动，新增模块只需在注册表追加条目，设 `enabled: false` 可跳过。

单步失败不阻塞后续执行，末尾输出汇总（成功/失败数、耗时）。VIP 步骤需 5000 积分。

---

## 操作约定

**用户偏好**：
- 当用户要求"读研报/读一下/解析"时，直接执行下载与解析流程，无需再次征求审批。
