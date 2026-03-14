# fetchers/broker_recommend.py
"""从 Tushare 拉取券商月度金股数据"""

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

from analyzers.broker_recommend._shared.db import upsert_recommendations

load_env_auto(PROJECT_ROOT)

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")
DATA_DIR = PROJECT_ROOT / "data"


def get_pro():
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY environment variable not set")
    ts.set_token(TUSHARE_API_KEY)
    return ts.pro_api()


def fetch_broker_recommend(month: str, save_csv: bool = True) -> int:
    """
    从 Tushare 拉取指定月份的金股数据，先保存CSV再导入DB
    
    Args:
        month: 月度 YYYYMM，如 "202602"
        save_csv: 是否先保存CSV
    
    Returns:
        新增/更新条数
    """
    pro = get_pro()
    all_dfs = []
    batch_num = 0
    
    # 循环提取（如果返回1000行说明可能还有数据）
    prev_df = None
    while True:
        try:
            df = pro.broker_recommend(month=month)
        except Exception as e:
            print(f"API 调用失败: {e}")
            break
        
        if df is None or df.empty:
            break
        
        batch_num += 1
        print(f"批次 {batch_num}: 获取 {len(df)} 条")
        
        # 检查是否与上一批重复（如果接口不支持分页）
        if prev_df is not None:
            if len(df) == len(prev_df) and df.equals(prev_df):
                print(f"  数据与上一批重复，停止拉取")
                break
        
        all_dfs.append(df)
        prev_df = df.copy()
        
        # 如果返回少于1000行，说明已获取完
        if len(df) < 1000:
            break
        
        # 如果返回1000行，可能还有数据，等待后继续
        print(f"  返回1000行，等待1秒后继续...")
        time.sleep(1)
    
    if not all_dfs:
        return 0
    
    # 合并所有批次
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # 去重（同一券商同一股票）
    combined_df = combined_df.drop_duplicates(subset=['broker', 'ts_code'], keep='first')
    
    print(f"合并后共 {len(combined_df)} 条（去重后）")
    
    # 保存CSV
    if save_csv:
        csv_path = DATA_DIR / f"broker_recommend_{month}.csv"
        combined_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"已保存CSV: {csv_path}")
    
    # 导入数据库
    rows = combined_df.to_dict("records")
    return upsert_recommendations(rows)


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="拉取券商月度金股")
    parser.add_argument("--month", help="月度 YYYYMM，默认当前月份")
    args = parser.parse_args()
    
    month = args.month or datetime.now().strftime("%Y%m")
    count = fetch_broker_recommend(month)
    print(f"已入库 {count} 条金股数据（{month}）")
