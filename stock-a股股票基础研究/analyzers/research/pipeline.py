# analyzers/research/pipeline.py
"""研报分析流程入口"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.research_report import fetch_research_report
from analyzers.research.search import search_reports
from analyzers.research.download import download_report, download_batch
from interpreters.research.extract import extract_report, extract_batch


def run_search(
    ts_code: str = None,
    ind_name: str = None,
    keyword: str = None,
    inst_csname: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    fetch_if_empty: bool = True,
) -> list[dict]:
    """
    搜索研报
    
    Args:
        fetch_if_empty: 若 DB 无数据，自动从 API 拉取
    """
    results = search_reports(
        ts_code=ts_code,
        ind_name=ind_name,
        keyword=keyword,
        inst_csname=inst_csname,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    
    if not results and fetch_if_empty:
        print("DB 无数据，从 API 拉取...")
        fetch_research_report(
            ts_code=ts_code,
            ind_name=ind_name,
            inst_csname=inst_csname,
            start_date=start_date,
            end_date=end_date,
        )
        results = search_reports(
            ts_code=ts_code,
            ind_name=ind_name,
            keyword=keyword,
            inst_csname=inst_csname,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    
    return results


def run_extract(report_id: int, force: bool = False) -> dict | None:
    """下载并解析单个研报"""
    return extract_report(report_id, force=force)


def run_batch_extract(report_ids: list[int]) -> list[dict]:
    """批量解析"""
    return extract_batch(report_ids)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="研报分析流程")
    subparsers = parser.add_subparsers(dest="command")
    
    # 搜索
    search_p = subparsers.add_parser("search", help="搜索研报")
    search_p.add_argument("--ts-code", help="股票代码")
    search_p.add_argument("--ind", help="行业名称")
    search_p.add_argument("--keyword", help="标题关键词")
    search_p.add_argument("--inst", help="券商名称")
    search_p.add_argument("--start", help="开始日期")
    search_p.add_argument("--end", help="结束日期")
    search_p.add_argument("--limit", type=int, default=20)
    
    # 解析
    extract_p = subparsers.add_parser("extract", help="解析研报")
    extract_p.add_argument("ids", nargs="+", type=int, help="研报 ID")
    extract_p.add_argument("--force", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "search":
        results = run_search(
            ts_code=args.ts_code,
            ind_name=args.ind,
            keyword=args.keyword,
            inst_csname=args.inst,
            start_date=args.start,
            end_date=args.end,
            limit=args.limit,
        )
        for r in results:
            print(f"[{r['id']}] [{r['trade_date']}] {r['title'][:60]}")
        print(f"\n共 {len(results)} 条")
    
    elif args.command == "extract":
        for rid in args.ids:
            result = run_extract(rid, force=args.force)
            if result:
                print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
