# 主营业务构成

拉取上市公司主营业务构成，支持按产品(P)、地区(D)、行业(I)三种维度拆分。

## 使用

```bash
# 单公司拉取（普通接口，需2000积分）
python fetchers/fina_mainbz.py --ts-code 000001.SZ

# 按类型筛选：P=产品 D=地区 I=行业
python fetchers/fina_mainbz.py --ts-code 000001.SZ --type P

# 指定报告期
python fetchers/fina_mainbz.py --ts-code 000001.SZ --period 20251231

# 单季度全量（VIP接口，需5000积分）
python fetchers/fina_mainbz.py --period 20251231 --vip

# 区间全量（VIP接口，自动拆分季度，含断点续传）
python fetchers/fina_mainbz_vip_batch.py --start-date 20240331 --end-date 20251231
```

## 数据存储

- `fina_mainbz`: 主营业务构成（唯一键：ts_code + end_date + bz_item）
- 字段：`bz_item`(业务名称) `bz_type`(类型) `bz_sales`(营业收入) `bz_profit`(营业利润) `bz_cost`(营业成本) + payload_json 完整数据
