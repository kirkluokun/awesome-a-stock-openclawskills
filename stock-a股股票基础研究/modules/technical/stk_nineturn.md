# 神奇九转指标

基于 Tom DeMark TD序列的趋势反转指标，识别连续9天特定走势判断潜在反转点。数据从 20230101 开始，每天 21 点更新。

## 核心字段

| 字段 | 说明 |
|------|------|
| up_count | 连续上涨计数 |
| down_count | 连续下跌计数 |
| nine_up_turn | `+9` 表示上涨九转信号（潜在见顶） |
| nine_down_turn | `-9` 表示下跌九转信号（潜在见底） |

## 使用

```bash
# 单日全市场（日线）
python fetchers/stk_nineturn.py --trade-date "2026-02-06 00:00:00"

# 单只股票
python fetchers/stk_nineturn.py --ts-code 000001.SZ --start-date 20260101 --end-date 20260206

# 60 分钟级别
python fetchers/stk_nineturn.py --ts-code 000001.SZ --freq 60min

# 批量拉取（按交易日逐天，含断点续拉）
python fetchers/stk_nineturn_batch.py --start-date 20230101 --end-date 20260206

# 重新拉取（忽略进度）
python fetchers/stk_nineturn_batch.py --start-date 20230101 --end-date 20260206 --no-resume

# 自定义间隔
python fetchers/stk_nineturn_batch.py --start-date 20230101 --end-date 20260206 --delay 0.3
```

## 接口限制

- 需 6000 积分
- 单次最多 10000 条（按 trade_date 拉取，每天 ~5500 条，无需分页）
- 默认 0.2s 间隔

## 数据存储

- 表：`stk_nineturn`（唯一键：ts_code + trade_date + freq）
- 信号列：`nine_up_turn`（+9 见顶）/ `nine_down_turn`（-9 见底）已建索引
- `payload_json` 保存完整原始数据
- 进度文件：`data/stk_nineturn_progress.json` + `data/stk_nineturn_progress.log`
