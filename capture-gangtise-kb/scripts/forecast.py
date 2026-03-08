#!/usr/bin/env python3
"""
查询公司盈利预测数据。

用法:
  python3 scripts/forecast.py 600519.SH
  python3 scripts/forecast.py 000858.SZ --json
"""
import json
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _client import require_configured, post

FORECAST_ENDPOINT = "/application/open-data/report/forecast/info"

# 字段中文映射
FIELD_NAMES = {
    'shnp': '归母净利润(百万)', 'shnpGr': '净利润增长率(%)', 'eps': '每股收益',
    'pe': '市盈率', 'bps': '每股净资产', 'pb': '市净率', 'peg': 'PEG',
    'roe': 'ROE(%)', 'ps': '市销率', 'or': '营业收入(百万)', 'rgr': '营收增长率(%)',
    'sgpm': '销售毛利率(%)', 'npmos': '净利率(%)', 'roic': 'ROIC(%)', 'coas': '总资产周转率(%)',
}

# 显示顺序
KEY_FIELDS = ['shnp', 'shnpGr', 'eps', 'pe', 'roe', 'bps', 'pb', 'or', 'rgr', 'sgpm', 'npmos', 'roic']


def query_forecast(stock_code: str) -> dict | None:
    """查询公司盈利预测。"""
    return post(FORECAST_ENDPOINT, {"stockCode": stock_code})


def format_results(result: dict) -> None:
    """格式化输出盈利预测。"""
    if not result or result.get('code') != '000000':
        print(f"查询失败: {result.get('msg', '未知错误') if result else '无响应'}")
        return

    items = result.get('data', [])
    if not items:
        print("无预测数据。")
        return

    items.sort(key=lambda x: x.get('fincForeYear', ''))

    for item in items:
        print(f"\n--- {item.get('fincForeYear', 'N/A')} ---")
        for field in KEY_FIELDS:
            val = item.get(field, '')
            if val:
                print(f"  {FIELD_NAMES.get(field, field)}: {val}")


def main():
    parser = argparse.ArgumentParser(description='查询公司盈利预测')
    parser.add_argument('stock_code', help='股票代码，如 600519.SH')
    parser.add_argument('--json', action='store_true', help='输出原始 JSON')

    args = parser.parse_args()
    require_configured()

    result = query_forecast(args.stock_code)
    if result:
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            format_results(result)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
