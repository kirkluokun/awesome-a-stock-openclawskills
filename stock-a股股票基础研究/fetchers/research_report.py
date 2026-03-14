# fetchers/research_report.py
"""从 Tushare 拉取券商研报元数据"""

import os
import sys
from pathlib import Path

import tushare as ts
from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.research._shared.db import upsert_reports

load_env_auto(PROJECT_ROOT)

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")


def get_pro():
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY environment variable not set")
    ts.set_token(TUSHARE_API_KEY)
    return ts.pro_api()


def fetch_research_report(
    trade_date: str = None,
    start_date: str = None,
    end_date: str = None,
    ts_code: str = None,
    ind_name: str = None,
    inst_csname: str = None,
    report_type: str = None,
) -> int:
    """
    从 Tushare 拉取研报元数据，存入 DB
    
    Args:
        trade_date: 单日 YYYYMMDD
        start_date/end_date: 日期范围
        ts_code: 股票代码
        ind_name: 行业名称
        inst_csname: 券商名称
        report_type: 个股研报/行业研报
    
    Returns:
        新增/更新条数
    """
    pro = get_pro()
    
    params = {}
    if trade_date:
        params["trade_date"] = trade_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if ts_code:
        params["ts_code"] = ts_code
    if ind_name:
        params["ind_name"] = ind_name
    if inst_csname:
        params["inst_csname"] = inst_csname
    if report_type:
        params["report_type"] = report_type
    
    try:
        df = pro.research_report(
            **params,
            fields="trade_date,ts_code,name,title,abstr,report_type,author,inst_csname,ind_name,url"
        )
    except Exception as e:
        print(f"API 调用失败: {e}")
        return 0
    
    if df.empty:
        return 0
    
    rows = df.to_dict("records")
    return upsert_reports(rows)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="拉取券商研报")
    parser.add_argument("--date", help="单日 YYYYMMDD")
    parser.add_argument("--start", help="开始日期")
    parser.add_argument("--end", help="结束日期")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--ind", help="行业名称")
    parser.add_argument("--inst", help="券商名称")
    args = parser.parse_args()
    
    count = fetch_research_report(
        trade_date=args.date,
        start_date=args.start,
        end_date=args.end,
        ts_code=args.ts_code,
        ind_name=args.ind,
        inst_csname=args.inst,
    )
    print(f"已入库 {count} 条研报")
