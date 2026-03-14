"""现金流量表流程入口"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.cashflow.search import get_cashflow, get_cashflow_history, get_field_value, ensure_data
from fetchers.cashflow import fetch_and_save


def run_fetch(**kwargs):
    count = fetch_and_save(**kwargs)
    print(f"保存 {count} 条记录")
    return count


def run_query(ts_code: str, field: str = None, end_date: str = None):
    ensure_data(ts_code, end_date, years=4)
    if field:
        value = get_field_value(ts_code, field, end_date)
        print("未找到数据" if value is None else f"{ts_code} {field} = {value}")
    else:
        record = get_cashflow(ts_code, end_date)
        print("未找到数据" if not record else record)


def run_history(ts_code: str, limit: int = 4):
    records = get_cashflow_history(ts_code, limit=limit)
    for r in records:
        print(r.get("end_date"), r.get("n_cashflow_act"), r.get("n_cashflow_inv"))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="现金流量表查询")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_fetch = subparsers.add_parser("fetch", help="拉取数据")
    p_fetch.add_argument("--ts-code")
    p_fetch.add_argument("--ann-date")
    p_fetch.add_argument("--f-ann-date")
    p_fetch.add_argument("--start-date")
    p_fetch.add_argument("--end-date")
    p_fetch.add_argument("--period")
    p_fetch.add_argument("--report-type")
    p_fetch.add_argument("--comp-type")
    p_fetch.add_argument("--is-calc", type=int)
    p_fetch.add_argument("--vip", action="store_true")

    p_query = subparsers.add_parser("query", help="查询数据")
    p_query.add_argument("--ts-code", required=True)
    p_query.add_argument("--field")
    p_query.add_argument("--end-date")

    p_history = subparsers.add_parser("history", help="查询历史")
    p_history.add_argument("--ts-code", required=True)
    p_history.add_argument("--limit", type=int, default=4)

    args = parser.parse_args()
    if args.command == "fetch":
        if not any([args.ts_code, args.period, args.start_date, args.end_date]):
            parser.error("请至少提供一个查询条件：--ts-code / --period / --start-date / --end-date")
        if args.vip and not args.period:
            parser.error("使用VIP接口时必须提供 --period 参数")
        run_fetch(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            f_ann_date=args.f_ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type,
            comp_type=args.comp_type,
            is_calc=args.is_calc,
            use_vip=args.vip,
        )
    elif args.command == "query":
        run_query(args.ts_code, args.field, args.end_date)
    elif args.command == "history":
        run_history(args.ts_code, args.limit)
