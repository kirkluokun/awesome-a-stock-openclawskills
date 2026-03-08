#!/usr/bin/env python3
import argparse, os, sqlite3

p = argparse.ArgumentParser()
p.add_argument("--workspace", required=True)
p.add_argument("--ts-code", required=True)
p.add_argument("--limit", type=int, default=20)
args = p.parse_args()

db = os.path.join(args.workspace, "results", "trade-journal", "db", "trades.db")
conn = sqlite3.connect(db)
rows = conn.execute(
    "SELECT timestamp, ts_code, side, price, quantity, position_after, reason FROM trades WHERE ts_code=? ORDER BY id DESC LIMIT ?",
    (args.ts_code, args.limit)
).fetchall()
conn.close()

for r in rows:
    print(" | ".join(map(str, r)))
