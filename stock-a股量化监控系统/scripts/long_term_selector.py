#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中长线选股引擎
每日推荐5-10只优质股票
综合多维度指标评分
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from typing import List, Dict
from smart_data_source import SmartDataSource
from stock_cache_db import StockCache
from advanced_indicators import AdvancedIndicators


class LongTermSelector:
    """中长线选股引擎"""
    
    def __init__(self):
        self.ds = SmartDataSource()
        self.cache = StockCache()
        self.indicators = AdvancedIndicators()
        
    def load_watchlist(self) -> List[str]:
        """加载监控列表，过滤创业板和科创板"""
        try:
            with open('watchlist.json', 'r') as f:
                all_stocks = json.load(f)
            
            # 过滤: 排除3开头(创业板)和688开头(科创板)
            filtered = [
                code for code in all_stocks 
                if not code.startswith('3') and not code.startswith('688')
            ]
            
            return filtered
        except:
            return []
    
    def analyze_single_stock(self, code: str) -> Dict:
        """
        分析单只股票
        返回综合评分和详细数据
        """
        try:
            # 获取历史数据
            df = self.ds.get_history_data(code, days=120)
            if df is None or df.empty or len(df) < 60:
                return None
            
            # 获取基础信息
            stock_info = self.cache.get_stock(code)
            if not stock_info:
                return None
            
            score = 0
            max_score = 100
            details = {}
            
            # ====== 1. 趋势评分 (30分) ======
            trend = self.indicators.score_trend(df)
            trend_score = trend['score'] * 0.30  # 转换为30分制
            score += trend_score
            
            details['trend'] = {
                'score': trend_score,
                'rating': trend['rating'],
                'reasons': trend['reasons'],
                'ma20': trend['ma20'],
                'ma60': trend['ma60']
            }
            
            # ====== 2. 动量评分 (15分) ======
            returns_5d = (df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6] * 100
            returns_20d = (df['close'].iloc[-1] - df['close'].iloc[-21]) / df['close'].iloc[-21] * 100
            
            momentum_score = 0
            if returns_5d > 0:
                momentum_score += 5
            if returns_20d > 0:
                momentum_score += 10
            
            score += momentum_score
            details['momentum'] = {
                'score': momentum_score,
                'returns_5d': returns_5d,
                'returns_20d': returns_20d
            }
            
            # ====== 3. 量能评分 (15分) ======
            obv = self.indicators.calc_obv(df)
            vol_ratio = self.indicators.calc_volume_ratio(df)
            
            volume_score = 0
            # OBV上升
            if obv.iloc[-1] > obv.iloc[-20]:
                volume_score += 8
            # 量比合理（0.8-2.0）
            if 0.8 < vol_ratio.iloc[-1] < 2.0:
                volume_score += 7
            
            score += volume_score
            details['volume'] = {
                'score': volume_score,
                'obv_trend': 'up' if obv.iloc[-1] > obv.iloc[-20] else 'down',
                'volume_ratio': vol_ratio.iloc[-1]
            }
            
            # ====== 4. 趋势强度 (10分) ======
            adx, plus_di, minus_di = self.indicators.calc_adx(df)
            
            strength_score = 0
            if adx.iloc[-1] > 25:  # ADX>25表示趋势明显
                strength_score += 5
            if plus_di.iloc[-1] > minus_di.iloc[-1]:  # 多头强势
                strength_score += 5
            
            score += strength_score
            details['strength'] = {
                'score': strength_score,
                'adx': adx.iloc[-1],
                'plus_di': plus_di.iloc[-1],
                'minus_di': minus_di.iloc[-1]
            }
            
            # ====== 5. 波动率评分 (10分) ======
            atr = self.indicators.calc_atr(df)
            volatility = df['close'].pct_change().std() * np.sqrt(252) * 100
            
            volatility_score = 0
            # 波动率适中（15-35%年化）
            if 15 < volatility < 35:
                volatility_score = 10
            elif 10 < volatility <= 15 or 35 <= volatility < 50:
                volatility_score = 5
            
            score += volatility_score
            details['volatility'] = {
                'score': volatility_score,
                'annual_volatility': volatility,
                'atr': atr.iloc[-1]
            }
            
            # ====== 6. 乖离率评分 (10分) ======
            bias = self.indicators.calc_bias(df, period=20)
            
            bias_score = 0
            # 乖离率在合理范围(-10% ~ +15%)
            if -10 < bias.iloc[-1] < 15:
                bias_score = 10
            elif -15 < bias.iloc[-1] <= -10 or 15 <= bias.iloc[-1] < 20:
                bias_score = 5
            
            score += bias_score
            details['bias'] = {
                'score': bias_score,
                'bias_value': bias.iloc[-1]
            }
            
            # ====== 7. 资金流评分 (10分) ======
            fund_flow = self.cache.get_fund_flow(code)
            
            fund_score = 0
            if fund_flow:
                main_in = fund_flow.get('main_in', 0)
                if main_in > 0:
                    fund_score = 10
                elif main_in > -100000000:  # 流出不严重
                    fund_score = 5
            else:
                fund_score = 5  # 无数据给中等分
            
            score += fund_score
            details['fund_flow'] = {
                'score': fund_score,
                'main_in': fund_flow.get('main_in', 0) / 10000 if fund_flow else 0
            }
            
            # ====== 8. 计算买卖点（基于ATR动态止损） ======
            current_price = float(stock_info.get('price', df['close'].iloc[-1]))
            atr_value = atr.iloc[-1]

            # 中长线使用更宽松的止损止盈
            stop_multiplier = 2.5  # ATR*2.5
            profit_multiplier = 4.0  # ATR*4.0

            if atr_value > 0 and current_price > 0:
                stop_loss = current_price - atr_value * stop_multiplier
                take_profit = current_price + atr_value * profit_multiplier
                stop_loss_pct = (stop_loss - current_price) / current_price * 100
                take_profit_pct = (take_profit - current_price) / current_price * 100
                risk = current_price - stop_loss
                reward = take_profit - current_price
                risk_reward_ratio = reward / risk if risk > 0 else 2.5
            else:
                # 默认值
                stop_loss = current_price * 0.92
                take_profit = current_price * 1.20
                stop_loss_pct = -8.0
                take_profit_pct = 20.0
                risk_reward_ratio = 2.5

            details['trade_points'] = {
                'buy_price': round(current_price, 2),
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'stop_loss_pct': round(stop_loss_pct, 2),
                'take_profit_pct': round(take_profit_pct, 2),
                'risk_reward_ratio': round(risk_reward_ratio, 2)
            }

            # 生成买入信号列表
            buy_signals = []
            if trend['rating'] in ['强势上涨', '稳健上涨']:
                buy_signals.append(f"趋势良好 ({trend['rating']})")
            if returns_20d > 5:
                buy_signals.append(f"20日涨幅 (+{returns_20d:.1f}%)")
            if obv.iloc[-1] > obv.iloc[-20]:
                buy_signals.append("OBV持续上升")
            if adx.iloc[-1] > 25 and plus_di.iloc[-1] > minus_di.iloc[-1]:
                buy_signals.append(f"趋势强度高 (ADX={adx.iloc[-1]:.0f})")
            if fund_flow and fund_flow.get('main_in', 0) > 0:
                buy_signals.append(f"主力流入 (+{fund_flow.get('main_in', 0)/10000:.0f}万)")

            # ====== 汇总结果 ======
            result = {
                'code': code,
                'name': stock_info.get('name', 'Unknown'),
                'price': current_price,
                'change_pct': float(stock_info.get('change_pct', 0)),
                'score': round(float(score), 2),
                'rating': self._get_rating(score),
                'details': self._convert_to_json_safe(details),
                'signals': [trend['rating']] + trend['reasons'][:2],
                'buy_signals': buy_signals,
                'buy_signal_count': len(buy_signals),
                # 买卖点字段
                'buy_price': round(current_price, 2),
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'stop_loss_pct': round(stop_loss_pct, 2),
                'take_profit_pct': round(take_profit_pct, 2),
                'risk_reward_ratio': round(risk_reward_ratio, 2),
                'recommend': bool(score >= 70),  # 70分以上推荐
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            return result
            
        except Exception as e:
            print(f"分析{code}失败: {e}")
            return None
    
    def _get_rating(self, score: float) -> str:
        """评级"""
        if score >= 85:
            return 'A+'
        elif score >= 75:
            return 'A'
        elif score >= 65:
            return 'B+'
        elif score >= 55:
            return 'B'
        elif score >= 45:
            return 'C'
        else:
            return 'D'
    
    def _convert_to_json_safe(self, obj):
        """
        转换为JSON安全的数据类型
        处理numpy/pandas类型、布尔值和NaN
        """
        import numpy as np
        import math
        
        if isinstance(obj, dict):
            return {k: self._convert_to_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_safe(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            val = float(obj)
            # 处理NaN和Infinity
            if math.isnan(val) or math.isinf(val):
                return None
            return val
        elif isinstance(obj, float):
            # 处理原生float的NaN
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, bool):
            return bool(obj)
        elif obj is None:
            return None
        else:
            return obj
    
    def select_top_stocks(self, top_n: int = 10) -> List[Dict]:
        """
        选择TOP N股票
        返回推荐列表
        """
        print("=" * 60)
        print(f"🎯 中长线选股 - TOP {top_n}")
        print("=" * 60)
        print()
        
        watchlist = self.load_watchlist()
        if not watchlist:
            print("❌ 监控列表为空")
            return []
        
        print(f"📊 分析 {len(watchlist)} 只股票...")
        print()
        
        results = []
        for i, code in enumerate(watchlist, 1):
            print(f"[{i}/{len(watchlist)}] {code}...", end=" ")
            
            result = self.analyze_single_stock(code)
            if result:
                print(f"✅ {result['score']:.1f}分 ({result['rating']})")
                results.append(result)
            else:
                print("❌ 分析失败")
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 取TOP N
        top_stocks = results[:top_n]
        
        print()
        print("=" * 60)
        print(f"📈 推荐结果 (TOP {len(top_stocks)})")
        print("=" * 60)
        print()
        
        for i, stock in enumerate(top_stocks, 1):
            print(f"{i}. {stock['name']} ({stock['code']})")
            print(f"   评分: {stock['score']:.1f} ({stock['rating']})")
            print(f"   价格: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)")
            print(f"   趋势: {stock['details']['trend']['rating']} | "
                  f"动量: {stock['details']['momentum']['returns_20d']:+.2f}% | "
                  f"资金: {stock['details']['fund_flow']['main_in']:+.0f}万")
            print()
        
        return top_stocks
    
    def generate_report(self, stocks: List[Dict]) -> str:
        """生成推荐报告"""
        report = []
        report.append("=" * 60)
        report.append(f"📊 中长线选股报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")
        
        for i, stock in enumerate(stocks, 1):
            report.append(f"{i}. {stock['name']} ({stock['code']})")
            report.append(f"   评级: {stock['rating']} | 评分: {stock['score']:.1f}/100")
            report.append(f"   价格: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)")
            report.append("")
            
            # 详细分析
            details = stock['details']
            report.append("   📈 技术面:")
            report.append(f"      趋势: {details['trend']['rating']} ({details['trend']['score']:.1f}/30)")
            report.append(f"      动量: 5日{details['momentum']['returns_5d']:+.2f}% | 20日{details['momentum']['returns_20d']:+.2f}%")
            report.append(f"      量能: {details['volume']['obv_trend']} | 量比{details['volume']['volume_ratio']:.2f}")
            report.append(f"      强度: ADX={details['strength']['adx']:.1f}")
            report.append("")
            
            report.append("   💰 资金面:")
            report.append(f"      主力: {details['fund_flow']['main_in']:+.0f}万")
            report.append("")
            
            report.append("   ✅ 推荐理由:")
            for reason in details['trend']['reasons'][:3]:
                report.append(f"      • {reason}")
            report.append("")
            report.append("-" * 60)
            report.append("")
        
        return "\n".join(report)
    
    def close(self):
        self.ds.close()
        self.cache.close()


if __name__ == '__main__':
    selector = LongTermSelector()
    
    # 选择TOP 5
    top_stocks = selector.select_top_stocks(top_n=5)
    
    # 生成报告
    if top_stocks:
        report = selector.generate_report(top_stocks)
        print(report)
        
        # 保存到文件
        with open('daily_recommendation.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("✅ 报告已保存到 daily_recommendation.txt")
    
    selector.close()
