#!/usr/bin/env python3
"""
知识库语义搜索。

用法:
  python3 scripts/query_kb.py "比亚迪最新消息"
  python3 scripts/query_kb.py "特斯拉" --type 10,40 --top 5 --days 180
  python3 scripts/query_kb.py "宁德时代" --json
"""
import json
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _client import require_configured, post, BASE_URL

KNOWLEDGE_ENDPOINT = "/application/open-data/ai/search/knowledge/batch"

# 资源类型映射
RT_NAMES = {
    10: '券商研报', 20: '内部研报', 40: '分析师观点', 50: '公告',
    60: '会议纪要', 70: '调研纪要', 80: '网络资源', 90: '产业公众号',
}


def query_knowledge(queries, resource_types=None, top=20, days_back=365, knowledge_name='system_knowledge_doc'):
    """查询知识库。"""
    end_time = int(time.time() * 1000)
    start_time = end_time - (days_back * 24 * 60 * 60 * 1000)

    data = {
        "queries": queries if isinstance(queries, list) else [queries],
        "resourceTypes": resource_types or [10, 40],
        "knowledgeNames": [knowledge_name],
        "startTime": start_time,
        "endTime": end_time,
        "top": min(top, 20),
    }
    return post(KNOWLEDGE_ENDPOINT, data, timeout=60)


def format_results(result):
    """格式化输出搜索结果。"""
    if not result or result.get('code') != '000000':
        print(f"查询失败: {result.get('msg', '未知错误') if result else '无响应'}")
        return

    data = result.get('data', [])
    if not data:
        print("无结果。")
        return

    for query_result in data:
        query = query_result.get('query', '')
        items = query_result.get('data', [])

        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")

        if not items:
            print("  无匹配结果。")
            continue

        for i, item in enumerate(items, 1):
            rt = item.get('resourceType')
            print(f"\n--- 结果 {i} ---")
            print(f"标题: {item.get('title', 'N/A')}")
            print(f"公司: {item.get('company', 'N/A')}")
            print(f"类型: {RT_NAMES.get(rt, 'Other')} ({rt})")

            ts = item.get('time')
            if ts:
                print(f"时间: {datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')}")

            # 溯源信息（type 40 不支持下载）
            source_id = item.get('sourceId')
            if source_id:
                print(f"SourceId: {source_id}")
                if rt and rt != 40:
                    print(f"下载: {BASE_URL}/application/open-data/ai/resource/download?resourceType={rt}&sourceId={source_id}")

            content = item.get('content', '')
            if content:
                if len(content) > 800:
                    content = content[:800] + "..."
                print(f"内容: {content}")


def main():
    parser = argparse.ArgumentParser(description='知识库语义搜索')
    parser.add_argument('query', help='查询关键词')
    parser.add_argument('--type', default='10,40', help='资源类型（逗号分隔，默认 10,40）')
    parser.add_argument('--top', type=int, default=20, help='返回数量（默认 20，最大 20）')
    parser.add_argument('--days', type=int, default=365, help='搜索天数（默认 365）')
    parser.add_argument('--json', action='store_true', help='输出原始 JSON')

    args = parser.parse_args()
    require_configured()

    resource_types = [int(t.strip()) for t in args.type.split(',')]
    result = query_knowledge(args.query, resource_types, args.top, args.days)

    if result:
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            format_results(result)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
