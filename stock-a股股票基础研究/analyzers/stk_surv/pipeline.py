# analyzers/stk_surv/pipeline.py
"""机构调研分析流程入口"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.stk_surv import fetch_stk_surv
from analyzers.stk_surv.search import (
    search_by_company, search_by_org, search_by_person, get_survey_detail
)


def run_fetch_recent(days: int = 30) -> int:
    """拉取最近N天的所有调研数据"""
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    return fetch_stk_surv(start_date=start_str, end_date=end_str, include_content=True)


def run_search(query: str, query_type: str = "company", days: int = None) -> list[dict]:
    """
    统一搜索入口
    
    Args:
        query: 搜索关键词
        query_type: company/org/person
        days: 可选，最近N天
    """
    if query_type == "company":
        return search_by_company(query, days)
    elif query_type == "org":
        return search_by_org(query, days)
    elif query_type == "person":
        return search_by_person(query, days)
    else:
        raise ValueError(f"不支持的查询类型: {query_type}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="机构调研分析流程")
    subparsers = parser.add_subparsers(dest="command")
    
    # 拉取
    fetch_p = subparsers.add_parser("fetch", help="拉取调研数据")
    fetch_p.add_argument("--days", type=int, default=30, help="最近N天，默认30")
    
    # 搜索
    search_p = subparsers.add_parser("search", help="搜索调研")
    search_p.add_argument("query", help="搜索关键词")
    search_p.add_argument("--type", choices=["company", "org", "person"], default="company", help="查询类型")
    search_p.add_argument("--days", type=int, help="最近N天")
    
    # 详情
    detail_p = subparsers.add_parser("detail", help="查看调研详情")
    detail_p.add_argument("--event-id", type=int, required=True, help="事件ID")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        count = run_fetch_recent(args.days)
        print(f"已入库 {count} 个调研事件")
    
    elif args.command == "search":
        results = run_search(args.query, args.type, args.days)
        for r in results:
            print(f"[{r['id']}] [{r['surv_date']}] {r['name']} ({r['ts_code']})")
        print(f"\n共 {len(results)} 条")
    
    elif args.command == "detail":
        result = get_survey_detail(args.event_id)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"未找到事件 ID {args.event_id}")
    
    else:
        parser.print_help()
