# fetchers/balancesheet_batch.py
"""批量拉取所有公司的资产负债表数据"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.balancesheet import fetch_and_save

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STOCK_CODES_FILE = DATA_DIR / "stock_basic_codes.csv"
PROGRESS_FILE = DATA_DIR / "balancesheet_batch_progress.json"
PROGRESS_LOG = DATA_DIR / "balancesheet_batch_progress.log"
PROGRESS_FILE_VIP = DATA_DIR / "balancesheet_vip_progress.json"
PROGRESS_LOG_VIP = DATA_DIR / "balancesheet_vip_progress.log"
SAVE_EVERY = 200
VIP_SAVE_EVERY = 5


def load_progress() -> set:
    """加载已处理的公司列表"""
    processed = set()
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        processed.update(data.get("processed", []))
    if PROGRESS_LOG.exists():
        for line in PROGRESS_LOG.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                processed.add(line)
    return processed


def append_progress(ts_code: str):
    """追加单个进度（避免频繁重写大文件）"""
    with PROGRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts_code}\n")


def save_progress(processed: set):
    """保存进度（周期性写入完整列表）"""
    data = {"processed": list(processed), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def quarter_ends_between(start_date: str, end_date: str) -> list[str]:
    """生成区间内所有季度末（不超过 end_date）"""
    def to_dt(s):
        return datetime.strptime(s, "%Y%m%d")

    def quarter_end(dt):
        if dt.month <= 3:
            return datetime(dt.year, 3, 31)
        if dt.month <= 6:
            return datetime(dt.year, 6, 30)
        if dt.month <= 9:
            return datetime(dt.year, 9, 30)
        return datetime(dt.year, 12, 31)

    start = quarter_end(to_dt(start_date))
    end_dt = to_dt(end_date)
    periods = []
    cur = start
    while cur <= end_dt:
        periods.append(cur.strftime("%Y%m%d"))
        if cur.month == 3:
            cur = datetime(cur.year, 6, 30)
        elif cur.month == 6:
            cur = datetime(cur.year, 9, 30)
        elif cur.month == 9:
            cur = datetime(cur.year, 12, 31)
        else:
            cur = datetime(cur.year + 1, 3, 31)
    return periods


def load_vip_progress() -> set:
    """加载 VIP 进度（按 period）"""
    processed = set()
    if PROGRESS_FILE_VIP.exists():
        data = json.loads(PROGRESS_FILE_VIP.read_text(encoding="utf-8"))
        processed.update(data.get("processed", []))
    if PROGRESS_LOG_VIP.exists():
        for line in PROGRESS_LOG_VIP.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                processed.add(line)
    return processed


def append_vip_progress(period: str):
    with PROGRESS_LOG_VIP.open("a", encoding="utf-8") as f:
        f.write(f"{period}\n")


def save_vip_progress(processed: set):
    data = {"processed": list(processed), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    PROGRESS_FILE_VIP.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def batch_fetch_vip_by_periods(periods: list[str], delay: float = 1.0, resume: bool = True):
    """按 period 批量拉取资产负债表（VIP）"""
    processed = load_vip_progress() if resume else set()
    remaining = [p for p in periods if p not in processed]
    print(f"共 {len(periods)} 个季度，剩余 {len(remaining)} 个待拉取")
    for idx, period in enumerate(remaining, 1):
        print(f"[{idx}/{len(remaining)}] 拉取 {period}")
        try:
            count = fetch_and_save(period=period, report_type="1", use_vip=True)
            print(f"  ✓ 保存 {count} 条")
            processed.add(period)
            append_vip_progress(period)
        except Exception as e:
            print(f"  ✗ 失败：{e}")
        if idx % VIP_SAVE_EVERY == 0:
            save_vip_progress(processed)
        time.sleep(delay)
    save_vip_progress(processed)


def batch_fetch_all_companies(start_date: str = "20240331", end_date: str = "20251231", delay: float = 0.5, resume: bool = True):
    """
    批量拉取所有公司的资产负债表数据
    
    Args:
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        delay: 每个公司之间的延迟（秒）
        resume: 是否从上次中断处继续
    """
    # 读取股票代码列表
    if not STOCK_CODES_FILE.exists():
        print(f"错误: 文件不存在 {STOCK_CODES_FILE}")
        return
    
    df = pd.read_csv(STOCK_CODES_FILE)
    total_companies = len(df)
    
    # 加载已处理的公司
    processed = load_progress() if resume else set()
    processed_in_df = set(df[df["ts_code"].isin(processed)]["ts_code"])
    remaining = df[~df["ts_code"].isin(processed_in_df)].reset_index(drop=True)
    
    if resume and processed_in_df:
        print(f"发现进度文件，已处理 {len(processed_in_df)} 家公司，剩余 {len(remaining)} 家")
    
    print(f"共 {total_companies} 家公司，开始拉取（{start_date} 至 {end_date}）...")
    print("=" * 60)
    
    total_records = 0
    success_count = 0
    fail_count = 0
    
    remaining_list = remaining.to_dict('records')
    for local_idx, row in enumerate(remaining_list):
        ts_code = row["ts_code"]
        name = row["name"]
        current_idx = len(processed_in_df) + local_idx + 1
        
        print(f"\n[{current_idx}/{total_companies}] {name} ({ts_code})")
        
        try:
            count = fetch_and_save(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                report_type="1"
            )
            total_records += count
            success_count += 1
            processed.add(ts_code)
            append_progress(ts_code)
            
            if count > 0:
                print(f"  ✓ 成功：{count} 条记录")
            else:
                print(f"  - 无数据")
        except Exception as e:
            fail_count += 1
            print(f"  ✗ 失败：{e}")
            processed.add(ts_code)
            append_progress(ts_code)
        
        # 每隔一定数量保存一次进度
        if (success_count + fail_count) % SAVE_EVERY == 0:
            save_progress(processed)
        
        # 延迟避免限流
        if current_idx < total_companies:
            time.sleep(delay)
    
    # 最终保存进度
    save_progress(processed)
    
    print("\n" + "=" * 60)
    print(f"拉取完成:")
    print(f"  成功: {success_count} 家公司")
    print(f"  失败: {fail_count} 家公司")
    print(f"  总计: {total_records} 条资产负债表记录")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="批量拉取所有公司的资产负债表数据")
    parser.add_argument("--start-date", default="20240331", help="开始日期 YYYYMMDD，默认20240331")
    parser.add_argument("--end-date", default="20251231", help="结束日期 YYYYMMDD，默认20251231")
    parser.add_argument("--period", help="报告期 YYYYMMDD（VIP模式单季度）")
    parser.add_argument("--vip", action="store_true", help="使用VIP接口按季度全量拉取")
    parser.add_argument("--delay", type=float, default=0.5, help="每个公司之间的延迟（秒），默认0.5")
    parser.add_argument("--limit", type=int, help="限制拉取公司数量（用于测试）")
    parser.add_argument("--no-resume", action="store_true", help="不从进度文件恢复，重新开始")
    args = parser.parse_args()
    
    # VIP 模式：按 period 拉取全量
    if args.vip:
        if args.period:
            periods = [args.period]
        else:
            periods = quarter_ends_between(args.start_date, args.end_date)
        batch_fetch_vip_by_periods(periods, delay=args.delay, resume=not args.no_resume)
        raise SystemExit(0)

    # 如果有限制，只处理前N个
    if args.limit:
        df = pd.read_csv(STOCK_CODES_FILE)
        df = df.head(args.limit)
        temp_file = DATA_DIR / "stock_basic_codes_temp.csv"
        df.to_csv(temp_file, index=False)
        STOCK_CODES_FILE = temp_file
        print(f"测试模式：仅处理前 {args.limit} 家公司")
    
    batch_fetch_all_companies(args.start_date, args.end_date, args.delay, resume=not args.no_resume)
