# 股票技术面因子（专业版）

日频技术面因子数据，261维，覆盖全A股全历史。由 Tushare 社区自产。

## 因子分类

| 类别 | 因子 | 后缀含义 |
|------|------|----------|
| 价格 | open/high/low/close/pre_close | _bfq 不复权 _qfq 前复权 _hfq 后复权 |
| 量价 | vol/amount/turnover_rate/volume_ratio | — |
| 估值 | pe/pe_ttm/pb/ps/ps_ttm/dv_ratio/dv_ttm | — |
| 市值 | total_mv/circ_mv/total_share/float_share/free_share | — |
| 趋势 | MA(5/10/20/30/60/90/250)/EMA/EXPMA | _bfq/_qfq/_hfq |
| MACD | macd_dif/macd_dea/macd | _bfq/_qfq/_hfq |
| KDJ | kdj_k/kdj_d/kdj | _bfq/_qfq/_hfq |
| RSI | rsi_6/rsi_12/rsi_24 | _bfq/_qfq/_hfq |
| BOLL | boll_upper/boll_mid/boll_lower | _bfq/_qfq/_hfq |
| 其他 | CCI/CR/DMI/OBV/WR/TRIX/MFI/MTM/ROC/PSY/VR 等 | _bfq/_qfq/_hfq |

## 使用

```bash
# 单只股票拉取（指定日期范围）
python fetchers/stk_factor_pro.py --ts-code 000001.SZ --start-date 20260101 --end-date 20260206

# 单日全市场
python fetchers/stk_factor_pro.py --trade-date 20260206

# 批量拉取（按交易日逐天，含断点续拉）
python fetchers/stk_factor_pro_batch.py --start-date 20250101 --end-date 20260206

# 续拉（自动跳过已完成日期）
python fetchers/stk_factor_pro_batch.py --start-date 20250101 --end-date 20260206

# 重新拉取（忽略进度）
python fetchers/stk_factor_pro_batch.py --start-date 20250101 --end-date 20260206 --no-resume

# 自定义间隔（默认0.2s，8000积分500次/分钟）
python fetchers/stk_factor_pro_batch.py --start-date 20250101 --end-date 20260206 --delay 0.3
```

## 接口限制

- 需 5000 积分
- 单次最多 10000 条（按 trade_date 拉取，每天 ~5500 条，无需分页）
- 8000 积分：500 次/分钟（默认 0.2s 间隔）
- 5000 积分：30 次/分钟（需设 --delay 2.0）

## 数据存储

- 表：`stk_factor`（唯一键：ts_code + trade_date）
- 提取列：close/pct_chg/vol/amount/turnover_rate/pe_ttm/pb/total_mv/circ_mv + MACD/KDJ/RSI/BOLL/MA 等前复权指标
- `payload_json` 保存完整 261 列原始数据
- 进度文件：`data/stk_factor_progress.json` + `data/stk_factor_progress.log`
