#!/usr/bin/env python3
import argparse, os, sqlite3
from datetime import datetime


def ensure_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts_code TEXT NOT NULL,
          side TEXT NOT NULL,
          price REAL NOT NULL,
          quantity INTEGER NOT NULL,
          position_before INTEGER,
          position_after INTEGER,
          reason TEXT,
          stop_loss REAL,
          take_profit TEXT,
          note TEXT,
          timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def append_md(md_path: str, row: dict):
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    if not os.path.exists(md_path):
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {row['ts_code']} 交易记录\n\n")
    with open(md_path, "a", encoding="utf-8") as f:
        f.write(
            f"## {row['timestamp']} | {row['side']} | {row['ts_code']}\n"
            f"- 价格：{row['price']}\n"
            f"- 数量：{row['quantity']}\n"
            f"- 交易后持仓：{row.get('position_after','')}\n"
            f"- 仓位变化：{row.get('position_before','')} -> {row.get('position_after','')}\n"
            f"- 触发原因：{row.get('reason','')}\n"
            f"- 止损：{row.get('stop_loss','')}\n"
            f"- 止盈：{row.get('take_profit','')}\n"
            f"- 备注：{row.get('note','')}\n\n"
        )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workspace", required=True)
    p.add_argument("--ts-code", required=True)
    p.add_argument("--side", required=True)
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--quantity", type=int, required=True)
    p.add_argument("--position-before", type=int)
    p.add_argument("--position-after", type=int)
    p.add_argument("--reason", default="")
    p.add_argument("--stop-loss", type=float)
    p.add_argument("--take-profit", default="")
    p.add_argument("--note", default="")
    p.add_argument("--timestamp", default=datetime.now().astimezone().isoformat(timespec="seconds"))
    args = p.parse_args()

    base = os.path.join(args.workspace, "results", "trade-journal")
    db_path = os.path.join(base, "db", "trades.db")
    md_path = os.path.join(base, "records", f"{args.ts_code}.md")

    row = {
        "ts_code": args.ts_code,
        "side": args.side.upper(),
        "price": args.price,
        "quantity": args.quantity,
        "position_before": args.position_before,
        "position_after": args.position_after,
        "reason": args.reason,
        "stop_loss": args.stop_loss,
        "take_profit": args.take_profit,
        "note": args.note,
        "timestamp": args.timestamp,
    }

    conn = ensure_db(db_path)
    conn.execute(
        """
        INSERT INTO trades(ts_code, side, price, quantity, position_before, position_after, reason, stop_loss, take_profit, note, timestamp)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            row["ts_code"], row["side"], row["price"], row["quantity"], row["position_before"], row["position_after"],
            row["reason"], row["stop_loss"], row["take_profit"], row["note"], row["timestamp"]
        ),
    )
    conn.commit(); conn.close()
    append_md(md_path, row)
    print(f"Recorded trade: {row['ts_code']} {row['side']} {row['quantity']} @ {row['price']}")


if __name__ == "__main__":
    main()
