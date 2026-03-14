# analyzers/balancesheet/pipeline.py
"""资产负债表分析流程入口"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.balancesheet.search import (
    get_balancesheet,
    get_balancesheet_history,
    get_field_value,
    search_by_field,
    ensure_data
)
from fetchers.balancesheet import fetch_and_save


def run_fetch(**kwargs):
    """拉取数据"""
    count = fetch_and_save(**kwargs)
    print(f"保存 {count} 条记录")
    return count


def run_query(ts_code: str, field: str = None, end_date: str = None):
    """查询数据"""
    if field:
        value = get_field_value(ts_code, field, end_date)
        if value is not None:
            print(f"{ts_code} {field} = {value:,.0f}")
        else:
            print(f"未找到数据")
    else:
        record = get_balancesheet(ts_code, end_date)
        if record:
            print(f"报告期: {record.get('end_date')}")
            total_assets = record.get('total_assets') or 0
            inventories = record.get('inventories') or 0
            accounts_receiv = record.get('accounts_receiv') or 0
            print(f"总资产: {total_assets:,.0f}")
            print(f"存货: {inventories:,.0f}")
            print(f"应收账款: {accounts_receiv:,.0f}")
        else:
            print("未找到数据")


def run_history(ts_code: str, limit: int = 4):
    """查询历史数据"""
    records = get_balancesheet_history(ts_code, limit=limit)
    print(f"\n{ts_code} 最近{len(records)}期数据:")
    print("-" * 60)
    for r in records:
        total_assets = r.get('total_assets') or 0
        inventories = r.get('inventories') or 0
        print(f"{r['end_date']}: 总资产={total_assets:,.0f}, "
              f"存货={inventories:,.0f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="资产负债表分析")
    subparsers = parser.add_subparsers(dest="command")
    
    # fetch命令
    p_fetch = subparsers.add_parser("fetch", help="拉取数据")
    p_fetch.add_argument("--ts-code")
    p_fetch.add_argument("--start-date")
    p_fetch.add_argument("--end-date")
    p_fetch.add_argument("--period", help="报告期 YYYYMMDD（VIP接口必需）")
    p_fetch.add_argument("--report-type", default="1")
    p_fetch.add_argument("--comp-type", help="公司类型")
    p_fetch.add_argument("--vip", action="store_true", help="使用VIP接口（全量拉取，需提供period）")
    
    # query命令
    p_query = subparsers.add_parser("query", help="查询数据")
    p_query.add_argument("--ts-code", required=True)
    p_query.add_argument("--field")
    p_query.add_argument("--end-date")
    
    # history命令
    p_history = subparsers.add_parser("history", help="查询历史")
    p_history.add_argument("--ts-code", required=True)
    p_history.add_argument("--limit", type=int, default=4)
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        if args.vip and not args.period:
            parser.error("使用VIP接口时必须提供 --period 参数")
        run_fetch(
            ts_code=args.ts_code,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type,
            comp_type=args.comp_type,
            use_vip=args.vip
        )
    elif args.command == "query":
        run_query(args.ts_code, args.field, args.end_date)
    elif args.command == "history":
        run_history(args.ts_code, args.limit)
