# 现金流量表查询

拉取、查询现金流量表数据，支持单公司与 VIP 全量刷新。

## 使用

```bash
# 单公司拉取（普通接口）
python -m analyzers.cashflow.pipeline fetch --ts-code 000001.SZ --start-date 20240331 --end-date 20241231

# 单季度全量（VIP接口）
python -m analyzers.cashflow.pipeline fetch --period 20240331 --vip

# 区间全量（VIP接口，自动拆分季度）
python fetchers/cashflow_vip_batch.py --start-date 20240331 --end-date 20251231

# 查询单字段（自动拉取数据不足时）
python -m analyzers.cashflow.pipeline query --ts-code 000001.SZ --field n_cashflow_act

# 查询历史
python -m analyzers.cashflow.pipeline history --ts-code 000001.SZ --limit 4
```

## 数据存储

- `cashflow`: 现金流量表（7个常用字段 + payload_json完整数据）
