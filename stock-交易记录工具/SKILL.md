---
name: stock-trade-journal
description: 按统一规则记录交易流水。按个股落 Markdown，同时写入 SQLite 便于统计与量化复盘。
when: 当用户说“记一下这笔交易”“记录交易”“建交易日志”“按模板持续记录”时使用。
examples:
  - "记录：603067.SH 在44.1减仓2900股，剩余34000"
  - "把这笔交易按模板记下来"
  - "查一下振华股份最近交易流水"
metadata:
  {
    "openclaw": {
      "emoji": "📒",
      "requires": { "bins": ["python3"] }
    }
  }
---

# stock-trade-journal

## 固定存储位置
- `results/trade-journal/records/<TS_CODE>.md`
- `results/trade-journal/db/trades.db`

## 执行规则
1. 每次交易动作都记录（买/卖/加/减）。
2. 同时写 Markdown + SQLite（双写）。
3. Markdown 按个股持续追加，数据库用于后续统计计算。

## 命令模板
```bash
python3 scripts/record_trade.py \
  --workspace /Users/kirk/.openclaw/workspace-technical-analysis \
  --ts-code 603067.SH --side SELL --price 44.1 --quantity 2900 \
  --position-before 36900 --position-after 34000 \
  --reason "压力位先锁利润" --stop-loss 37.2 --take-profit "45.5分批"
```
