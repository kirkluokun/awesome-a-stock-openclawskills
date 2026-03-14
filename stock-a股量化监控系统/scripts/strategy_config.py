#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化策略配置
区分短线和中长线策略
"""

# ============== 短线策略配置 ==============

SHORT_TERM_STRATEGIES = {
    'rsi_short': {
        'name': 'RSI短线',
        'type': 'short',
        'period': '1-3天',
        'params': {
            'rsi_period': 6,      # 短周期RSI
            'oversold': 25,       # 超卖阈值（更激进）
            'overbought': 75,     # 超买阈值（更激进）
        },
        'description': '超短线RSI策略，适合T+0或快速进出'
    },
    'macd_short': {
        'name': 'MACD短线',
        'type': 'short',
        'period': '2-5天',
        'params': {
            'fast': 8,
            'slow': 17,
            'signal': 9,
        },
        'description': 'MACD金叉死叉，短期趋势跟踪'
    },
    'kdj_short': {
        'name': 'KDJ短线',
        'type': 'short',
        'period': '1-3天',
        'params': {
            'n': 9,
            'oversold': 20,
            'overbought': 80,
        },
        'description': 'KDJ超买超卖，适合日内波段'
    },
    'boll_breakout': {
        'name': '布林突破短线',
        'type': 'short',
        'period': '1-5天',
        'params': {
            'period': 10,         # 短周期布林
            'std': 1.5,          # 标准差倍数
        },
        'description': '布林带突破，捕捉短期波动'
    },
    'volume_surge': {
        'name': '放量突破',
        'type': 'short',
        'period': '1-3天',
        'params': {
            'volume_ratio': 2.0,  # 放量2倍
            'price_change': 3.0,  # 涨幅>3%
        },
        'description': '量价齐升，短期强势股'
    },
}

# ============== 中长线策略配置 ==============

LONG_TERM_STRATEGIES = {
    'ma_trend': {
        'name': 'MA趋势中长线',
        'type': 'long',
        'period': '20-60天',
        'params': {
            'ma_short': 20,
            'ma_long': 60,
            'ma_filter': 120,    # 长期趋势过滤
        },
        'description': '均线多头排列，趋势跟踪'
    },
    'macd_trend': {
        'name': 'MACD趋势',
        'type': 'long',
        'period': '15-30天',
        'params': {
            'fast': 12,
            'slow': 26,
            'signal': 9,
            'hold_days': 15,     # 最少持仓天数
        },
        'description': 'MACD趋势确认，中期持有'
    },
    'value_growth': {
        'name': '价值成长',
        'type': 'long',
        'period': '60-180天',
        'params': {
            'rsi_threshold': 40,  # RSI回调买入
            'ma_filter': 200,     # 长期趋势线
            'min_hold': 30,       # 最少30天
        },
        'description': '价值投资，长期持有优质股'
    },
    'position_building': {
        'name': '分批建仓',
        'type': 'long',
        'period': '30-90天',
        'params': {
            'ma_periods': [20, 60, 120],
            'rsi_levels': [40, 35, 30],  # 分批买入点
            'position_sizes': [0.3, 0.4, 0.3],  # 仓位分配
        },
        'description': '均线支撑位分批建仓'
    },
    'trend_following': {
        'name': '趋势跟随',
        'type': 'long',
        'period': '30-120天',
        'params': {
            'ma_short': 30,
            'ma_long': 60,
            'atr_period': 20,    # ATR止损
            'atr_multiplier': 2.0,
        },
        'description': '中长期趋势跟随+ATR止损'
    },
}

# ============== 策略选择建议 ==============

STRATEGY_RECOMMENDATIONS = {
    'short': {
        '震荡市': ['rsi_short', 'kdj_short', 'boll_breakout'],
        '单边上涨': ['volume_surge', 'macd_short'],
        '单边下跌': ['rsi_short'],  # 抢反弹
        '高波动': ['kdj_short', 'boll_breakout'],
        '低波动': ['volume_surge'],  # 等待突破
    },
    'long': {
        '牛市': ['ma_trend', 'trend_following'],
        '熊市': ['value_growth', 'position_building'],
        '震荡': ['position_building'],  # 分批低吸
        '突破': ['macd_trend', 'trend_following'],
    }
}

# ============== 持仓时间建议 ==============

HOLDING_PERIOD = {
    'short': {
        'min_days': 1,
        'max_days': 5,
        'target_days': 2,
        # 固定止损止盈（已废弃，改用ATR动态止损）
        'stop_loss': -3.0,    # 备用固定止损-3%
        'take_profit': 5.0,   # 备用固定止盈+5%
    },
    'long': {
        'min_days': 15,
        'max_days': 120,
        'target_days': 45,
        'stop_loss': -8.0,    # 止损-8%
        'take_profit': 20.0,  # 止盈+20%
    }
}

# ============== 动态止损止盈配置 (ATR) ==============

ATR_STOP_LOSS = {
    'short': {
        'atr_period': 7,           # ATR计算周期
        'stop_multiplier': 2.0,    # 止损 = 买入价 - ATR * 2.0 (约-2%~-5%)
        'profit_multiplier': 3.0,  # 止盈 = 买入价 + ATR * 3.0 (约+3%~+8%)
        # 追踪止损
        'trailing_enabled': True,
        'trailing_trigger': 2.0,   # 盈利>ATR*2时激活追踪止损
        'trailing_lock': 1.5,      # 盈利>ATR*3时，止损移至买入价+ATR*1.5
        # 备用固定值（当ATR无效时）
        'fallback_stop': -3.0,
        'fallback_profit': 5.0,
    },
    'long': {
        'atr_period': 14,
        'stop_multiplier': 2.5,
        'profit_multiplier': 4.0,
        'trailing_enabled': True,
        'trailing_trigger': 2.0,
        'trailing_lock': 1.5,
        'fallback_stop': -8.0,
        'fallback_profit': 20.0,
    }
}

# ============== 买入信号权重配置 ==============

BUY_SIGNAL_WEIGHTS = {
    'rsi_oversold': 20,        # RSI超卖 (<30)
    'kdj_golden_cross': 20,    # KDJ金叉 (K上穿D且J<50)
    'macd_golden_cross': 15,   # MACD金叉 (DIF上穿DEA)
    'bollinger_bounce': 15,    # 布林下轨反弹
    'volume_surge': 15,        # 放量突破 (量比>1.5且涨幅>2%)
    'fund_inflow': 15,         # 主力流入 (>500万)
}

# 买入阈值
BUY_SCORE_THRESHOLD = {
    'strong': 70,    # A级：强烈推荐
    'normal': 60,    # B级：可操作
    'weak': 50,      # C级：观望
}

# ============== 卖出信号配置 ==============

SELL_SIGNALS = {
    # 止损类（最高优先级）
    'atr_stop_loss': {
        'priority': 1,
        'description': '价格 < 买入价 - ATR*2',
    },
    # 止盈类
    'atr_take_profit': {
        'priority': 2,
        'description': '价格 > 买入价 + ATR*3',
    },
    # 技术指标类
    'kdj_death_cross': {
        'priority': 3,
        'condition': 'K下穿D且J>70',
    },
    'macd_death_cross': {
        'priority': 3,
        'condition': 'DIF下穿DEA',
    },
    'bollinger_upper': {
        'priority': 4,
        'condition': '价格触及上轨',
    },
    # 时间止损
    'time_stop': {
        'priority': 5,
        'condition': '持仓>5天未盈利',
        'days': 5,
    },
}

# ============== 风险控制参数 ==============

RISK_CONTROL = {
    'short': {
        'max_position': 0.3,   # 单只最多30%
        'max_stocks': 5,       # 最多5只
        'daily_loss_limit': -5.0,  # 日亏损限制
    },
    'long': {
        'max_position': 0.25,  # 单只最多25%
        'max_stocks': 8,       # 最多8只
        'monthly_loss_limit': -15.0,  # 月亏损限制
    }
}


def get_strategy_config(strategy_name: str, strategy_type: str = None):
    """获取策略配置"""
    if strategy_type == 'short':
        return SHORT_TERM_STRATEGIES.get(strategy_name)
    elif strategy_type == 'long':
        return LONG_TERM_STRATEGIES.get(strategy_name)
    else:
        # 自动判断
        if strategy_name in SHORT_TERM_STRATEGIES:
            return SHORT_TERM_STRATEGIES[strategy_name]
        elif strategy_name in LONG_TERM_STRATEGIES:
            return LONG_TERM_STRATEGIES[strategy_name]
    return None


def list_strategies(strategy_type: str = None):
    """列出所有策略"""
    if strategy_type == 'short':
        return SHORT_TERM_STRATEGIES
    elif strategy_type == 'long':
        return LONG_TERM_STRATEGIES
    else:
        return {
            'short': SHORT_TERM_STRATEGIES,
            'long': LONG_TERM_STRATEGIES
        }


def recommend_strategy(market_condition: str, strategy_type: str):
    """根据市场情况推荐策略"""
    recommendations = STRATEGY_RECOMMENDATIONS.get(strategy_type, {})
    return recommendations.get(market_condition, [])


if __name__ == '__main__':
    print("=" * 60)
    print("量化策略配置")
    print("=" * 60)
    print()
    
    print("📊 短线策略:")
    for name, config in SHORT_TERM_STRATEGIES.items():
        print(f"  • {config['name']} ({config['period']})")
        print(f"    {config['description']}")
    
    print()
    print("📈 中长线策略:")
    for name, config in LONG_TERM_STRATEGIES.items():
        print(f"  • {config['name']} ({config['period']})")
        print(f"    {config['description']}")
    
    print()
    print("💡 震荡市推荐:")
    print(f"  短线: {recommend_strategy('震荡市', 'short')}")
    print(f"  长线: {recommend_strategy('震荡', 'long')}")
