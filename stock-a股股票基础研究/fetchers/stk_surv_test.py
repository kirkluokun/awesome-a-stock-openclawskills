# fetchers/stk_surv_test.py
"""测试 stk_surv 接口数据结构"""

import os
import sys
from pathlib import Path

import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_env_auto(PROJECT_ROOT)

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")


def get_pro():
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY environment variable not set")
    ts.set_token(TUSHARE_API_KEY)
    return ts.pro_api()


def test_stk_surv():
    """测试拉取数据，查看结构"""
    pro = get_pro()
    
    # 测试1：按股票代码拉取
    print("=== 测试1：按股票代码拉取（002223.SZ，20211024）===")
    try:
        df1 = pro.stk_surv(
            ts_code='002223.SZ',
            trade_date='20211024',
            fields='ts_code,name,surv_date,fund_visitors,rece_place,rece_mode,rece_org,org_type,comp_rece,content'
        )
        print(f"返回 {len(df1)} 条记录")
        print("\n前5条数据：")
        print(df1.head().to_string())
        print("\n字段列表：")
        print(df1.columns.tolist())
        print("\n数据类型：")
        print(df1.dtypes)
        print("\ncontent 字段示例（前3条）：")
        if 'content' in df1.columns:
            for i, content in enumerate(df1['content'].head(3)):
                print(f"  [{i+1}] {type(content)}: {str(content)[:100] if pd.notna(content) else 'None'}")
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*60)
    
    # 测试2：按日期范围拉取（最近30天）
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n=== 测试2：按日期范围拉取（{start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')}）===")
    try:
        df2 = pro.stk_surv(
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d'),
            fields='ts_code,name,surv_date,fund_visitors,rece_place,rece_mode,rece_org,org_type,comp_rece,content'
        )
        print(f"返回 {len(df2)} 条记录")
        if len(df2) > 0:
            print("\n前3条数据：")
            print(df2.head(3).to_string())
            print("\n按公司分组统计（前10）：")
            print(df2.groupby(['ts_code', 'name', 'surv_date']).size().head(10))
    except Exception as e:
        print(f"错误: {e}")
    
    # 保存到CSV查看
    if len(df1) > 0:
        csv_path = PROJECT_ROOT / "data" / "stk_surv_sample.csv"
        df1.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n已保存样本数据到: {csv_path}")


if __name__ == "__main__":
    test_stk_surv()
