---
name: stock-tech-analysis-step1
description: A股技术分析第一步（数据获取与最小校验）。严格优先使用 tushare-mcp（通过 mcporter 调用 tushare-pro.*）拉取日线、技术因子、资金流并落盘到 results/project-name/data/raw。
when: 当用户要求“先拉数据再做技术分析”、"用tushare做第一步"、"获取某只A股日线/因子/资金流"、"技术分析第一步" 时使用。
examples:
  - "先把振华股份的数据拉一下"
  - "用 tushare mcp 做技术分析第一步"
  - "先获取日线、因子、资金流，落盘后再分析"
metadata:
  {
    "openclaw": {
      "emoji": "📈",
      "requires": { "bins": ["mcporter", "python3"] }
    }
  }
---

# stock-tech-analysis-step1

## 目标
把技术分析流程中的**第一步（数据底座）**标准化：
1. 仅使用 `tushare-mcp`（经 `mcporter`）获取数据
2. 最小校验（不做重清洗）
3. 数据落盘到 `results/project-name/data/raw/`
4. 给出可直接进入 Step 2 技术分析的摘要

## 数据范围（默认）
- 标的：用户指定（A股格式 `XXXXXX.SH/SZ`）
- 日线：近 1 年（`tushare_daily`）
- 技术因子：近 1 年（`tushare_stk_factor_pro`）
- 资金流向：近 3 个月（`tushare_moneyflow`）

## 核心规则
1. **数据源唯一**：优先且默认只用 `tushare-mcp`
2. **接口调用方式**：`mcporter call tushare-pro.<tool>`
3. **落盘规范**：`results/<project-name>/data/raw/`
4. **最小校验**：仅检查条数、关键字段、最新交易日与最新收盘
5. **摘要必须输出**：最新交易日、最新收盘、近20日涨跌幅、数据条数、完整性

## 标准执行模板

### 1) 日线
```bash
mcporter call tushare-pro.tushare_daily \
  ts_code=603067.SH start_date=2025-03-01 end_date=2026-03-05 _limit=5000
```

### 2) 技术因子
```bash
mcporter call tushare-pro.tushare_stk_factor_pro \
  ts_code=603067.SH start_date=2025-03-01 end_date=2026-03-05 _limit=5000
```

### 3) 资金流向
```bash
mcporter call tushare-pro.tushare_moneyflow \
  ts_code=603067.SH start_date=2025-12-01 end_date=2026-03-05 _limit=5000
```

## 输出文件命名建议
- `<ts_code>_daily_1y.json`
- `<ts_code>_stk_factor_pro_1y.json`
- `<ts_code>_moneyflow_3m.json`

## 最小检查清单
- [ ] 三份数据都成功返回
- [ ] 日线/因子条数大于 0
- [ ] 最新交易日可识别
- [ ] 最新收盘价可读取
- [ ] 可计算近20日涨跌幅

## 失败回退（轻量）
- 若 `tushare_stk_factor_pro` 不可用：明确报错原因（权限/接口不可用），保留日线与资金流并继续流程。
- 若 `mcporter` 未配置 `tushare-pro`：先修复 MCP 注册与 token，再重试。

## 交付摘要模板
- 标的：603067.SH
- 最新交易日：YYYYMMDD
- 最新收盘：XX.XX
- 近20日涨跌幅：XX.XX%
- 数据条数：日线 N / 因子 N / 资金流 N
- 完整性：完整 / 部分缺失（注明原因）
