# stock-trade-journal

交易记录技能包（最小可用版）：
- 按个股写入 Markdown
- 同步写入 SQLite（trades.db）

## 目录
- `scripts/record_trade.py`：记录单笔交易（自动建表/建文件）
- `scripts/query_trades.py`：查询交易记录
- `templates/trade-entry.md`：Markdown 模板

## 示例
```bash
python3 scripts/record_trade.py \
  --workspace /Users/kirk/.openclaw/workspace-technical-analysis \
  --ts-code 603067.SH --side SELL --price 44.1 --quantity 2900 \
  --position-before 36900 --position-after 34000 \
  --reason "压力位先锁利润"

python3 scripts/query_trades.py \
  --workspace /Users/kirk/.openclaw/workspace-technical-analysis \
  --ts-code 603067.SH --limit 20
```
