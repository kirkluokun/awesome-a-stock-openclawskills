#!/usr/bin/env python3
"""
经济数据指标查询 Agent。

用法:
  python3 scripts/indicator.py "比亚迪仰望销量"
  python3 scripts/indicator.py "2024年GDP增速" --stream
  python3 scripts/indicator.py "光伏行业产能" --json
"""
import json
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _client import require_configured, post, post_stream

INDICATOR_ENDPOINT = "/application/open-ai/ai/search/indicator"


def query_indicator(text: str, stream: bool = False) -> dict | str | None:
    """
    查询经济数据指标。
    stream=False 返回完整 dict；stream=True 逐行打印并返回拼接后的内容。
    """
    if not stream:
        return post(INDICATOR_ENDPOINT, {"text": text, "stream": False}, timeout=60)

    # 流式模式
    response = post_stream(INDICATOR_ENDPOINT, {"text": text, "stream": True})
    if not response:
        return None

    try:
        content_parts = []
        for raw_line in response:
            line = raw_line.decode('utf-8').strip()
            if not line.startswith('data:'):
                continue
            payload = line[5:].strip()
            if payload == '[DONE]':
                break
            try:
                chunk = json.loads(payload)
                delta = chunk.get('choices', [{}])[0].get('delta', {})
                c = delta.get('content', '')
                if c:
                    content_parts.append(c)
                    print(c, end='', flush=True)
            except json.JSONDecodeError:
                continue
        print()  # 换行
        return ''.join(content_parts)
    finally:
        response.close()


def format_result(result: dict) -> None:
    """格式化非流式结果。"""
    if not result or result.get('code') != '000000':
        print(f"查询失败: {result.get('msg', '未知错误') if result else '无响应'}")
        return

    choices = result.get('data', {}).get('choices', [])
    if not choices:
        print("无结果。")
        return

    msg = choices[0].get('message', {})
    content = msg.get('content', '')
    reasoning = msg.get('reasoning_content', '')

    if reasoning and reasoning != content:
        print(f"[推理过程]\n{reasoning}\n")
    if content:
        print(content)


def main():
    parser = argparse.ArgumentParser(description='经济数据指标查询')
    parser.add_argument('text', help='查询内容，如 "比亚迪仰望销量"')
    parser.add_argument('--stream', action='store_true', help='流式输出')
    parser.add_argument('--json', action='store_true', help='输出原始 JSON（仅非流式）')

    args = parser.parse_args()
    require_configured()

    if args.stream:
        result = query_indicator(args.text, stream=True)
        if result is None:
            sys.exit(1)
    else:
        result = query_indicator(args.text, stream=False)
        if result:
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                format_result(result)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
