#!/usr/bin/env python3
"""
YouTube 视频搜索 — 通过 Serper API 的 /videos 端点搜索视频。

返回结构化 JSON，包含视频标题、YouTube 链接、频道、时长等信息。
设计用于与 get_transcript.py / youtube_transcript.py 串联使用，
实现"检索 → 文字稿 → 摘要" 闭环。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# =============================================================================
# .env 加载
# =============================================================================
def _load_env_file():
    """从技能目录或公共路径加载 .env 文件。"""
    skill_dir = Path(__file__).parent.parent
    env_paths = [
        skill_dir / ".env",           # 本技能文件夹
        skill_dir.parent / ".env",    # 上一级目录（多技能共享）
    ]
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        if line.startswith("export "):
                            line = line[7:]
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and key not in os.environ:
                            os.environ[key] = value

_load_env_file()


# =============================================================================
# 配置
# =============================================================================
SERP_VIDEOS_URL = "https://google.serper.dev/videos"
USER_AGENT = "Mozilla/5.0 (compatible; CaptureYouTube/1.0)"


def get_api_key() -> str:
    key = os.environ.get("SERPER_API_KEY") or os.environ.get("SERP_API_KEY")
    if not key:
        print(json.dumps({
            "error": "缺少 Serper API Key",
            "how_to_fix": [
                "1. 在 https://serper.dev 免费获取 key（2,500 次免费查询）",
                "2. 添加 SERPER_API_KEY=\"your-key\" 到技能目录的 .env 文件",
            ],
        }, ensure_ascii=False, indent=2), flush=True)
        sys.exit(1)
    return key


# =============================================================================
# Serper 视频 API
# =============================================================================
def _serper_post(endpoint: str, api_key: str, payload: dict) -> dict:
    """POST 请求 Serper API。"""
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(endpoint, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        msgs = {
            401: "API Key 无效或已过期。",
            429: "请求频率超限，请稍后重试。",
        }
        raise Exception(msgs.get(e.code, f"Serper HTTP {e.code}: {body[:300]}"))
    except URLError as e:
        raise Exception(f"网络错误: {e.reason}")


def search_videos(query: str, api_key: str, num: int = 10,
                  gl: Optional[str] = None, hl: str = "en") -> List[Dict[str, Any]]:
    """通过 Serper /videos 端点搜索视频。"""
    payload: Dict[str, Any] = {"q": query, "num": num, "hl": hl}
    if gl and gl != "world":
        payload["gl"] = gl

    data = _serper_post(SERP_VIDEOS_URL, api_key, payload)
    results = []
    for item in data.get("videos", [])[:num]:
        r: Dict[str, Any] = {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "source": "video",
        }
        if item.get("duration"):
            r["duration"] = item["duration"]
        if item.get("channel"):
            r["channel"] = item["channel"]
        if item.get("date"):
            r["date"] = item["date"]
        if item.get("imageUrl"):
            r["thumbnail"] = item["imageUrl"]
        results.append(r)
    return results


def is_youtube_url(url: str) -> bool:
    """判断 URL 是否为 YouTube 链接。"""
    import re
    return bool(re.match(
        r'(https?://)?(www\.)?(youtube\.com/(watch|shorts|live)|youtu\.be/|m\.youtube\.com/)', url
    ))


# =============================================================================
# 输出
# =============================================================================
def format_results(results: List[Dict[str, Any]], query: str,
                   locale: Dict[str, Optional[str]]) -> str:
    """格式化搜索结果为 JSON 输出。"""
    yt_results = [r for r in results if is_youtube_url(r.get("url", ""))]
    non_yt_results = [r for r in results if not is_youtube_url(r.get("url", ""))]

    output = {
        "query": query,
        "locale": locale,
        "total_results": len(results),
        "youtube_results": len(yt_results),
        "other_results": len(non_yt_results),
        "videos": results,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


# =============================================================================
# CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="YouTube 视频搜索 — 通过 Serper API 搜索视频",
    )
    parser.add_argument("--query", "-q", required=True, help="搜索关键词")
    parser.add_argument("--num", "-n", type=int, default=10,
                        help="返回结果数量（默认 10）")
    parser.add_argument("--gl", default="world",
                        help="国家代码（如 cn, us）。默认: world")
    parser.add_argument("--hl", default="en",
                        help="语言代码（如 zh, en）。默认: en")
    parser.add_argument("--youtube-only", action="store_true",
                        help="仅返回 YouTube 链接的结果")

    args = parser.parse_args()
    api_key = get_api_key()
    locale = {"gl": args.gl, "hl": args.hl}

    try:
        results = search_videos(args.query, api_key, num=args.num,
                                gl=locale["gl"], hl=locale["hl"])
    except Exception as e:
        print(json.dumps({"error": str(e), "query": args.query},
                         ensure_ascii=False, indent=2), flush=True)
        sys.exit(1)

    if args.youtube_only:
        results = [r for r in results if is_youtube_url(r.get("url", ""))]

    if not results:
        print(json.dumps({"error": "未找到视频结果", "query": args.query},
                         ensure_ascii=False), flush=True)
        sys.exit(1)

    print(format_results(results, args.query, locale), flush=True)


if __name__ == "__main__":
    main()
