#!/usr/bin/env python3
"""
获取财务基础数据
数据来源: Tushare

支持接口:
    1. forecast / forecast_vip - 业绩预告
    2. express / express_vip - 业绩快报
    3. disclosure_date - 预披露时间
    4. fina_indicator / fina_indicator_vip - 财务指标数据
    5. income / income_vip - 利润表
    6. balancesheet / balancesheet_vip - 资产负债表
    7. cashflow / cashflow_vip - 现金流量表
    8. fina_mainbz / fina_mainbz_vip - 主营业务构成
    9. stk_factor_pro - 股票技术面因子(专业版)
    10. stk_nineturn - 神奇九转指标
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


def fetch_forecast(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    type_: str = None
) -> pd.DataFrame:
    """业绩预告"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    if type_:
        params["type"] = type_
    return pro.forecast(**params)


def fetch_forecast_vip(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    type_: str = None
) -> pd.DataFrame:
    """业绩预告（VIP）"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    if type_:
        params["type"] = type_
    return pro.forecast_vip(**params)


def fetch_express(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None
) -> pd.DataFrame:
    """业绩快报"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    return pro.express(**params)


def fetch_express_vip(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None
) -> pd.DataFrame:
    """业绩快报（VIP）"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    return pro.express_vip(**params)


def fetch_disclosure_date(
    ts_code: str = None,
    end_date: str = None,
    pre_date: str = None,
    ann_date: str = None,
    actual_date: str = None
) -> pd.DataFrame:
    """预披露时间"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if end_date:
        params["end_date"] = end_date
    if pre_date:
        params["pre_date"] = pre_date
    if ann_date:
        params["ann_date"] = ann_date
    if actual_date:
        params["actual_date"] = actual_date
    return pro.disclosure_date(**params)


def fetch_fina_indicator(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None
) -> pd.DataFrame:
    """财务指标数据"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    return pro.fina_indicator(**params)


def fetch_fina_indicator_vip(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None
) -> pd.DataFrame:
    """财务指标数据（VIP）"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    return pro.fina_indicator_vip(**params)


def fetch_income(
    ts_code: str = None,
    ann_date: str = None,
    f_ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    report_type: str = None,
    comp_type: str = None
) -> pd.DataFrame:
    """利润表"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if f_ann_date:
        params["f_ann_date"] = f_ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    if report_type:
        params["report_type"] = report_type
    if comp_type:
        params["comp_type"] = comp_type
    return pro.income(**params)


def fetch_income_vip(
    ts_code: str = None,
    ann_date: str = None,
    f_ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    report_type: str = None,
    comp_type: str = None
) -> pd.DataFrame:
    """利润表（VIP）"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if f_ann_date:
        params["f_ann_date"] = f_ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    if report_type:
        params["report_type"] = report_type
    if comp_type:
        params["comp_type"] = comp_type
    return pro.income_vip(**params)


def fetch_balancesheet(
    ts_code: str = None,
    ann_date: str = None,
    f_ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    report_type: str = None,
    comp_type: str = None
) -> pd.DataFrame:
    """资产负债表"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if f_ann_date:
        params["f_ann_date"] = f_ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    if report_type:
        params["report_type"] = report_type
    if comp_type:
        params["comp_type"] = comp_type
    return pro.balancesheet(**params)


def fetch_balancesheet_vip(
    ts_code: str = None,
    ann_date: str = None,
    f_ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    report_type: str = None,
    comp_type: str = None
) -> pd.DataFrame:
    """资产负债表（VIP）"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if f_ann_date:
        params["f_ann_date"] = f_ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    if report_type:
        params["report_type"] = report_type
    if comp_type:
        params["comp_type"] = comp_type
    return pro.balancesheet_vip(**params)


def fetch_cashflow(
    ts_code: str = None,
    ann_date: str = None,
    f_ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    report_type: str = None,
    comp_type: str = None,
    is_calc: int = None
) -> pd.DataFrame:
    """现金流量表"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if f_ann_date:
        params["f_ann_date"] = f_ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    if report_type:
        params["report_type"] = report_type
    if comp_type:
        params["comp_type"] = comp_type
    if is_calc is not None:
        params["is_calc"] = is_calc
    return pro.cashflow(**params)


def fetch_cashflow_vip(
    ts_code: str = None,
    ann_date: str = None,
    f_ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    report_type: str = None,
    comp_type: str = None,
    is_calc: int = None
) -> pd.DataFrame:
    """现金流量表（VIP）"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if ann_date:
        params["ann_date"] = ann_date
    if f_ann_date:
        params["f_ann_date"] = f_ann_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if period:
        params["period"] = period
    if report_type:
        params["report_type"] = report_type
    if comp_type:
        params["comp_type"] = comp_type
    if is_calc is not None:
        params["is_calc"] = is_calc
    return pro.cashflow_vip(**params)


def fetch_fina_mainbz(
    ts_code: str = None,
    period: str = None,
    type_: str = None,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """主营业务构成（单只股票历史，需2000积分）"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if period:
        params["period"] = period
    if type_:
        params["type"] = type_
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return pro.fina_mainbz(**params)


def fetch_fina_mainbz_vip(
    ts_code: str = None,
    period: str = None,
    type_: str = None,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """主营业务构成（VIP全量，需5000积分）"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if period:
        params["period"] = period
    if type_:
        params["type"] = type_
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return pro.fina_mainbz_vip(**params)


def fetch_stk_factor_pro(
    ts_code: str = None,
    trade_date: str = None,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """股票技术面因子(专业版，需5000积分)"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if trade_date:
        params["trade_date"] = trade_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return pro.stk_factor_pro(**params)


def fetch_stk_nineturn(
    ts_code: str = None,
    trade_date: str = None,
    freq: str = None,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """神奇九转指标(需6000积分)"""
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if trade_date:
        params["trade_date"] = trade_date
    if freq:
        params["freq"] = freq
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return pro.stk_nineturn(**params)


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
    parser = argparse.ArgumentParser(description="获取财务基础数据")
    subparsers = parser.add_subparsers(dest="api", help="API接口")

    # forecast
    p_forecast = subparsers.add_parser("forecast", help="业绩预告")
    p_forecast.add_argument("--ts_code")
    p_forecast.add_argument("--ann_date")
    p_forecast.add_argument("--start_date")
    p_forecast.add_argument("--end_date")
    p_forecast.add_argument("--period")
    p_forecast.add_argument("--type", dest="type_")

    # forecast_vip
    p_forecast_vip = subparsers.add_parser("forecast_vip", help="业绩预告（VIP）")
    p_forecast_vip.add_argument("--ts_code")
    p_forecast_vip.add_argument("--ann_date")
    p_forecast_vip.add_argument("--start_date")
    p_forecast_vip.add_argument("--end_date")
    p_forecast_vip.add_argument("--period")
    p_forecast_vip.add_argument("--type", dest="type_")

    # express
    p_express = subparsers.add_parser("express", help="业绩快报")
    p_express.add_argument("--ts_code")
    p_express.add_argument("--ann_date")
    p_express.add_argument("--start_date")
    p_express.add_argument("--end_date")
    p_express.add_argument("--period")

    # express_vip
    p_express_vip = subparsers.add_parser("express_vip", help="业绩快报（VIP）")
    p_express_vip.add_argument("--ts_code")
    p_express_vip.add_argument("--ann_date")
    p_express_vip.add_argument("--start_date")
    p_express_vip.add_argument("--end_date")
    p_express_vip.add_argument("--period")

    # disclosure_date
    p_disclosure = subparsers.add_parser("disclosure_date", help="预披露时间")
    p_disclosure.add_argument("--ts_code")
    p_disclosure.add_argument("--end_date")
    p_disclosure.add_argument("--pre_date")
    p_disclosure.add_argument("--ann_date")
    p_disclosure.add_argument("--actual_date")

    # fina_indicator
    p_fina = subparsers.add_parser("fina_indicator", help="财务指标数据")
    p_fina.add_argument("--ts_code")
    p_fina.add_argument("--ann_date")
    p_fina.add_argument("--start_date")
    p_fina.add_argument("--end_date")
    p_fina.add_argument("--period")

    # fina_indicator_vip
    p_fina_vip = subparsers.add_parser("fina_indicator_vip", help="财务指标数据（VIP）")
    p_fina_vip.add_argument("--ts_code")
    p_fina_vip.add_argument("--ann_date")
    p_fina_vip.add_argument("--start_date")
    p_fina_vip.add_argument("--end_date")
    p_fina_vip.add_argument("--period")

    # income
    p_income = subparsers.add_parser("income", help="利润表")
    p_income.add_argument("--ts_code")
    p_income.add_argument("--ann_date")
    p_income.add_argument("--f_ann_date")
    p_income.add_argument("--start_date")
    p_income.add_argument("--end_date")
    p_income.add_argument("--period")
    p_income.add_argument("--report_type")
    p_income.add_argument("--comp_type")

    # income_vip
    p_income_vip = subparsers.add_parser("income_vip", help="利润表（VIP）")
    p_income_vip.add_argument("--ts_code")
    p_income_vip.add_argument("--ann_date")
    p_income_vip.add_argument("--f_ann_date")
    p_income_vip.add_argument("--start_date")
    p_income_vip.add_argument("--end_date")
    p_income_vip.add_argument("--period")
    p_income_vip.add_argument("--report_type")
    p_income_vip.add_argument("--comp_type")

    # balancesheet
    p_bal = subparsers.add_parser("balancesheet", help="资产负债表")
    p_bal.add_argument("--ts_code")
    p_bal.add_argument("--ann_date")
    p_bal.add_argument("--f_ann_date")
    p_bal.add_argument("--start_date")
    p_bal.add_argument("--end_date")
    p_bal.add_argument("--period")
    p_bal.add_argument("--report_type")
    p_bal.add_argument("--comp_type")

    # balancesheet_vip
    p_bal_vip = subparsers.add_parser("balancesheet_vip", help="资产负债表（VIP）")
    p_bal_vip.add_argument("--ts_code")
    p_bal_vip.add_argument("--ann_date")
    p_bal_vip.add_argument("--f_ann_date")
    p_bal_vip.add_argument("--start_date")
    p_bal_vip.add_argument("--end_date")
    p_bal_vip.add_argument("--period")
    p_bal_vip.add_argument("--report_type")
    p_bal_vip.add_argument("--comp_type")

    # cashflow
    p_cash = subparsers.add_parser("cashflow", help="现金流量表")
    p_cash.add_argument("--ts_code")
    p_cash.add_argument("--ann_date")
    p_cash.add_argument("--f_ann_date")
    p_cash.add_argument("--start_date")
    p_cash.add_argument("--end_date")
    p_cash.add_argument("--period")
    p_cash.add_argument("--report_type")
    p_cash.add_argument("--comp_type")
    p_cash.add_argument("--is_calc", type=int)

    # cashflow_vip
    p_cash_vip = subparsers.add_parser("cashflow_vip", help="现金流量表（VIP）")
    p_cash_vip.add_argument("--ts_code")
    p_cash_vip.add_argument("--ann_date")
    p_cash_vip.add_argument("--f_ann_date")
    p_cash_vip.add_argument("--start_date")
    p_cash_vip.add_argument("--end_date")
    p_cash_vip.add_argument("--period")
    p_cash_vip.add_argument("--report_type")
    p_cash_vip.add_argument("--comp_type")
    p_cash_vip.add_argument("--is_calc", type=int)

    args = parser.parse_args()
    if not args.api:
        parser.print_help()
        sys.exit(1)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 调用 {args.api}")

    if args.api == "forecast":
        df = fetch_forecast(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            type_=args.type_
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "forecast_vip":
        df = fetch_forecast_vip(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            type_=args.type_
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "express":
        df = fetch_express(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "express_vip":
        df = fetch_express_vip(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "disclosure_date":
        df = fetch_disclosure_date(
            ts_code=args.ts_code,
            end_date=args.end_date,
            pre_date=args.pre_date,
            ann_date=args.ann_date,
            actual_date=args.actual_date
        )
        suffix = args.end_date or args.ts_code or "all"

    elif args.api == "fina_indicator":
        df = fetch_fina_indicator(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "fina_indicator_vip":
        df = fetch_fina_indicator_vip(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "income":
        df = fetch_income(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            f_ann_date=args.f_ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type,
            comp_type=args.comp_type
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "income_vip":
        df = fetch_income_vip(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            f_ann_date=args.f_ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type,
            comp_type=args.comp_type
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "balancesheet":
        df = fetch_balancesheet(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            f_ann_date=args.f_ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type,
            comp_type=args.comp_type
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "balancesheet_vip":
        df = fetch_balancesheet_vip(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            f_ann_date=args.f_ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type,
            comp_type=args.comp_type
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "cashflow":
        df = fetch_cashflow(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            f_ann_date=args.f_ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type,
            comp_type=args.comp_type,
            is_calc=args.is_calc
        )
        suffix = args.ts_code or args.period or "all"

    elif args.api == "cashflow_vip":
        df = fetch_cashflow_vip(
            ts_code=args.ts_code,
            ann_date=args.ann_date,
            f_ann_date=args.f_ann_date,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type,
            comp_type=args.comp_type,
            is_calc=args.is_calc
        )
        suffix = args.ts_code or args.period or "all"

    if df is not None and not df.empty:
        print(f"获取到 {len(df)} 条数据")
        print(f"字段: {list(df.columns)}")
        save_to_csv(df, args.api, suffix)
    else:
        print("未获取到数据")


if __name__ == "__main__":
    main()
