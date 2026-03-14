#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新全市场A股数据到缓存数据库
用于市场情绪计算
"""

import akshare as ak
from stock_cache_db import StockCache
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


def update_all_market_data():
    """更新全市场A股数据"""
    print(f"\n{'='*60}")
    print(f"📊 开始更新全市场A股数据")
    print(f"{'='*60}\n")
    
    try:
        # 获取实时行情数据
        print("🔄 正在获取全市场实时行情...")
        df = ak.stock_zh_a_spot_em()
        
        print(f"✅ 获取到 {len(df)} 只股票数据\n")
        
        # 写入缓存数据库
        cache = StockCache()
        success_count = 0
        
        for idx, row in df.iterrows():
            try:
                code = str(row['代码'])
                
                # 构造股票数据
                stock_data = {
                    'code': code,
                    'name': row['名称'],
                    'price': float(row['最新价']) if row['最新价'] else None,
                    'change_pct': float(row['涨跌幅']) if row['涨跌幅'] else None,
                    'volume': float(row['成交量']) if row['成交量'] else None,
                    'amount': float(row['成交额']) if row['成交额'] else None,
                    'turnover': float(row.get('换手率', 0)) if row.get('换手率') else None,
                    'amplitude': float(row.get('振幅', 0)) if row.get('振幅') else None,
                }
                
                # 保存到缓存
                cache.save_stock(code, stock_data)
                success_count += 1
                
                if (idx + 1) % 500 == 0:
                    print(f"   处理进度: {idx+1}/{len(df)} ({success_count} 成功)")
                    
            except Exception as e:
                continue
        
        cache.close()
        
        print(f"\n{'='*60}")
        print(f"✅ 数据更新完成!")
        print(f"   总数: {len(df)} 只")
        print(f"   成功: {success_count} 只")
        print(f"   失败: {len(df) - success_count} 只")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        return success_count
        
    except Exception as e:
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == '__main__':
    update_all_market_data()
