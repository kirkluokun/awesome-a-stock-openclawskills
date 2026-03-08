#!/usr/bin/env python3
"""
yfinance 数据获取器 — 补充 Tushare MCP 未覆盖的资产
主要用于：国际商品期货(CL=F, GC=F...)、加密货币(BTC-USD)、国际指数、部分外汇

A 股 / 港股 / 美股 / 国内期货 / 宏观数据 → 请直接使用 tushare MCP tool

用法：
    from data_fetcher import fetch, fetch_multi, identify_asset_type
    python data_fetcher.py AAPL --period 1y
    python data_fetcher.py --check
"""

import sys
import argparse
import pandas as pd
import numpy as np

# ===== 商品/指数中文名映射 =====
COMMODITY_TICKERS = {
    '原油': 'CL=F', 'crude': 'CL=F', 'wti': 'CL=F',
    'brent': 'BZ=F', '布伦特': 'BZ=F',
    '天然气': 'NG=F', 'natgas': 'NG=F',
    '汽油': 'RB=F', '取暖油': 'HO=F',
    '黄金': 'GC=F', 'gold': 'GC=F',
    '白银': 'SI=F', 'silver': 'SI=F',
    '铂金': 'PL=F', '钯金': 'PA=F',
    '铜': 'HG=F', 'copper': 'HG=F',
    '大豆': 'ZS=F', '豆粕': 'ZM=F', '豆油': 'ZL=F',
    '玉米': 'ZC=F', '小麦': 'ZW=F',
    '棉花': 'CT=F', '糖': 'SB=F', '咖啡': 'KC=F', '可可': 'CC=F',
    '活牛': 'LE=F', '瘦肉猪': 'HE=F',
}

INDEX_TICKERS = {
    '标普500': '^GSPC', 'sp500': '^GSPC',
    '纳斯达克': '^IXIC', 'nasdaq': '^IXIC',
    '道琼斯': '^DJI', 'dow': '^DJI',
    '恐慌指数': '^VIX', 'vix': '^VIX',
    '美元指数': 'DX-Y.NYB', 'dxy': 'DX-Y.NYB',
    '日经': '^N225', 'nikkei': '^N225',
}


def identify_asset_type(symbol: str) -> dict:
    """识别资产类型，返回 {ticker, type, market}"""
    s = symbol.lower().strip()
    su = symbol.upper().strip()
    if s in COMMODITY_TICKERS:
        return {'ticker': COMMODITY_TICKERS[s], 'type': 'commodity', 'market': 'global', 'name_cn': symbol}
    if s in INDEX_TICKERS:
        return {'ticker': INDEX_TICKERS[s], 'type': 'index', 'market': 'global', 'name_cn': symbol}
    if su.endswith('=F'):
        return {'ticker': su, 'type': 'commodity', 'market': 'global', 'name_cn': ''}
    if '-USD' in su or '-USDT' in su:
        return {'ticker': su, 'type': 'crypto', 'market': 'global', 'name_cn': ''}
    if su.endswith('=X'):
        return {'ticker': su, 'type': 'forex', 'market': 'global', 'name_cn': ''}
    if symbol.startswith('^'):
        return {'ticker': symbol, 'type': 'index', 'market': 'global', 'name_cn': ''}
    return {'ticker': su, 'type': 'stock', 'market': 'US', 'name_cn': ''}


def fetch(symbol: str, period: str = '1y', interval: str = '1d',
          start: str = None, end: str = None) -> pd.DataFrame:
    """
    通过 yfinance 获取数据，返回标准化 DataFrame (Open, High, Low, Close, Volume)

    Args:
        symbol: ticker 或中文名（自动映射）
        period: 1d/5d/1mo/3mo/6mo/1y/2y/5y/10y/ytd/max
        interval: 1m/5m/15m/30m/1h/1d/1wk/1mo
        start/end: YYYY-MM-DD 格式，指定时 period 无效
    """
    import yfinance as yf
    asset = identify_asset_type(symbol)
    ticker = asset['ticker']
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end, interval=interval) if start else stock.history(period=period, interval=interval)
    if hist.empty:
        raise ValueError(f"未获取到 {ticker} 的数据")
    # 部分外汇/指数可能没有 Volume 列
    cols = ['Open', 'High', 'Low', 'Close']
    if 'Volume' in hist.columns:
        cols.append('Volume')
    df = hist[cols].copy()
    if 'Volume' not in df.columns:
        df['Volume'] = 0
    df.index.name = 'Date'
    return df


def fetch_multi(symbols: list, period: str = '1y', column: str = 'Close',
                how: str = 'inner') -> pd.DataFrame:
    """获取多资产数据合并为 DataFrame，列名为资产代码

    Args:
        how: 合并方式，'inner'(交集，无NaN) / 'outer'(并集，可能有NaN)
    """
    dfs = {}
    for s in symbols:
        try:
            df = fetch(s, period=period)
            asset = identify_asset_type(s)
            label = asset.get('name_cn') or asset['ticker']
            dfs[label] = df[column]
        except Exception as e:
            print(f"⚠️ {s}: {e}")
    if not dfs:
        return pd.DataFrame()
    result = pd.DataFrame(dfs)
    if how == 'inner':
        result = result.dropna()
    return result


def get_info(symbol: str) -> dict:
    """获取资产基本信息（仅 yfinance 支持的）"""
    import yfinance as yf
    return yf.Ticker(identify_asset_type(symbol)['ticker']).info


def check_env():
    """检查环境依赖"""
    pkgs = {
        'pandas': 'pandas', 'numpy': 'numpy', 'matplotlib': 'matplotlib',
        'seaborn': 'seaborn', 'yfinance': 'yfinance', 'mplfinance': 'mplfinance',
        'statsmodels': 'statsmodels', 'arch': 'arch', 'scipy': 'scipy',
        'sklearn': 'scikit-learn', 'hmmlearn': 'hmmlearn', 'ruptures': 'ruptures',
        'networkx': 'networkx', 'pywt': 'PyWavelets',
    }
    optional = {'prophet': 'prophet'}
    print("🔍 环境检查\n" + "=" * 40)
    ok = True
    for mod, pkg in pkgs.items():
        try:
            __import__(mod)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg}")
            ok = False
    print("\n📦 可选:")
    for mod, pkg in optional.items():
        try:
            __import__(mod)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ⚪ {pkg}")
    print("=" * 40)
    print("✅ 就绪" if ok else "⚠️ 请运行: pip install -r requirements.txt")
    return ok


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='yfinance 数据获取器')
    parser.add_argument('symbol', nargs='?')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--period', default='1y')
    parser.add_argument('--interval', default='1d')
    parser.add_argument('--start', default=None)
    parser.add_argument('--end', default=None)
    parser.add_argument('--save', default=None)
    args = parser.parse_args()
    if args.check:
        check_env()
    elif args.symbol:
        df = fetch(args.symbol, args.period, args.interval, args.start, args.end)
        print(f"📈 {len(df)} 条 ({df.index[0].date()} ~ {df.index[-1].date()})")
        print(df.tail(10))
        if args.save:
            df.to_csv(args.save)
            print(f"💾 → {args.save}")
    else:
        parser.print_help()
