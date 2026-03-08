---
name: tushare-mcp
description: 通过 Tushare Pro MCP 获取中国金融市场数据。覆盖 A股/港股/美股/基金/期货/债券/宏观 共 158+ 个接口。当需要股价、财务、指数、宏观数据时，使用 tushare_* MCP tool 而非 Python 脚本。
allowed-tools:
  - "mcp__tushare-pro__tushare_*"
---

# Tushare MCP 数据技能

> 鉴权变量：`TUSHARE_API_KEY`。

通过 MCP 服务器调用 Tushare Pro API，**不再需要写 Python 脚本**。

## 核心规则

1. **使用 MCP tool，不写脚本** — 所有数据通过 `tushare_*` tool 获取
2. **先用 ToolSearch 加载** — MCP tool 是 deferred 的，调用前必须 `ToolSearch("tushare ...")` 加载
3. **日期格式 YYYYMMDD 或 YYYY-MM-DD** — 两种都支持，MCP 内部自动转换
4. **默认返回 100 行** — 需要更多数据用 `_limit` 参数
5. **数据输出遵循存储规范** — 见 [output-storage.md](reference/output-storage.md)

## 使用流程

```
1. 确认需求 → 需要什么数据？
2. 查 tool 索引 → reference/tool-index.md 找到对应 tool
3. ToolSearch 加载 → ToolSearch("+tushare <关键词>")
4. 调用 tool → 传参获取数据
5. 存储/展示 → 按 output-storage.md 规范处理
```

## 快速定位 Tool

| 需求场景 | 用哪个 tool | 关键参数 |
|---------|------------|---------|
| 查某只股票行情 | `tushare_daily` | ts_code, start_date, end_date |
| 查财务三表 | `tushare_income/balancesheet/cashflow` | ts_code, period |
| 查指数走势 | `tushare_index_daily` | ts_code, start_date, end_date |
| 查 ETF 行情 | `tushare_fund_daily` | ts_code, trade_date |
| 查港股行情 | `tushare_hk_daily` | ts_code, start_date, end_date |
| 查美股行情 | `tushare_us_daily` | ts_code, start_date, end_date |
| 查宏观 GDP | `tushare_cn_gdp` | q（季度如 2024Q1） |
| 查利率 Shibor | `tushare_shibor` | start_date, end_date |
| 查龙虎榜 | `tushare_top_list` | trade_date |
| 查研究报告 | `tushare_research_report` | ts_code, start_date, end_date |
| 技术面因子 | `tushare_stk_factor_pro` | ts_code, start_date, end_date |
| 筹码分布 | `tushare_cyq_chips` | ts_code, trade_date |
| 涨跌停统计 | `tushare_limit_list_d` | trade_date |
| 资金流向 | `tushare_moneyflow` | ts_code, trade_date |
| 融资融券 | `tushare_margin` | trade_date |
| 实时分钟线 | `tushare_rt_min` | ts_code |

**完整 tool 索引**：[reference/tool-index.md](reference/tool-index.md)

## 代码格式说明

| 市场 | 代码格式 | 示例 |
|------|---------|------|
| 沪市 | XXXXXX.SH | 600000.SH |
| 深市 | XXXXXX.SZ | 000001.SZ |
| 北交所 | XXXXXX.BJ | 430047.BJ |
| 港股 | XXXXX.HK | 00700.HK |
| 美股 | TICKER | AAPL |
| 指数 | XXXXXX.SH/SZ | 000001.SH（上证综指） |
| ETF | XXXXXX.SH/SZ | 510050.SH |
| 期货 | 品种代码.交易所 | CU2401.SHF |

## 已知限制

- 港股/美股财务数据需 15000 积分，积分不足会报错
- 部分高级接口需要单独开通权限（如 rt_min 实时分钟线）
- 单次请求默认 100 行上限，大批量需多次请求或调 `_limit`

## 调研纪要/PDF 场景

需要处理“调研纪要原文/关注问题”时，先读：
- [调研纪要/PDF 处理指引](reference/research-notes-pdf.md)

## 参考

- [Tool 完整索引](reference/tool-index.md) — 按场景分类的 158 个 tool
- [数据输出规范](reference/output-storage.md) — 文件存储路径和格式
- [查询模式手册](reference/query-patterns.md) — 常见分析场景的 tool 组合
- [调研纪要/PDF 处理指引](reference/research-notes-pdf.md) — 纪要抓取、权限回退与输出模板
