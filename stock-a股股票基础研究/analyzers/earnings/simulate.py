#!/usr/bin/env python3
"""
本地模拟流程：按日期批量 ingest -> compare -> run
"""

import argparse
from pathlib import Path

from _shared.sim_runner import (
    build_ingest_cmd,
    build_simple_cmd,
    normalize_path,
    parse_dates,
    reset_db,
    resolve_db_path,
    run_cmd,
)


def main():
    parser = argparse.ArgumentParser(description="本地模拟流程")
    parser.add_argument("--dates", required=True, help="逗号分隔日期列表 (YYYYMMDD,YYYYMMDD)")
    parser.add_argument("--report-rc-file", required=True, help="report_rc CSV")
    parser.add_argument("--report-rc-update-file", help="report_rc 更新样本 CSV")
    parser.add_argument("--update-date", help="更新样本日期 (YYYYMMDD)")
    parser.add_argument("--forecast-file", help="forecast CSV")
    parser.add_argument("--express-file", help="express CSV")
    parser.add_argument("--income-file", help="income CSV")
    parser.add_argument("--disclosure-file", help="disclosure_date CSV")
    parser.add_argument("--reset-db", action="store_true", help="重建数据库")
    parser.add_argument("--only-report-rc", action="store_true", help="只处理 report_rc")
    parser.add_argument("--no-vip", action="store_true", help="不使用 VIP 接口")
    parser.add_argument("--env-path", help="指定 .env 路径")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[2]
    ingest_path = Path(__file__).with_name("ingest.py")
    compare_path = Path(__file__).with_name("compare.py")
    run_path = Path(__file__).with_name("run.py")

    args.report_rc_file = normalize_path(args.report_rc_file)
    args.report_rc_update_file = normalize_path(args.report_rc_update_file)
    args.forecast_file = normalize_path(args.forecast_file)
    args.express_file = normalize_path(args.express_file)
    args.income_file = normalize_path(args.income_file)
    args.disclosure_file = normalize_path(args.disclosure_file)
    args.env_path = normalize_path(args.env_path)

    date_list = parse_dates(args.dates)
    if not date_list:
        raise SystemExit("未提供有效 dates")

    if args.reset_db:
        reset_db(resolve_db_path(root_dir))

    run_cmd(build_simple_cmd(Path(__file__).with_name("db.py")) + ["--init"])

    for date_str in date_list:
        cmd = build_ingest_cmd(ingest_path, date_str, args)
        run_cmd(cmd)

    if args.report_rc_update_file:
        update_date = args.update_date or date_list[-1]
        args.report_rc_file = args.report_rc_update_file
        cmd = build_ingest_cmd(ingest_path, update_date, args)
        run_cmd(cmd)

    run_cmd(build_simple_cmd(compare_path))
    run_cmd(build_simple_cmd(run_path))


if __name__ == "__main__":
    main()
