# 资产负债表查询与分析

拉取、查询资产负债表数据，支持基础财务分析。

## 使用

```bash
# 拉取单公司数据
python -m analyzers.balancesheet.pipeline fetch --ts-code 000001.SZ --start-date 20240101 --end-date 20241231

# 拉取全量数据（VIP接口，需5000积分）
python -m analyzers.balancesheet.pipeline fetch --period 20241231 --vip

# 查询单字段（自动拉取数据不足时）
python -m analyzers.balancesheet.pipeline query --ts-code 000001.SZ --field inventories

# 查询完整记录
python -m analyzers.balancesheet.pipeline query --ts-code 000001.SZ

# 查询历史数据
python -m analyzers.balancesheet.pipeline history --ts-code 000001.SZ --limit 4
```

## 数据存储

- `balancesheet`: 资产负债表（20个常用字段 + payload_json完整数据）

## 财务分析参考

- `analyzers/financial_analysis/reference.md`: 基础指标定义、财务比率、常见问题分析模板
