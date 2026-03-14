# interpreters/research/extract.py
"""研报内容提取"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.research._shared.db import connect, update_parsed_at
from analyzers.research.download import download_report
from interpreters.research._shared.llm import extract_insights
from interpreters.research._shared.pdf_parser import extract_text

OUTPUT_DIR = PROJECT_ROOT / "output"


def extract_report(report_id: int, force: bool = False) -> dict | None:
    """
    提取单个研报内容
    
    Args:
        report_id: 研报 ID
        force: 强制重新解析
    
    Returns:
        {
            "report_id": 123,
            "title": "...",
            "trade_date": "...",
            "inst_csname": "...",
            "summary": "...",
            "key_points": [...],
            "investment_advice": "...",
            "risk_warning": "...",
            "raw_text": "..."
        }
    """
    conn = connect()
    try:
        cur = conn.execute(
            """SELECT id, trade_date, ts_code, name, title, inst_csname, 
                      local_path, parsed_at
               FROM research_report WHERE id = ?""",
            (report_id,)
        )
        row = cur.fetchone()
    finally:
        conn.close()
    
    if not row:
        print(f"研报 {report_id} 不存在")
        return None
    
    row = dict(row)
    
    # 已解析且不强制重解析
    if row["parsed_at"] and not force:
        print(f"研报 {report_id} 已解析于 {row['parsed_at']}")
        # 从缓存文件读取
        cache_file = OUTPUT_DIR / "research" / f"{report_id}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
    
    # 确保已下载
    local_path = row["local_path"]
    if not local_path or not Path(local_path).exists():
        local_path = download_report(report_id)
        if not local_path:
            return None
    
    # 提取文本
    print(f"提取文本: {local_path}")
    raw_text = extract_text(local_path, max_pages=3)
    
    if not raw_text.strip():
        print(f"研报 {report_id} 无法提取文本")
        return None
    
    # LLM 提取
    print(f"调用 Gemini 分析...")
    insights = extract_insights(raw_text)
    
    # 组装结果
    result = {
        "report_id": report_id,
        "title": row["title"],
        "trade_date": row["trade_date"],
        "ts_code": row["ts_code"],
        "name": row["name"],
        "inst_csname": row["inst_csname"],
        "summary": insights.get("summary", ""),
        "key_points": insights.get("key_points", []),
        "investment_advice": insights.get("investment_advice", ""),
        "risk_warning": insights.get("risk_warning", ""),
        "raw_text": raw_text[:5000],  # 截断保存
    }
    
    # 保存缓存
    cache_dir = OUTPUT_DIR / "research"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{report_id}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 更新解析时间
    update_parsed_at(report_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    print(f"解析完成: {cache_file}")
    return result


def extract_batch(report_ids: list[int]) -> list[dict]:
    """批量提取"""
    results = []
    for rid in report_ids:
        result = extract_report(rid)
        if result:
            results.append(result)
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="提取研报内容")
    parser.add_argument("ids", nargs="+", type=int, help="研报 ID")
    parser.add_argument("--force", action="store_true", help="强制重新解析")
    args = parser.parse_args()
    
    for rid in args.ids:
        result = extract_report(rid, force=args.force)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
