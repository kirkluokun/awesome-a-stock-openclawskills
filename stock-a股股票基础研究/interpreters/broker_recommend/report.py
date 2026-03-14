# interpreters/broker_recommend/report.py
"""券商金股报告生成"""

import csv
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.broker_recommend.stats import get_monthly_stats

OUTPUT_DIR = PROJECT_ROOT / "output"


def generate_report(month: str, output_format: str = "csv") -> str:
    """
    生成报告
    
    Args:
        month: 月度 YYYYMM
        output_format: 输出格式，目前仅支持 csv
    
    Returns:
        文件路径
    """
    stats = get_monthly_stats(month)
    
    if output_format == "csv":
        filename = f"broker_recommend_{month}.csv"
        filepath = OUTPUT_DIR / filename
        
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["排名", "股票代码", "股票名称", "推荐次数", "推荐券商"])
            
            for i, item in enumerate(stats["by_company"], 1):
                brokers_str = "|".join(item["brokers"])
                writer.writerow([
                    i,
                    item["ts_code"],
                    item["name"],
                    item["count"],
                    brokers_str
                ])
        
        print(f"报告已生成: {filepath}")
        return str(filepath)
    
    else:
        raise ValueError(f"不支持的格式: {output_format}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成券商金股报告")
    parser.add_argument("--month", help="月度 YYYYMM，默认当前月份")
    parser.add_argument("--format", default="csv", help="输出格式，默认 csv")
    args = parser.parse_args()
    
    month = args.month or datetime.now().strftime("%Y%m")
    generate_report(month, args.format)
