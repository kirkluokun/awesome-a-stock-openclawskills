"""批量拉取股票技术面因子数据（按交易日逐天）

策略：
- stk_factor_pro 无 VIP 接口，按 trade_date 逐天拉取
- 每天 ~5500 条，低于单次 10000 上限
- 8000 积分：500 次/分钟，默认 0.2s 间隔
- 通过交易日历过滤非交易日，避免无效请求
- 支持断点续拉
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env
load_env_auto(PROJECT_ROOT)

from fetchers.finance_basic import pro
from fetchers.stk_factor_pro import fetch_and_save

DATA_DIR = PROJECT_ROOT / "data"
PROGRESS_FILE = DATA_DIR / "stk_factor_progress.json"
PROGRESS_LOG = DATA_DIR / "stk_factor_progress.log"
SAVE_EVERY = 50  # 每 50 天保存一次完整进度


def get_trade_dates(start_date: str, end_date: str) -> list[str]:
    """获取区间内的交易日列表"""
    df = pro.trade_cal(
        exchange="SSE",
        start_date=start_date,
        end_date=end_date,
        is_open="1",
    )
    dates = sorted(df["cal_date"].tolist())
    return dates


def load_progress() -> set:
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


def append_progress(trade_date: str):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PROGRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{trade_date}\n")


def save_progress(processed: set):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "processed": sorted(processed),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    PROGRESS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_batch(
    start_date: str,
    end_date: str,
    delay: float = 0.2,
    resume: bool = True,
):
    print(f"获取 {start_date} ~ {end_date} 交易日历...")
    trade_dates = get_trade_dates(start_date, end_date)
    print(f"交易日共 {len(trade_dates)} 天")

    processed = load_progress() if resume else set()
    remaining = [d for d in trade_dates if d not in processed]
    print(f"剩余 {len(remaining)} 天待拉取")

    if not remaining:
        print("全部已完成")
        return

    total_count = 0
    start_time = time.time()

    for idx, td in enumerate(remaining, 1):
        print(f"[{idx}/{len(remaining)}] {td}", end=" ", flush=True)
        try:
            count = fetch_and_save(trade_date=td)
            print(f"✓ {count} 条")
            total_count += count
            processed.add(td)
            append_progress(td)
        except Exception as e:
            print(f"✗ {e}")

        if idx % SAVE_EVERY == 0:
            save_progress(processed)
            elapsed = time.time() - start_time
            rate = idx / elapsed * 60
            print(f"  -- 进度: {idx}/{len(remaining)}, 速率: {rate:.0f} 天/分钟")

        time.sleep(delay)

    save_progress(processed)
    elapsed = time.time() - start_time
    print(f"\n完成! 共 {total_count} 条, 耗时 {elapsed:.0f}s")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="批量拉取股票技术面因子")
    parser.add_argument("--start-date", required=True, help="开始日期 YYYYMMDD")
    parser.add_argument("--end-date", required=True, help="结束日期 YYYYMMDD")
    parser.add_argument("--delay", type=float, default=0.2, help="请求间隔秒数 (默认0.2)")
    parser.add_argument("--no-resume", action="store_true", help="不续拉，从头开始")
    args = parser.parse_args()

    run_batch(
        args.start_date,
        args.end_date,
        args.delay,
        resume=not args.no_resume,
    )
