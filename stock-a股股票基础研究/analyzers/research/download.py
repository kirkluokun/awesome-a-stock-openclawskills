# analyzers/research/download.py
"""下载研报 PDF"""

import re
import time
from pathlib import Path

import requests

from ._shared.db import connect, update_local_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output" / "reports"


def sanitize_filename(name: str) -> str:
    """清理文件名"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)[:100]


def download_report(report_id: int, force: bool = False) -> str | None:
    """
    下载单个研报 PDF
    
    Args:
        report_id: 研报 ID
        force: 强制重新下载
    
    Returns:
        本地文件路径，失败返回 None
    """
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT id, ts_code, title, url, local_path FROM research_report WHERE id = ?",
            (report_id,)
        )
        row = cur.fetchone()
    finally:
        conn.close()
    
    if not row:
        print(f"研报 {report_id} 不存在")
        return None
    
    row = dict(row)
    
    # 已下载且不强制重下
    if row["local_path"] and Path(row["local_path"]).exists() and not force:
        return row["local_path"]
    
    # 按股票代码分目录
    ts_code = row["ts_code"] or "unknown"
    subdir = OUTPUT_DIR / ts_code.replace(".", "_")
    subdir.mkdir(parents=True, exist_ok=True)
    
    # 文件名
    filename = sanitize_filename(row["title"]) + ".pdf"
    local_path = subdir / filename
    
    # 下载
    try:
        resp = requests.get(row["url"], timeout=30)
        resp.raise_for_status()
        local_path.write_bytes(resp.content)
        
        # 更新 DB
        update_local_path(report_id, str(local_path))
        print(f"已下载: {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"下载失败 [{report_id}]: {e}")
        return None


def download_batch(report_ids: list[int], delay: float = 1.0) -> list[str]:
    """
    批量下载
    
    Args:
        report_ids: 研报 ID 列表
        delay: 下载间隔（秒）
    
    Returns:
        成功下载的本地路径列表
    """
    paths = []
    for i, rid in enumerate(report_ids):
        path = download_report(rid)
        if path:
            paths.append(path)
        if i < len(report_ids) - 1:
            time.sleep(delay)
    return paths


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="下载研报 PDF")
    parser.add_argument("ids", nargs="+", type=int, help="研报 ID")
    parser.add_argument("--force", action="store_true", help="强制重新下载")
    args = parser.parse_args()
    
    for rid in args.ids:
        download_report(rid, force=args.force)
