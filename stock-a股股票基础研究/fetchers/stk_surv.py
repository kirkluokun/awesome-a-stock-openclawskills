# fetchers/stk_surv.py
"""从 Tushare 拉取机构调研数据"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.stk_surv._shared.db import upsert_event, upsert_participants

load_env_auto(PROJECT_ROOT)

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")


def get_pro():
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY environment variable not set")
    ts.set_token(TUSHARE_API_KEY)
    return ts.pro_api()


def fetch_stk_surv(
    ts_code: str = None,
    trade_date: str = None,
    start_date: str = None,
    end_date: str = None,
    include_content: bool = True,
) -> int:
    """
    拉取调研数据，存入两张表
    
    Args:
        ts_code: 股票代码
        trade_date: 单日 YYYYMMDD
        start_date/end_date: 日期范围
        include_content: 是否拉取content字段
    
    Returns:
        新增事件数
    """
    pro = get_pro()
    
    fields = "ts_code,name,surv_date,fund_visitors,rece_place,rece_mode,rece_org,org_type,comp_rece"
    if include_content:
        fields += ",content"
    
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if trade_date:
        params["trade_date"] = trade_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    all_dfs = []
    offset = 0
    limit = 100
    
    # 循环拉取（单次最大100条）
    while True:
        try:
            df = pro.stk_surv(**params, offset=offset, limit=limit, fields=fields)
        except Exception as e:
            print(f"API 调用失败: {e}")
            break
        
        if df is None or df.empty:
            break
        
        all_dfs.append(df)
        print(f"  获取 {len(df)} 条（offset={offset}）")
        
        if len(df) < limit:
            break
        
        offset += limit
        time.sleep(0.5)  # 避免限流
    
    if not all_dfs:
        return 0
    
    # 合并数据
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"合并后共 {len(combined_df)} 条记录")
    
    # 按(ts_code, surv_date)分组处理
    event_count = 0
    for (ts_code_val, surv_date_val), group in combined_df.groupby(['ts_code', 'surv_date']):
        # 提取事件信息（取第一条，因为同一事件的公共字段相同）
        first_row = group.iloc[0].to_dict()
        event_row = {
            "ts_code": ts_code_val,
            "name": first_row.get("name"),
            "surv_date": surv_date_val,
            "rece_place": first_row.get("rece_place"),
            "rece_mode": first_row.get("rece_mode"),
            "comp_rece": first_row.get("comp_rece"),
            "content": first_row.get("content") if include_content else None
        }
        
        # 插入或更新事件
        event_id = upsert_event(event_row)
        
        # 提取参与人员
        participants = []
        for _, row in group.iterrows():
            participants.append({
                "fund_visitors": row.get("fund_visitors"),
                "rece_org": row.get("rece_org"),
                "org_type": row.get("org_type")
            })
        
        # 插入参与人员
        upsert_participants(event_id, participants)
        event_count += 1
    
    return event_count


if __name__ == "__main__":
    import argparse
    from datetime import datetime, timedelta
    
    parser = argparse.ArgumentParser(description="拉取机构调研数据")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--date", help="单日 YYYYMMDD")
    parser.add_argument("--start", help="开始日期")
    parser.add_argument("--end", help="结束日期")
    parser.add_argument("--days", type=int, help="最近N天")
    parser.add_argument("--no-content", action="store_true", help="不拉取content")
    args = parser.parse_args()
    
    if args.days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        count = fetch_stk_surv(start_date=start_str, end_date=end_str, include_content=not args.no_content)
    else:
        count = fetch_stk_surv(
            ts_code=args.ts_code,
            trade_date=args.date,
            start_date=args.start,
            end_date=args.end,
            include_content=not args.no_content
        )
    
    print(f"已入库 {count} 个调研事件")
