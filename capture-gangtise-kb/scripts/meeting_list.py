#!/usr/bin/env python3
"""
查询电话会议列表。

用法:
  python3 scripts/meeting_list.py
  python3 scripts/meeting_list.py --stock 600519.SH
  python3 scripts/meeting_list.py --topic 银行 --size 20
  python3 scripts/meeting_list.py --json
"""
import json
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _client import require_configured, post

MEETING_ENDPOINT = "/application/open-meeting/cnfr/getList"

# 会议进程映射
PROCESS_MAP = {1: '会议中', 2: '未开始', 3: '录制成功', 4: '录制失败', 7: '上传完成'}
# 会议类型映射
METHOD_MAP = {1: '电话会议', 2: '上传会议', 3: '腾讯会议', 4: '进门财经', 5: 'Zoom'}


def query_meetings(page_num: int = 1, page_size: int = 10, stock_codes: list | None = None,
                   topic: list | None = None, days_back: int = 7) -> dict | None:
    """查询会议列表。"""
    end_time = int(time.time() * 1000)
    start_time = end_time - (days_back * 24 * 60 * 60 * 1000)

    data = {
        "pageNum": page_num,
        "pageSize": page_size,
        "startTime": start_time,
        "endTime": end_time,
        "status": 17,  # 已发布
    }
    if stock_codes:
        data["securityIdList"] = stock_codes
    if topic:
        data["topicList"] = topic

    return post(MEETING_ENDPOINT, data)


def format_results(result: dict) -> None:
    """格式化输出会议列表。"""
    if not result or result.get('code') != '000000':
        print(f"查询失败: {result.get('msg', '未知错误') if result else '无响应'}")
        return

    page_data = result.get('data', {})
    total = page_data.get('total', 0)
    items = page_data.get('list', [])

    print(f"共 {total} 条会议，当前页 {len(items)} 条")

    for item in items:
        cnfr_time = item.get('cnfrTime')
        time_str = datetime.fromtimestamp(cnfr_time / 1000).strftime('%m-%d %H:%M') if cnfr_time else 'N/A'
        process = PROCESS_MAP.get(item.get('process'), str(item.get('process', '')))
        method = METHOD_MAP.get(item.get('cnfrCreateMethod'), str(item.get('cnfrCreateMethod', '')))

        print(f"\n--- [{time_str}] {item.get('topic', 'N/A')} ---")
        print(f"  机构: {item.get('partyName', 'N/A')} | 行业: {item.get('blockName', 'N/A')} | 状态: {process}")
        print(f"  类型: {method} | 类别: {item.get('categoryStmt', 'N/A')}")

        security = item.get('securityAbbr')
        if security:
            print(f"  关联股票: {security} ({item.get('securityId', '')})")

        summary = item.get('summary')
        if summary:
            if len(summary) > 300:
                summary = summary[:300] + "..."
            print(f"  摘要: {summary}")

        live_url = item.get('liveUrl')
        if live_url:
            print(f"  直播: {live_url}")


def main():
    parser = argparse.ArgumentParser(description='查询电话会议列表')
    parser.add_argument('--stock', help='股票代码，如 600519.SH')
    parser.add_argument('--topic', help='会议主题关键词')
    parser.add_argument('--days', type=int, default=7, help='查询天数（默认 7）')
    parser.add_argument('--page', type=int, default=1, help='页码（默认 1）')
    parser.add_argument('--size', type=int, default=10, help='每页数量（默认 10）')
    parser.add_argument('--json', action='store_true', help='输出原始 JSON')

    args = parser.parse_args()
    require_configured()

    stock_codes = [args.stock] if args.stock else None
    topics = [args.topic] if args.topic else None

    result = query_meetings(args.page, args.size, stock_codes, topics, args.days)
    if result:
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            format_results(result)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
