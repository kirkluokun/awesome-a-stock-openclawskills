# 财务指标查询

拉取、查询财务指标数据，支持单公司与 VIP 全量刷新。

## 使用

```bash
# 单公司拉取（普通接口）
python -m analyzers.fina_indicator.pipeline fetch --ts-code 000001.SZ --start-date 20240331 --end-date 20241231

# 单季度全量（VIP接口）
python -m analyzers.fina_indicator.pipeline fetch --period 20240331 --vip

# 区间全量（VIP接口，自动拆分季度）
python fetchers/fina_indicator_vip_batch.py --start-date 20240331 --end-date 20251231

# 查询单字段
python -m analyzers.fina_indicator.pipeline query --ts-code 000001.SZ --field roe

# 查询历史
python -m analyzers.fina_indicator.pipeline history --ts-code 000001.SZ --limit 4
```

## 数据存储

- `fina_indicator`: 财务指标（12个常用字段 + payload_json完整数据）

## 字段清单参考

- `docs/financial-indicators.md`: 财务指标字段完整清单（字段名 + 中文含义）
