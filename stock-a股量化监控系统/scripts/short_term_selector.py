#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短线选股引擎 (优化版)
每日推荐3-5只短线机会股
排除创业板(3开头)和科创板(688开头)

优化内容：
1. 新增MACD、布林带指标评分
2. 动态止损止盈（基于ATR）
3. 精确买卖点输出
4. 多指标共振确认

评分体系 (满分100分):
- RSI信号: 20分
- KDJ信号: 20分
- MACD信号: 15分
- 布林带信号: 15分
- 量价异动: 15分
- 资金流向: 15分
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from typing import List, Dict
from smart_data_source import SmartDataSource
from stock_cache_db import StockCache
from short_term_indicators import ShortTermIndicators


class ShortTermSelector:
    """短线选股引擎"""
    
    def __init__(self):
        self.ds = SmartDataSource()
        self.cache = StockCache()
        self.indicators = ShortTermIndicators()
        
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
        短线分析单只股票 (优化版)
        评分满分100分，新增MACD/布林带/动态止损止盈

        评分体系:
        - RSI信号: 20分
        - KDJ信号: 20分
        - MACD信号: 15分
        - 布林带信号: 15分
        - 量价异动: 15分
        - 资金流向: 15分
        """
        try:
            # 获取历史数据（短线只需30天）
            df = self.ds.get_history_data(code, days=30)
            if df is None or df.empty or len(df) < 10:
                return None

            # 获取基础信息
            stock_info = self.cache.get_stock(code)
            if not stock_info:
                return None

            score = 0
            details = {}
            signals = []
            buy_signals = []  # 买入信号列表
            sell_signals = []  # 卖出信号列表

            current_price = float(stock_info.get('price', df['close'].iloc[-1]))

            # ====== 1. RSI超卖反弹 (20分) ======
            rsi = self.indicators.calc_rsi(df)
            rsi_now = rsi.iloc[-1]

            rsi_score = 0
            rsi_signal = None
            if rsi_now < 30:
                rsi_score = 20
                rsi_signal = f'RSI超卖 ({rsi_now:.0f})'
                buy_signals.append(rsi_signal)
                signals.append('RSI超卖')
            elif rsi_now < 40:
                rsi_score = 12
                rsi_signal = f'RSI偏低 ({rsi_now:.0f})'
            elif 40 <= rsi_now <= 60:
                rsi_score = 5
            elif rsi_now > 70:
                rsi_score = 0
                rsi_signal = f'RSI超买 ({rsi_now:.0f})'
                sell_signals.append(rsi_signal)

            score += rsi_score
            details['rsi'] = {
                'score': rsi_score,
                'value': rsi_now,
                'signal': rsi_signal
            }

            # ====== 2. KDJ金叉 (20分) ======
            k, d, j = self.indicators.calc_kdj(df)
            kdj_result = self.indicators.detect_kdj_cross(k, d, j)

            kdj_score = 0
            if kdj_result['golden_cross'] and kdj_result['j'] < 50:
                kdj_score = 20
                buy_signals.append(f"KDJ金叉 (K={kdj_result['k']:.0f}, J={kdj_result['j']:.0f})")
            elif kdj_result['oversold']:
                kdj_score = 15
                buy_signals.append(f"KDJ超卖 (J={kdj_result['j']:.0f})")
            elif kdj_result['death_cross'] and kdj_result['j'] > 70:
                kdj_score = -10
                sell_signals.append(f"KDJ死叉 (K={kdj_result['k']:.0f}, J={kdj_result['j']:.0f})")
            elif kdj_result['overbought']:
                kdj_score = -5
                sell_signals.append(f"KDJ超买 (J={kdj_result['j']:.0f})")
            elif kdj_result['score'] > 0:
                kdj_score = kdj_result['score']

            score += max(0, kdj_score)  # 负分不计入总分
            if kdj_result['signal']:
                signals.append(kdj_result['signal'])

            details['kdj'] = {
                'score': max(0, kdj_score),
                'k': kdj_result['k'],
                'd': kdj_result['d'],
                'j': kdj_result['j'],
                'signal': kdj_result['signal'],
                'golden_cross': kdj_result['golden_cross'],
                'death_cross': kdj_result['death_cross']
            }

            # ====== 3. MACD信号 (15分) ======
            dif, dea, macd_hist = self.indicators.calc_macd_short(df)
            macd_result = self.indicators.detect_macd_cross(dif, dea, macd_hist)

            macd_score = 0
            if macd_result['golden_cross']:
                macd_score = 15
                buy_signals.append(f"MACD金叉 (DIF={macd_result['dif']:.3f})")
            elif macd_result['signal'] == 'MACD翻红':
                macd_score = 10
                buy_signals.append("MACD柱翻红")
            elif macd_result['death_cross']:
                macd_score = -10
                sell_signals.append(f"MACD死叉 (DIF={macd_result['dif']:.3f})")
            elif macd_result['signal'] == 'MACD翻绿':
                macd_score = -5
                sell_signals.append("MACD柱翻绿")
            elif macd_result['macd_hist'] > 0 and macd_result['dif'] > macd_result['dea']:
                macd_score = 8  # MACD多头

            score += max(0, macd_score)
            if macd_result['signal']:
                signals.append(macd_result['signal'])

            details['macd'] = {
                'score': max(0, macd_score),
                'dif': macd_result['dif'],
                'dea': macd_result['dea'],
                'macd_hist': macd_result['macd_hist'],
                'signal': macd_result['signal'],
                'golden_cross': macd_result['golden_cross'],
                'death_cross': macd_result['death_cross']
            }

            # ====== 4. 布林带信号 (15分) ======
            upper, middle, lower = self.indicators.calc_bollinger(df)
            boll_result = self.indicators.detect_bollinger_signal(df, upper, middle, lower)

            boll_score = 0
            if boll_result['signal'] == '下轨反弹':
                boll_score = 15
                buy_signals.append(f"布林下轨反弹 (位置{boll_result['position_pct']:.0f}%)")
            elif boll_result['signal'] == '中轨支撑':
                boll_score = 10
                buy_signals.append("布林中轨支撑")
            elif boll_result['signal'] == '触及上轨':
                boll_score = -5
                sell_signals.append("布林触及上轨")
            elif boll_result['signal'] == '跌破下轨':
                boll_score = 5  # 超卖但风险较高
            elif boll_result['position_pct'] < 30:
                boll_score = 8  # 偏下轨

            score += max(0, boll_score)
            if boll_result['signal']:
                signals.append(boll_result['signal'])

            details['bollinger'] = {
                'score': max(0, boll_score),
                'upper': boll_result['upper'],
                'middle': boll_result['middle'],
                'lower': boll_result['lower'],
                'bandwidth': boll_result['bandwidth'],
                'position_pct': boll_result['position_pct'],
                'signal': boll_result['signal']
            }

            # ====== 5. 量价异动 (15分) ======
            volume_surge = self.indicators.detect_volume_surge(df, ratio=1.5)

            volume_score = 0
            if volume_surge['surge_type'] == '放量上涨':
                volume_score = 15
                buy_signals.append(f"放量突破 (量比{volume_surge['volume_ratio']:.1f})")
            elif volume_surge['volume_ratio'] > 1.5 and volume_surge['price_change'] > 2:
                volume_score = 12
                buy_signals.append(f"温和放量 (量比{volume_surge['volume_ratio']:.1f})")
            elif volume_surge['surge_type'] == '放量下跌':
                volume_score = -10
                sell_signals.append(f"放量下跌 (量比{volume_surge['volume_ratio']:.1f})")
            elif volume_surge['surge_type'] == '缩量上涨':
                volume_score = 5

            score += max(0, volume_score)
            if volume_surge['surge_type']:
                signals.append(volume_surge['surge_type'])

            details['volume'] = {
                'score': max(0, volume_score),
                'volume_ratio': volume_surge['volume_ratio'],
                'price_change': volume_surge['price_change'],
                'surge_type': volume_surge['surge_type']
            }

            # ====== 6. 资金流向 (15分) ======
            fund_flow = self.cache.get_fund_flow(code)

            fund_score = 0
            fund_signal = None
            main_in_wan = 0

            if fund_flow:
                main_in = fund_flow.get('main_in', 0)
                main_in_wan = main_in / 10000  # 转换为万

                if main_in > 5000000:  # 主力流入>500万
                    fund_score = 15
                    fund_signal = f'主力流入 (+{main_in_wan:.0f}万)'
                    buy_signals.append(fund_signal)
                elif main_in > 0:
                    fund_score = 8
                    fund_signal = f'小幅流入 (+{main_in_wan:.0f}万)'
                elif main_in < -5000000:
                    fund_score = 0
                    fund_signal = f'主力流出 ({main_in_wan:.0f}万)'
                    sell_signals.append(fund_signal)

                if fund_signal and fund_signal not in signals:
                    signals.append(fund_signal.split(' ')[0])  # 只取"主力流入"等

            score += fund_score
            details['fund_flow'] = {
                'score': fund_score,
                'main_in': main_in_wan,
                'signal': fund_signal
            }

            # ====== 7. ATR动态止损止盈 ======
            atr = self.indicators.calc_atr_short(df)
            atr_now = atr.iloc[-1]

            trade_points = self.indicators.calc_trade_points(
                current_price, atr_now,
                stop_multiplier=2.0,
                profit_multiplier=3.0
            )

            details['trade_points'] = trade_points

            # ====== 8. 计算共振信号数 ======
            buy_signal_count = len(buy_signals)
            sell_signal_count = len(sell_signals)

            # ====== 汇总结果 ======
            result = {
                'code': code,
                'name': stock_info.get('name', 'Unknown'),
                'price': current_price,
                'change_pct': float(stock_info.get('change_pct', 0)),
                'score': round(float(score), 2),
                'rating': self._get_rating(score),
                'signals': signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'buy_signal_count': buy_signal_count,
                'sell_signal_count': sell_signal_count,
                'details': self._convert_to_json_safe(details),
                # 买卖点
                'buy_price': trade_points['buy_price'],
                'stop_loss': trade_points['stop_loss'],
                'take_profit': trade_points['take_profit'],
                'stop_loss_pct': trade_points['stop_loss_pct'],
                'take_profit_pct': trade_points['take_profit_pct'],
                'atr': trade_points['atr'],
                'atr_pct': trade_points['atr_pct'],
                'risk_reward_ratio': trade_points['risk_reward_ratio'],
                'recommend': bool(score >= 60 and buy_signal_count >= 2),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            return result

        except Exception as e:
            import traceback
            print(f"分析{code}失败: {e}")
            traceback.print_exc()
            return None
    
    def _get_rating(self, score: float) -> str:
        """
        评级
        A+/A: 强烈推荐 (≥70分)
        B+/B: 可操作 (≥50分)
        C: 观望 (<50分)
        """
        if score >= 85:
            return 'A+'
        elif score >= 70:
            return 'A'
        elif score >= 60:
            return 'B+'
        elif score >= 50:
            return 'B'
        else:
            return 'C'
    
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
    
    def select_top_stocks(self, top_n: int = 5) -> List[Dict]:
        """
        短线选股TOP N
        返回推荐列表
        """
        print("=" * 60)
        print(f"⚡ 短线选股 - TOP {top_n}")
        print("=" * 60)
        print()
        
        watchlist = self.load_watchlist()
        if not watchlist:
            print("❌ 监控列表为空")
            return []
        
        print(f"📊 分析 {len(watchlist)} 只股票 (已排除创业板/科创板)...")
        print()
        
        results = []
        for i, code in enumerate(watchlist, 1):
            print(f"[{i}/{len(watchlist)}] {code}...", end=" ")
            
            result = self.analyze_single_stock(code)
            if result:
                print(f"✅ {result['score']:.1f}分 ({result['rating']})")
                if result['signals']:
                    print(f"    信号: {', '.join(result['signals'][:3])}")
                results.append(result)
            else:
                print("❌ 跳过")
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 取TOP N
        top_stocks = results[:top_n]
        
        print()
        print("=" * 60)
        print(f"⚡ 短线推荐 (TOP {len(top_stocks)})")
        print("=" * 60)
        print()

        for i, stock in enumerate(top_stocks, 1):
            print(f"【{stock['code']} {stock['name']}】评分: {stock['score']:.0f}分 ({stock['rating']})")
            print(f"现价: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)")
            print()

            # 买入信号
            if stock['buy_signals']:
                print("📈 买入信号:")
                for sig in stock['buy_signals'][:4]:
                    print(f"  ✓ {sig}")
                print()

            # 卖出信号（如果有）
            if stock['sell_signals']:
                print("📉 卖出信号:")
                for sig in stock['sell_signals'][:2]:
                    print(f"  ✗ {sig}")
                print()

            # 操作建议
            print("💰 操作建议:")
            print(f"  买点: ¥{stock['buy_price']:.2f} (当前价即可)")
            print(f"  止损: ¥{stock['stop_loss']:.2f} ({stock['stop_loss_pct']:.1f}%, 基于ATR)")
            print(f"  止盈: ¥{stock['take_profit']:.2f} (+{stock['take_profit_pct']:.1f}%, 基于ATR)")
            print(f"  盈亏比: {stock['risk_reward_ratio']:.1f}:1")
            print(f"  预期持仓: 1-3天")
            print()
            print("-" * 60)
            print()

        return top_stocks
    
    def generate_report(self, stocks: List[Dict]) -> str:
        """生成短线推荐报告 (优化版)"""
        report = []
        report.append("=" * 60)
        report.append(f"⚡ 短线选股报告 (优化版)")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"持仓建议: 1-3天")
        report.append(f"评分体系: RSI(20)+KDJ(20)+MACD(15)+布林(15)+量价(15)+资金(15)")
        report.append("=" * 60)
        report.append("")

        for i, stock in enumerate(stocks, 1):
            report.append(f"【{stock['code']} {stock['name']}】评分: {stock['score']:.0f}分 ({stock['rating']})")
            report.append(f"现价: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)")
            report.append("")

            # 买入信号
            if stock.get('buy_signals'):
                report.append("📈 买入信号:")
                for sig in stock['buy_signals'][:5]:
                    report.append(f"   ✓ {sig}")
                report.append("")

            # 卖出信号
            if stock.get('sell_signals'):
                report.append("📉 卖出信号:")
                for sig in stock['sell_signals'][:3]:
                    report.append(f"   ✗ {sig}")
                report.append("")

            # 技术指标详情
            details = stock['details']
            report.append("📊 技术指标:")
            rsi_val = details.get('rsi', {}).get('value', 0)
            report.append(f"   RSI: {rsi_val:.1f}")

            kdj = details.get('kdj', {})
            report.append(f"   KDJ: K={kdj.get('k', 0):.1f}, D={kdj.get('d', 0):.1f}, J={kdj.get('j', 0):.1f}")

            macd = details.get('macd', {})
            if macd:
                report.append(f"   MACD: DIF={macd.get('dif', 0):.4f}, DEA={macd.get('dea', 0):.4f}")

            boll = details.get('bollinger', {})
            if boll:
                report.append(f"   布林: 位置{boll.get('position_pct', 50):.0f}%, 带宽{boll.get('bandwidth', 0):.1f}%")

            volume = details.get('volume', {})
            report.append(f"   量比: {volume.get('volume_ratio', 0):.2f}")
            report.append("")

            # 资金流向
            fund = details.get('fund_flow', {})
            if fund.get('signal'):
                report.append("💵 资金面:")
                report.append(f"   {fund.get('signal')}")
                report.append("")

            # 操作建议（核心）
            report.append("💰 操作建议:")
            report.append(f"   买点: ¥{stock.get('buy_price', stock['price']):.2f} (当前价即可)")
            report.append(f"   止损: ¥{stock.get('stop_loss', 0):.2f} ({stock.get('stop_loss_pct', -3):.1f}%, 基于ATR)")
            report.append(f"   止盈: ¥{stock.get('take_profit', 0):.2f} (+{stock.get('take_profit_pct', 5):.1f}%, 基于ATR)")
            report.append(f"   盈亏比: {stock.get('risk_reward_ratio', 1.5):.1f}:1")
            report.append(f"   预期持仓: 1-3天")
            report.append("")

            # 评级建议
            if stock['score'] >= 85:
                report.append("   ★★★ 强烈推荐: 多指标共振，机会较好")
            elif stock['score'] >= 70:
                report.append("   ★★☆ 推荐: 有一定机会，可适量参与")
            elif stock['score'] >= 60:
                report.append("   ★☆☆ 关注: 信号一般，轻仓试探")
            else:
                report.append("   ☆☆☆ 观望: 暂不建议操作")

            report.append("")
            report.append("-" * 60)
            report.append("")

        report.append("⚠️ 风险提示:")
        report.append("   • 短线交易风险较高，建议控制仓位")
        report.append("   • 严格执行动态止损止盈")
        report.append("   • 多指标共振确认，减少假信号")
        report.append("   • 不追涨杀跌，理性交易")
        report.append("")

        return "\n".join(report)
    
    def close(self):
        self.ds.close()
        self.cache.close()


if __name__ == '__main__':
    selector = ShortTermSelector()
    
    # 选择TOP 5
    top_stocks = selector.select_top_stocks(top_n=5)
    
    # 生成报告
    if top_stocks:
        report = selector.generate_report(top_stocks)
        print(report)
        
        # 保存到文件
        with open('short_term_recommendation.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("✅ 报告已保存到 short_term_recommendation.txt")
    
    selector.close()
