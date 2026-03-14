#!/usr/bin/env python3
"""
获取股票基础信息数据
数据来源: Tushare

支持接口:
    1. stock_basic - 股票列表
    2. stk_premarket - 股本情况（盘前）
    3. bak_basic - 股票历史列表
    4. trade_cal - 交易日历

用法:
    python fetch_stock_basic.py stock_basic [options]
    python fetch_stock_basic.py stk_premarket --trade_date 20260202
    python fetch_stock_basic.py bak_basic --trade_date 20260202
    python fetch_stock_basic.py trade_cal --start_date 20260101 --end_date 20260131
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

# 加载 .env
load_env_auto(Path(__file__).resolve())

# 初始化 Tushare
api_key = os.getenv("TUSHARE_API_KEY")
if not api_key:
    print("错误: 未找到 TUSHARE_API_KEY")
    sys.exit(1)

pro = ts.pro_api(api_key)


def fetch_stock_basic(
    ts_code: str = None,
    name: str = None,
    market: str = None,
    list_status: str = None,
    exchange: str = None,
    is_hs: str = None
) -> pd.DataFrame:
    """
    获取股票列表
    
    参数:
        ts_code: TS股票代码
        name: 名称
        market: 市场类别 (主板/创业板/科创板/CDR/北交所)
        list_status: 上市状态 L上市 D退市 P暂停上市 G过会未交易，默认L
        exchange: 交易所 SSE上交所 SZSE深交所 BSE北交所
        is_hs: 是否沪深港通标的 N否 H沪股通 S深股通
    """
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if name:
        params["name"] = name
    if market:
        params["market"] = market
    if list_status:
        params["list_status"] = list_status
    if exchange:
        params["exchange"] = exchange
    if is_hs:
        params["is_hs"] = is_hs
    
    df = pro.stock_basic(**params)
    return df


def fetch_stk_premarket(
    ts_code: str = None,
    trade_date: str = None,
    start_date: str = None,
    end_date: str = None
) -> pd.DataFrame:
    """
    获取股本情况（盘前）
    
    参数:
        ts_code: 股票代码
        trade_date: 交易日期 (YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if trade_date:
        params["trade_date"] = trade_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    df = pro.stk_premarket(**params)
    return df


def fetch_bak_basic(
    trade_date: str = None,
    ts_code: str = None
) -> pd.DataFrame:
    """
    获取股票历史列表（历史每天股票列表）
    数据从2016年开始
    
    参数:
        trade_date: 交易日期 (YYYYMMDD)
        ts_code: 股票代码
    """
    params = {}
    if trade_date:
        params["trade_date"] = trade_date
    if ts_code:
        params["ts_code"] = ts_code
    
    df = pro.bak_basic(**params)
    return df


def fetch_trade_cal(
    exchange: str = None,
    start_date: str = None,
    end_date: str = None,
    is_open: str = None
) -> pd.DataFrame:
    """
    获取交易日历
    
    参数:
        exchange: 交易所 SSE/SZSE/CFFEX/SHFE/CZCE/DCE/INE
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        is_open: 是否交易 0休市 1交易
    """
    params = {}
    if exchange:
        params["exchange"] = exchange
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if is_open is not None:
        params["is_open"] = is_open
    
    df = pro.trade_cal(**params)
    return df


def save_to_csv(df: pd.DataFrame, api_name: str, suffix: str = None):
    """保存数据到 CSV"""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    if suffix:
        filename = f"{api_name}_{suffix}.csv"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{api_name}_{timestamp}.csv"
    
    filepath = output_dir / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"已保存: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="获取股票基础信息数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 获取所有上市股票列表
    python fetch_stock_basic.py stock_basic
    
    # 获取创业板股票
    python fetch_stock_basic.py stock_basic --market 创业板
    
    # 获取某日盘前股本情况
    python fetch_stock_basic.py stk_premarket --trade_date 20260202
    
    # 获取某日历史股票列表
    python fetch_stock_basic.py bak_basic --trade_date 20260202
    
    # 获取交易日历
    python fetch_stock_basic.py trade_cal --start_date 20260101 --end_date 20260131
        """
    )
    
    subparsers = parser.add_subparsers(dest="api", help="API接口")
    
    # stock_basic 子命令
    p_basic = subparsers.add_parser("stock_basic", help="股票列表")
    p_basic.add_argument("--ts_code", help="TS股票代码")
    p_basic.add_argument("--name", help="股票名称")
    p_basic.add_argument("--market", help="市场类别: 主板/创业板/科创板/CDR/北交所")
    p_basic.add_argument("--list_status", help="上市状态: L上市 D退市 P暂停上市 G过会未交易")
    p_basic.add_argument("--exchange", help="交易所: SSE上交所 SZSE深交所 BSE北交所")
    p_basic.add_argument("--is_hs", help="沪深港通标的: N否 H沪股通 S深股通")
    
    # stk_premarket 子命令
    p_premarket = subparsers.add_parser("stk_premarket", help="股本情况（盘前）")
    p_premarket.add_argument("--ts_code", help="股票代码")
    p_premarket.add_argument("--trade_date", help="交易日期 (YYYYMMDD)")
    p_premarket.add_argument("--start_date", help="开始日期 (YYYYMMDD)")
    p_premarket.add_argument("--end_date", help="结束日期 (YYYYMMDD)")
    
    # bak_basic 子命令
    p_bak = subparsers.add_parser("bak_basic", help="股票历史列表")
    p_bak.add_argument("--trade_date", help="交易日期 (YYYYMMDD)")
    p_bak.add_argument("--ts_code", help="股票代码")
    
    # trade_cal 子命令
    p_cal = subparsers.add_parser("trade_cal", help="交易日历")
    p_cal.add_argument("--exchange", help="交易所: SSE/SZSE/CFFEX/SHFE/CZCE/DCE/INE")
    p_cal.add_argument("--start_date", help="开始日期 (YYYYMMDD)")
    p_cal.add_argument("--end_date", help="结束日期 (YYYYMMDD)")
    p_cal.add_argument("--is_open", help="是否交易: 0休市 1交易")
    
    args = parser.parse_args()
    
    if not args.api:
        parser.print_help()
        sys.exit(1)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 调用 {args.api}")
    
    # 根据子命令调用对应函数
    if args.api == "stock_basic":
        df = fetch_stock_basic(
            ts_code=args.ts_code,
            name=args.name,
            market=args.market,
            list_status=args.list_status,
            exchange=args.exchange,
            is_hs=args.is_hs
        )
        suffix = args.market or args.list_status or "all"
        
    elif args.api == "stk_premarket":
        df = fetch_stk_premarket(
            ts_code=args.ts_code,
            trade_date=args.trade_date,
            start_date=args.start_date,
            end_date=args.end_date
        )
        suffix = args.trade_date or f"{args.start_date}_{args.end_date}"
        
    elif args.api == "bak_basic":
        df = fetch_bak_basic(
            trade_date=args.trade_date,
            ts_code=args.ts_code
        )
        suffix = args.trade_date or args.ts_code
        
    elif args.api == "trade_cal":
        df = fetch_trade_cal(
            exchange=args.exchange,
            start_date=args.start_date,
            end_date=args.end_date,
            is_open=args.is_open
        )
        suffix = f"{args.start_date}_{args.end_date}"
    
    if df is not None and not df.empty:
        print(f"获取到 {len(df)} 条数据")
        print(f"字段: {list(df.columns)}")
        print(f"\n预览:")
        print(df.head(5))
        save_to_csv(df, args.api, suffix)
    else:
        print("未获取到数据")


if __name__ == "__main__":
    main()
