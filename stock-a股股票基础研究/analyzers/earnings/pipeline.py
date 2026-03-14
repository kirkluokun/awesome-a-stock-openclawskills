#!/usr/bin/env python3
"""
主流程入口：拉取 -> 对比 -> JSON 输出
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from db import connect, run_migrations


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_table(conn, table: str):
    cur = conn.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def change_direction(change_log: str):
    if not change_log:
        return None
    try:
        data = json.loads(change_log)
    except json.JSONDecodeError:
        return None
    np_change = data.get("np")
    if not np_change:
        return None
    old = np_change.get("old")
    new = np_change.get("new")
    if old is None or new is None:
        return None
    if new > old:
        return "up"
    if new < old:
        return "down"
    return "same"


def load_report_rc_changes(conn, since_ts: str):
    sql = (
        "SELECT ts_code, report_date, period, org_name, np, change_type, change_log, updated_at "
        "FROM report_rc WHERE change_type = 'update' AND updated_at >= ?"
    )
    rows = conn.execute(sql, (since_ts,)).fetchall()
    result = []
    for row in rows:
        row_dict = dict(row)
        row_dict["direction"] = change_direction(row_dict.get("change_log"))
        result.append(row_dict)
    return result


def write_json(output_dir: Path, payload: dict):
    output_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"summary_{ts}.json"
    filepath.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return filepath


def cleanup_old_files(output_dir: Path, pattern: str, keep: int = 5):
    """清理旧文件，只保留最近 N 个"""
    files = sorted(output_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    for old_file in files[keep:]:
        old_file.unlink()
        print(f"已清理: {old_file.name}")


def main():
    parser = argparse.ArgumentParser(description="主流程入口")
    parser.add_argument("--summary-only", action="store_true", help="仅输出汇总 JSON")
    args = parser.parse_args()

    conn = connect()
    run_migrations(conn)

    alerts = load_table(conn, "alerts")
    since_ts = datetime.now().strftime("%Y-%m-%d 00:00:00")
    expectation_changes = load_report_rc_changes(conn, since_ts)

    payload = {
        "run_meta": {
            "run_at": now_ts(),
            "alerts_count": len(alerts),
        },
        "summary": {
            "alerts": len(alerts),
        },
        "alerts": alerts,
        "changes": expectation_changes,
    }

    output_dir = Path(__file__).resolve().parents[2] / "output"
    filepath = write_json(output_dir, payload)
    conn.close()

    # 清理旧文件，只保留最近 5 个
    cleanup_old_files(output_dir, "summary_*.json", keep=5)

    print(f"已输出: {filepath}")


if __name__ == "__main__":
    main()
