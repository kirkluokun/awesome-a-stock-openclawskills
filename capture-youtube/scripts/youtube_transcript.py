#!/usr/bin/env python3
"""
YouTube 逐字稿 — 使用 Gemini 直接从视频生成文字稿。

支持分段转录：对于长视频，按每 N 分钟一段分别调用 Gemini，
最后拼接成完整文字稿。解决单次调用 token 限制导致的截断问题。
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Gemini model used for transcript generation.
GEMINI_MODEL = "gemini-3-pro-preview"
API_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# 单段转录的 prompt（不带时间范围限制的完整版）
PROMPT_FULL = (
    "Create a clean verbatim transcript for the YouTube video at the URL below. "
    "Use the video content directly (do not request captions). "
    "Identify speakers when clearly implied by the text; otherwise use a generic label like 'Speaker'. "
    "Use reasonable paragraph breaks. "
    "NO time codes. "
    "Output ONLY transcript lines in the form: Speaker: text. "
    "No extra info, no headings, no lists."
)

# 分段转录的 prompt 模板
PROMPT_SEGMENT = (
    "Create a clean verbatim transcript for the YouTube video at the URL below. "
    "IMPORTANT: Only transcribe the content from **{start}** to **{end}** of the video. "
    "Ignore all content outside this time range. "
    "Use the video content directly (do not request captions). "
    "Identify speakers when clearly implied by the text; otherwise use a generic label like 'Speaker'. "
    "Use reasonable paragraph breaks. "
    "NO time codes. "
    "Output ONLY transcript lines in the form: Speaker: text. "
    "No extra info, no headings, no lists. "
    "Do NOT include any notes about the time range."
)


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def gemini_generate(api_key: str, parts: list[dict], max_retries: int = 3) -> str:
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.2},
    }

    data = json.dumps(payload).encode("utf-8")

    for attempt in range(max_retries):
        req = urllib.request.Request(
            API_ENDPOINT,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                raw = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as ex:
            body = ex.read().decode("utf-8", errors="replace")
            if ex.code == 429 and attempt < max_retries - 1:
                wait = 30 * (attempt + 1)
                eprint(f"  ⏳ 速率限制，等待 {wait}s 后重试 ({attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            if ex.code >= 500 and attempt < max_retries - 1:
                wait = 15 * (attempt + 1)
                eprint(f"  ⏳ 服务器错误 {ex.code}，等待 {wait}s 后重试...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"Gemini API error: HTTP {ex.code}\n{body}")

    obj = json.loads(raw)
    candidates = obj.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"No candidates in response: {raw[:500]}")

    content = candidates[0].get("content") or {}
    out_parts = content.get("parts") or []
    text_chunks = [p.get("text", "") for p in out_parts if isinstance(p, dict)]
    text = "".join(text_chunks).strip()
    if not text:
        raise RuntimeError(f"Empty response text: {raw[:500]}")
    return text


def fetch_youtube_title_oembed(url: str) -> str | None:
    """Get title without downloading anything."""
    try:
        oembed = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")
        req = urllib.request.Request(oembed, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            title = (data.get("title") or "").strip()
            return title or None
    except Exception:
        return None


def detect_duration_seconds(url: str) -> int | None:
    """尝试通过 yt-dlp 获取视频时长（秒）。"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "duration", "--no-warnings", "--no-download", url],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            val = result.stdout.strip()
            if val.replace(".", "").isdigit():
                return int(float(val))
    except Exception:
        pass

    # 备用方法：从 URL 参数或 oembed 无法获取时长
    return None


def parse_duration_str(s: str) -> int | None:
    """解析 HH:MM:SS 或 MM:SS 格式为秒数。"""
    parts = s.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1 and parts[0].isdigit():
            return int(parts[0])
    except ValueError:
        pass
    return None


def format_time(seconds: int) -> str:
    """秒数转换为 HH:MM:SS 格式。"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def safe_slug(s: str, max_len: int = 60) -> str:
    keep: list[str] = []
    for ch in s:
        if ch.isalnum():
            keep.append(ch.lower())
        elif ch in (" ", "-", "_", "."):
            keep.append("-")
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    if not slug:
        slug = "video"
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return slug


def suggest_filename_stem(api_key: str, title: str) -> str | None:
    prompt = (
        "Suggest a short, filesystem-safe filename stem for a transcript file based on this title. "
        "Rules: output ONLY the filename stem, no extension, no quotes, no extra words. "
        "Use lowercase ASCII with hyphens, max 40 characters.\n\n"
        f"Title: {title}"
    )
    try:
        text = gemini_generate(api_key, [{"text": prompt}])
    except Exception:
        return None

    stem = text.strip().splitlines()[0].strip()
    stem = safe_slug(stem, max_len=40)
    return stem or None


def default_out_dir() -> Path:
    """Default output directory: the workspace 'out/' (outside the skills folder)."""
    here = Path(__file__).resolve()
    for p in here.parents:
        if p.name == "skills":
            return p.parent / "out"
    return Path.cwd() / "out"


def transcribe_single(api_key: str, url: str) -> str:
    """单次调用 Gemini 获取完整文字稿（适用于短视频）。"""
    parts = [
        {"text": PROMPT_FULL},
        {"file_data": {"file_uri": url}},
    ]
    return gemini_generate(api_key, parts)


def transcribe_segmented(api_key: str, url: str, duration_secs: int,
                         segment_minutes: int = 10) -> str:
    """分段调用 Gemini 获取文字稿，每段 N 分钟。"""
    segment_secs = segment_minutes * 60
    num_segments = math.ceil(duration_secs / segment_secs)

    eprint(f"📊 视频时长: {format_time(duration_secs)} | 分 {num_segments} 段转录（每段 {segment_minutes} 分钟）")

    all_transcripts = []

    for i in range(num_segments):
        start_sec = i * segment_secs
        end_sec = min((i + 1) * segment_secs, duration_secs)

        start_str = format_time(start_sec)
        end_str = format_time(end_sec)

        print(f"  📝 [{i+1}/{num_segments}] {start_str} → {end_str} ...", end=" ", file=sys.stderr, flush=True)

        prompt = PROMPT_SEGMENT.format(start=start_str, end=end_str)
        parts = [
            {"text": prompt},
            {"file_data": {"file_uri": url}},
        ]

        try:
            text = gemini_generate(api_key, parts)
            all_transcripts.append(text)
            word_count = len(text.split())
            eprint(f"✅ ({word_count} words)")
        except Exception as e:
            eprint(f"❌ 失败: {e}")
            all_transcripts.append(f"[段落 {i+1} ({start_str}-{end_str}) 转录失败]")

        # 在段落之间短暂等待，避免速率限制
        if i < num_segments - 1:
            time.sleep(3)

    return "\n\n".join(all_transcripts)


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="youtube_transcript",
        description="Verbatim transcript for a YouTube URL using Gemini. "
                    "Supports segmented transcription for long videos.",
    )
    ap.add_argument("url", help="YouTube URL")
    ap.add_argument("--out", help="Write transcript to this file (default: auto-named in workspace out/)")
    ap.add_argument("--duration", help="Video duration in HH:MM:SS or total seconds (auto-detected if omitted)")
    ap.add_argument("--segment-minutes", type=int, default=10,
                    help="Segment length in minutes for long videos (default: 10)")
    ap.add_argument("--no-segment", action="store_true",
                    help="Disable segmented mode, use single call (may truncate long videos)")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        eprint("Missing GEMINI_API_KEY environment variable")
        eprint("Get a key from https://aistudio.google.com/apikey")
        return 2

    url = args.url
    title = fetch_youtube_title_oembed(url)
    eprint(f"🎬 {title or 'Unknown Title'}")

    out_path: Path
    if args.out:
        out_path = Path(args.out)
    else:
        stem: str | None = None
        if title:
            stem = suggest_filename_stem(api_key, title)
        if not stem:
            stem = safe_slug(title or "transcript", max_len=40) or "transcript"
        out_path = default_out_dir() / f"{stem}.txt"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 确定视频时长
    duration_secs: int | None = None
    if args.duration:
        duration_secs = parse_duration_str(args.duration)
        if duration_secs is None:
            eprint(f"⚠️ 无法解析时长 '{args.duration}'，尝试自动检测...")

    if duration_secs is None and not args.no_segment:
        eprint("🔍 检测视频时长...")
        duration_secs = detect_duration_seconds(url)
        if duration_secs:
            eprint(f"  → {format_time(duration_secs)}")
        else:
            eprint("  → 无法自动检测时长，使用单次模式（可能被截断）")
            eprint("  💡 提示：用 --duration HH:MM:SS 手动指定时长可启用分段转录")

    # 决定使用单次还是分段模式
    segment_minutes = args.segment_minutes
    use_segmented = (
        not args.no_segment
        and duration_secs is not None
        and duration_secs > segment_minutes * 60
    )

    if use_segmented:
        transcript = transcribe_segmented(api_key, url, duration_secs, segment_minutes)
    else:
        if duration_secs and duration_secs <= segment_minutes * 60:
            eprint(f"📝 短视频（{format_time(duration_secs)}），单次转录...")
        transcript = transcribe_single(api_key, url)

    header = title or "Transcript"
    out_path.write_text(header + "\n\n" + transcript.strip() + "\n", encoding="utf-8")
    eprint(f"\n✅ 保存至: {out_path}")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
