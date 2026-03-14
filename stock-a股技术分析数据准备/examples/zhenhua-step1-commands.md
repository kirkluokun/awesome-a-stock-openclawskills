# 振华股份（603067.SH）Step1 命令模板

## 1) 日线（近1年）
```bash
mcporter call tushare-pro.tushare_daily \
  ts_code=603067.SH start_date=2025-03-01 end_date=2026-03-05 _limit=5000
```

## 2) 技术因子（近1年）
```bash
mcporter call tushare-pro.tushare_stk_factor_pro \
  ts_code=603067.SH start_date=2025-03-01 end_date=2026-03-05 _limit=5000
```

## 3) 资金流向（近3个月）
```bash
mcporter call tushare-pro.tushare_moneyflow \
  ts_code=603067.SH start_date=2025-12-01 end_date=2026-03-05 _limit=5000
```

## 4) 落盘目录（规范）
```text
results/zhenhua-tech-analysis/data/raw/
  603067SH_daily_1y.json
  603067SH_stk_factor_pro_1y.json
  603067SH_moneyflow_3m.json
```

## 5) 摘要字段（Step1完成即输出）
- 最新交易日
- 最新收盘
- 近20日涨跌幅
- 条数（日线/因子/资金流）
- 完整性（完整/部分缺失+原因）
