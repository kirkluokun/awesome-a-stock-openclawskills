#!/usr/bin/env python3
"""
解析 summary JSON 并输出：
1. 文字报告（最近3天更新）
2. CSV 存档表格
"""

import argparse
from datetime import datetime
from pathlib import Path

from _shared.renderer import (
    build_csv,
    build_text_report,
    find_latest_summary,
    load_json,
    load_stock_names,
)


def cleanup_old_files(output_dir: Path, pattern: str, keep: int = 5):
    """清理旧文件，只保留最近 N 个"""
    files = sorted(output_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    for old_file in files[keep:]:
        old_file.unlink()


def main():
    parser = argparse.ArgumentParser(description="解释 summary 输出")
    parser.add_argument("--summary-file", help="指定 summary JSON 路径")
    parser.add_argument("--days", type=int, default=3, help="文字报告覆盖天数")
    args = parser.parse_args()

    # 定位 summary 文件
    project_root = Path(__file__).resolve().parents[2]
    if args.summary_file:
        summary_path = Path(args.summary_file).expanduser()
    else:
        scripts_output = project_root / "output"
        summary_path = find_latest_summary(scripts_output)

    if not summary_path or not summary_path.exists():
        raise SystemExit("未找到 summary 文件")

    summary = load_json(summary_path)
    name_map = load_stock_names(project_root / "data/stock_basic_all.csv")

    # 输出目录
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")

    # 1. 生成文字报告
    text_report = build_text_report(summary, name_map=name_map, days=args.days)
    text_path = output_dir / f"report_{today}.txt"
    text_path.write_text(text_report, encoding="utf-8")
    print(f"文字报告: {text_path}")
    print("-" * 50)
    print(text_report)
    print("-" * 50)

    # 2. 生成 CSV 存档
    csv_content = build_csv(summary, name_map=name_map)
    csv_path = output_dir / f"alerts_{today}.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"CSV存档: {csv_path}")

    # 3. 清理旧文件（保留最近5个）
    cleanup_old_files(output_dir, "report_*.txt", keep=5)
    cleanup_old_files(output_dir, "alerts_*.csv", keep=5)


if __name__ == "__main__":
    main()
