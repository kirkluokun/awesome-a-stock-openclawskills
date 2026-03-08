#!/usr/bin/env python3
"""
技术指标计算库
所有函数接受 DataFrame (需含 Close, High, Low, Volume 列) 并返回新增列后的 DataFrame

用法：
    from indicators import add_all, add_ma, add_macd, add_rsi, add_kdj, add_bollinger
    df = add_all(df)                    # 一次性计算全部指标
    df = add_macd(df)                   # 只加 MACD
    signals = generate_signals(df)      # 生成交易信号
"""

import pandas as pd
import numpy as np


# ============================================================
# 趋势指标
# ============================================================

def add_ma(df, periods=(5, 10, 20, 60, 120, 250), col='Close'):
    """简单移动平均线"""
    for p in periods:
        df[f'MA{p}'] = df[col].rolling(window=p).mean()
    return df


def add_ema(df, periods=(12, 26, 50, 200), col='Close'):
    """指数移动平均线"""
    for p in periods:
        df[f'EMA{p}'] = df[col].ewm(span=p, adjust=False).mean()
    return df


def add_macd(df, fast=12, slow=26, signal=9, col='Close'):
    """MACD 指标"""
    ema_f = df[col].ewm(span=fast, adjust=False).mean()
    ema_s = df[col].ewm(span=slow, adjust=False).mean()
    df['MACD_DIF'] = ema_f - ema_s
    df['MACD_DEA'] = df['MACD_DIF'].ewm(span=signal, adjust=False).mean()
    df['MACD_HIST'] = 2 * (df['MACD_DIF'] - df['MACD_DEA'])
    return df


# ============================================================
# 震荡指标
# ============================================================

def add_rsi(df, periods=(6, 14), col='Close'):
    """RSI 相对强弱指数"""
    for p in periods:
        delta = df[col].diff()
        gain = delta.where(delta > 0, 0).rolling(window=p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=p).mean()
        rs = gain / loss
        df[f'RSI{p}'] = 100 - (100 / (1 + rs))
    return df


def add_kdj(df, n=9, col_close='Close', col_high='High', col_low='Low'):
    """KDJ 指标"""
    low_min = df[col_low].rolling(window=n).min()
    high_max = df[col_high].rolling(window=n).max()
    denom = (high_max - low_min).replace(0, np.nan)  # 避免涨跌停/停牌时除零
    rsv = ((df[col_close] - low_min) / denom * 100).fillna(50)  # 除零时 RSV 默认 50
    df['KDJ_K'] = rsv.ewm(com=2, adjust=False).mean()
    df['KDJ_D'] = df['KDJ_K'].ewm(com=2, adjust=False).mean()
    df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']
    return df


def add_bollinger(df, period=20, std_dev=2, col='Close'):
    """布林带"""
    df['BOLL_MID'] = df[col].rolling(window=period).mean()
    std = df[col].rolling(window=period).std()
    df['BOLL_UPPER'] = df['BOLL_MID'] + std_dev * std
    df['BOLL_LOWER'] = df['BOLL_MID'] - std_dev * std
    return df


# ============================================================
# 成交量指标
# ============================================================

def add_obv(df, col_close='Close', col_volume='Volume'):
    """OBV 能量潮"""
    df['OBV'] = (np.sign(df[col_close].diff()) * df[col_volume]).fillna(0).cumsum()
    return df


def add_volume_ratio(df, period=5, col_volume='Volume'):
    """量比"""
    df['VOL_RATIO'] = df[col_volume] / df[col_volume].rolling(window=period).mean()
    return df


# ============================================================
# 波动率指标
# ============================================================

def add_atr(df, period=14, col_high='High', col_low='Low', col_close='Close'):
    """ATR 真实波动幅度均值"""
    tr1 = df[col_high] - df[col_low]
    tr2 = abs(df[col_high] - df[col_close].shift(1))
    tr3 = abs(df[col_low] - df[col_close].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df[f'ATR{period}'] = tr.rolling(window=period).mean()
    return df


# ============================================================
# 组合函数
# ============================================================

def add_all(df):
    """一次性计算全部技术指标"""
    df = add_ma(df)
    df = add_ema(df)
    df = add_macd(df)
    df = add_rsi(df)
    df = add_kdj(df)
    df = add_bollinger(df)
    df = add_obv(df)
    df = add_volume_ratio(df)
    df = add_atr(df)
    return df


# ============================================================
# 信号生成
# ============================================================

def generate_signals(df):
    """
    基于技术指标生成交易信号汇总
    返回: [(信号名, 方向, 说明), ...]
    """
    if len(df) < 2:
        return [('⚠️ 数据不足', '无法判断', '需要至少2行数据才能生成信号')]

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    signals = []

    # MACD
    if 'MACD_DIF' in df.columns:
        if prev['MACD_DIF'] < prev['MACD_DEA'] and latest['MACD_DIF'] > latest['MACD_DEA']:
            signals.append(('🟢 MACD 金叉', '看多', 'DIF 上穿 DEA'))
        elif prev['MACD_DIF'] > prev['MACD_DEA'] and latest['MACD_DIF'] < latest['MACD_DEA']:
            signals.append(('🔴 MACD 死叉', '看空', 'DIF 下穿 DEA'))

    # RSI
    rsi = latest.get('RSI14', 50)
    if rsi > 70:
        signals.append(('🔴 RSI 超买', '看空', f'RSI={rsi:.1f} > 70'))
    elif rsi < 30:
        signals.append(('🟢 RSI 超卖', '看多', f'RSI={rsi:.1f} < 30'))

    # KDJ
    if 'KDJ_K' in df.columns:
        if prev['KDJ_K'] < prev['KDJ_D'] and latest['KDJ_K'] > latest['KDJ_D']:
            signals.append(('🟢 KDJ 金叉', '看多', 'K 上穿 D'))
        elif prev['KDJ_K'] > prev['KDJ_D'] and latest['KDJ_K'] < latest['KDJ_D']:
            signals.append(('🔴 KDJ 死叉', '看空', 'K 下穿 D'))

    # 均线排列
    if all(k in latest.index for k in ['MA20', 'MA60']):
        if latest['Close'] > latest['MA20'] > latest['MA60']:
            signals.append(('🟢 多头排列', '看多', '价格 > MA20 > MA60'))
        elif latest['Close'] < latest['MA20'] < latest['MA60']:
            signals.append(('🔴 空头排列', '看空', '价格 < MA20 < MA60'))

    # 布林带
    if 'BOLL_UPPER' in df.columns:
        if latest['Close'] > latest['BOLL_UPPER']:
            signals.append(('🔴 突破上轨', '注意', '可能高位回调'))
        elif latest['Close'] < latest['BOLL_LOWER']:
            signals.append(('🟢 跌破下轨', '注意', '可能低位反弹'))

    # 量价
    if 'VOL_RATIO' in df.columns and latest.get('VOL_RATIO', 1) > 2:
        signals.append(('⚡ 放量', '关注', f'量比={latest["VOL_RATIO"]:.1f}'))

    return signals
