#!/usr/bin/env python3
"""
YouTube 频道追踪器 — 追踪指定 YouTube 频道/博主的最新视频。

功能：
  - 添加/删除追踪频道
  - 检查频道最新视频更新
  - 检查所有追踪频道的更新
  - 列出所有追踪的频道

频道列表保存在 JSON 文件中持久化。
利用 yt-dlp 获取频道最新视频列表，无需额外 API。
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# 数据目录
# =============================================================================
def _data_dir() -> Path:
    """追踪数据存储目录。"""
    here = Path(__file__).resolve()
    data = here.parent.parent / "data"
    data.mkdir(parents=True, exist_ok=True)
    return data


def _tracker_file() -> Path:
    return _data_dir() / "tracked_channels.json"


def _history_file() -> Path:
    return _data_dir() / "check_history.json"


# =============================================================================
# 频道数据管理
# =============================================================================
def load_channels() -> Dict[str, Any]:
    """加载追踪频道列表。"""
    f = _tracker_file()
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"channels": [], "updated_at": None}


def save_channels(data: Dict[str, Any]):
    """保存追踪频道列表。"""
    data["updated_at"] = datetime.now().isoformat()
    _tracker_file().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_history() -> Dict[str, Any]:
    """加载检查历史。"""
    f = _history_file()
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"checks": {}}


def save_history(data: Dict[str, Any]):
    _history_file().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# =============================================================================
# yt-dlp 频道视频获取
# =============================================================================
def normalize_channel_url(url_or_handle: str) -> str:
    """标准化频道 URL。支持 @handle、频道 URL 和频道 ID。"""
    url_or_handle = url_or_handle.strip()
    # @handle 格式
    if url_or_handle.startswith("@"):
        return f"https://www.youtube.com/{url_or_handle}"
    # 已经是完整 URL
    if url_or_handle.startswith("http"):
        return url_or_handle
    # 频道 ID（UC 开头）
    if url_or_handle.startswith("UC"):
        return f"https://www.youtube.com/channel/{url_or_handle}"
    # 尝试当成 handle
    return f"https://www.youtube.com/@{url_or_handle}"


def fetch_channel_info(channel_url: str) -> Optional[Dict[str, Any]]:
    """使用 yt-dlp 获取频道基本信息（不下载视频）。"""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--playlist-items", "1",
        "--flat-playlist",
        channel_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        # yt-dlp --flat-playlist 输出每行是一个 JSON
        lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
        if not lines:
            return None
        first = json.loads(lines[0])
        return {
            "channel": first.get("channel") or first.get("uploader") or "未知频道",
            "channel_id": first.get("channel_id") or first.get("uploader_id") or "",
            "channel_url": first.get("channel_url") or first.get("uploader_url") or channel_url,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def fetch_latest_videos(channel_url: str, count: int = 5) -> List[Dict[str, Any]]:
    """使用 yt-dlp 获取频道最新的 N 个视频。"""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--playlist-items", f"1:{count}",
        "--flat-playlist",
        "--no-warnings",
        channel_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return []
        videos = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                video = {
                    "title": item.get("title", "未知标题"),
                    "url": item.get("url") or item.get("webpage_url") or "",
                    "duration": item.get("duration"),
                    "upload_date": item.get("upload_date", ""),
                }
                # 标准化 URL
                vid_id = item.get("id") or item.get("url", "")
                if vid_id and not video["url"].startswith("http"):
                    video["url"] = f"https://www.youtube.com/watch?v={vid_id}"
                if item.get("view_count"):
                    video["views"] = item["view_count"]
                if item.get("description"):
                    video["description"] = item["description"][:200]
                videos.append(video)
            except json.JSONDecodeError:
                continue
        return videos
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


# =============================================================================
# 命令实现
# =============================================================================
def cmd_add(args):
    """添加频道到追踪列表。"""
    channel_url = normalize_channel_url(args.channel)
    data = load_channels()

    # 检查重复
    for ch in data["channels"]:
        if ch["url"] == channel_url or ch.get("alias") == args.alias:
            print(json.dumps({
                "status": "already_tracked",
                "message": f"频道已在追踪列表中: {ch.get('name', channel_url)}",
                "channel": ch,
            }, ensure_ascii=False, indent=2))
            return

    # 尝试获取频道信息
    info = fetch_channel_info(channel_url)
    channel_entry = {
        "url": channel_url,
        "name": info["channel"] if info else (args.alias or channel_url),
        "added_at": datetime.now().isoformat(),
        "last_checked": None,
    }
    if args.alias:
        channel_entry["alias"] = args.alias
    if info:
        channel_entry["channel_id"] = info.get("channel_id", "")

    data["channels"].append(channel_entry)
    save_channels(data)

    print(json.dumps({
        "status": "added",
        "message": f"已添加频道: {channel_entry['name']}",
        "channel": channel_entry,
    }, ensure_ascii=False, indent=2))


def cmd_remove(args):
    """从追踪列表中移除频道。"""
    data = load_channels()
    target = args.channel.strip()
    found = None

    for i, ch in enumerate(data["channels"]):
        if (target == ch["url"] or target == ch.get("name", "")
                or target == ch.get("alias", "") or target == ch.get("channel_id", "")):
            found = data["channels"].pop(i)
            break

    if found:
        save_channels(data)
        print(json.dumps({
            "status": "removed",
            "message": f"已移除频道: {found.get('name', target)}",
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            "status": "not_found",
            "message": f"未找到频道: {target}",
        }, ensure_ascii=False, indent=2))


def cmd_list(args):
    """列出所有追踪的频道。"""
    data = load_channels()
    if not data["channels"]:
        print(json.dumps({
            "status": "empty",
            "message": "追踪列表为空，使用 add 命令添加频道",
        }, ensure_ascii=False, indent=2))
        return

    output = {
        "status": "ok",
        "total": len(data["channels"]),
        "channels": data["channels"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_check(args):
    """检查频道更新。"""
    data = load_channels()
    history = load_history()
    count = args.count or 5

    if args.channel:
        # 检查指定频道
        target = args.channel.strip()
        channel_url = None
        channel_name = target

        # 先在追踪列表中查找
        for ch in data["channels"]:
            if (target == ch["url"] or target == ch.get("name", "")
                    or target == ch.get("alias", "") or target == ch.get("channel_id", "")):
                channel_url = ch["url"]
                channel_name = ch.get("name", target)
                break

        # 如果不在列表中，直接使用输入 URL
        if not channel_url:
            channel_url = normalize_channel_url(target)

        videos = fetch_latest_videos(channel_url, count=count)
        if not videos:
            print(json.dumps({
                "status": "error",
                "message": f"无法获取频道视频: {channel_name}",
                "channel_url": channel_url,
            }, ensure_ascii=False, indent=2))
            return

        # 检查新视频
        prev_ids = set(history.get("checks", {}).get(channel_url, {}).get("video_ids", []))
        new_videos = []
        all_ids = []
        for v in videos:
            vid_match = re.search(r'[?&]v=([^&]+)', v.get("url", ""))
            vid_id = vid_match.group(1) if vid_match else v.get("url", "")
            all_ids.append(vid_id)
            if vid_id not in prev_ids:
                new_videos.append(v)

        # 更新历史
        history.setdefault("checks", {})[channel_url] = {
            "video_ids": all_ids,
            "checked_at": datetime.now().isoformat(),
            "channel_name": channel_name,
        }
        save_history(history)

        # 更新追踪列表的 last_checked
        for ch in data["channels"]:
            if ch["url"] == channel_url:
                ch["last_checked"] = datetime.now().isoformat()
        save_channels(data)

        output: Dict[str, Any] = {
            "status": "ok",
            "channel": channel_name,
            "channel_url": channel_url,
            "total_fetched": len(videos),
            "new_videos": len(new_videos) if prev_ids else "首次检查",
            "videos": videos,
        }
        if prev_ids and new_videos:
            output["new_video_list"] = new_videos

        print(json.dumps(output, ensure_ascii=False, indent=2))

    else:
        # 检查所有追踪频道
        if not data["channels"]:
            print(json.dumps({
                "status": "empty",
                "message": "追踪列表为空",
            }, ensure_ascii=False, indent=2))
            return

        all_updates = []
        for ch in data["channels"]:
            channel_url = ch["url"]
            channel_name = ch.get("name", channel_url)

            videos = fetch_latest_videos(channel_url, count=count)
            if not videos:
                all_updates.append({
                    "channel": channel_name,
                    "status": "fetch_failed",
                })
                continue

            prev_ids = set(
                history.get("checks", {}).get(channel_url, {}).get("video_ids", [])
            )
            new_videos = []
            all_ids = []
            for v in videos:
                vid_match = re.search(r'[?&]v=([^&]+)', v.get("url", ""))
                vid_id = vid_match.group(1) if vid_match else v.get("url", "")
                all_ids.append(vid_id)
                if vid_id not in prev_ids:
                    new_videos.append(v)

            history.setdefault("checks", {})[channel_url] = {
                "video_ids": all_ids,
                "checked_at": datetime.now().isoformat(),
                "channel_name": channel_name,
            }

            ch["last_checked"] = datetime.now().isoformat()

            update_entry: Dict[str, Any] = {
                "channel": channel_name,
                "channel_url": channel_url,
                "status": "ok",
                "total_fetched": len(videos),
                "new_count": len(new_videos) if prev_ids else "首次检查",
            }
            if prev_ids and new_videos:
                update_entry["new_videos"] = new_videos
            elif prev_ids and not new_videos:
                update_entry["message"] = "暂无新视频"
            else:
                update_entry["latest_videos"] = videos[:3]

            all_updates.append(update_entry)

        save_history(history)
        save_channels(data)

        # 统计
        has_new = [u for u in all_updates if isinstance(u.get("new_count"), int) and u["new_count"] > 0]
        print(json.dumps({
            "status": "ok",
            "total_channels": len(data["channels"]),
            "channels_with_updates": len(has_new),
            "checked_at": datetime.now().isoformat(),
            "results": all_updates,
        }, ensure_ascii=False, indent=2))


# =============================================================================
# CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="YouTube 频道追踪器 — 追踪博主最新视频更新",
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # add
    p_add = sub.add_parser("add", help="添加频道到追踪列表")
    p_add.add_argument("channel", help="频道 URL、@handle 或频道 ID")
    p_add.add_argument("--alias", help="频道别名（便于识别）")

    # remove
    p_rm = sub.add_parser("remove", help="移除追踪频道")
    p_rm.add_argument("channel", help="频道 URL、名称、别名或 ID")

    # list
    sub.add_parser("list", help="列出所有追踪频道")

    # check
    p_check = sub.add_parser("check", help="检查频道更新")
    p_check.add_argument("channel", nargs="?", help="指定频道（省略则检查所有）")
    p_check.add_argument("--count", "-n", type=int, default=5,
                         help="每个频道获取的视频数量（默认 5）")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {"add": cmd_add, "remove": cmd_remove, "list": cmd_list, "check": cmd_check}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
