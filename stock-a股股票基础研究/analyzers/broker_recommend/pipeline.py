# analyzers/broker_recommend/pipeline.py
"""券商金股分析流程入口"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.broker_recommend import fetch_broker_recommend
from analyzers.broker_recommend.stats import get_monthly_stats


def run_fetch(month: str = None) -> int:
    """
    拉取数据
    
    Args:
        month: 月度 YYYYMM，None 时使用当前月份
    
    Returns:
        新增条数
    """
    if not month:
        month = datetime.now().strftime("%Y%m")
    return fetch_broker_recommend(month)


def run_stats(month: str = None) -> dict:
    """
    运行统计
    
    Args:
        month: 月度 YYYYMM，None 时使用当前月份
    
    Returns:
        统计结果
    """
    if not month:
        month = datetime.now().strftime("%Y%m")
    return get_monthly_stats(month)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="券商金股分析流程")
    subparsers = parser.add_subparsers(dest="command")
    
    # 拉取
    fetch_p = subparsers.add_parser("fetch", help="拉取金股数据")
    fetch_p.add_argument("--month", help="月度 YYYYMM，默认当前月份")
    
    # 统计
    stats_p = subparsers.add_parser("stats", help="查看统计")
    stats_p.add_argument("--month", help="月度 YYYYMM，默认当前月份")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        count = run_fetch(args.month)
        print(f"已入库 {count} 条")
    
    elif args.command == "stats":
        result = run_stats(args.month)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
