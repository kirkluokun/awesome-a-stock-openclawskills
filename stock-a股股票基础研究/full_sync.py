#!/usr/bin/env python3
"""
全量数据刷新：一次性拉取所有数据源，更新数据库，输出时间戳日志
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
REGISTRY_FILE = PROJECT_ROOT / "sync_registry.json"
PYTHON = sys.executable


# ── period 自适应 ──────────────────────────────────────────────

def get_periods(date_str: str) -> list[str]:
    """根据日期自动计算需要拉取的 period（与 ingest.py 规则一致）"""
    dt = datetime.strptime(date_str, "%Y%m%d")
    y, m = dt.year, dt.month
    if 1 <= m <= 4:
        return [f"{y - 1}1231", f"{y}0331"]
    if 5 <= m <= 8:
        return [f"{y}0630"]
    if 9 <= m <= 10:
        return [f"{y}0930"]
    return [f"{y}1231"]


# ── 注册表加载 ────────────────────────────────────────────────

def load_registry(today: str, periods: list[str]) -> list[dict]:
    """从 sync_registry.json 加载步骤，替换变量占位符"""
    if not REGISTRY_FILE.exists():
        raise FileNotFoundError(f"注册表不存在: {REGISTRY_FILE}")

    raw = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    first_period = periods[0]
    last_period = periods[-1]

    # 变量替换映射
    today_dash = f"{today[:4]}-{today[4:6]}-{today[6:8]}"
    variables = {
        "{today}": today,
        "{today_dash}": today_dash,
        "{first_period}": first_period,
        "{last_period}": last_period,
    }

    steps = []
    for entry in raw:
        if not entry.get("enabled", True):
            continue

        # 替换 cmd 中的变量占位符
        cmd_parts = []
        for part in entry["cmd"]:
            for var, val in variables.items():
                part = part.replace(var, val)
            cmd_parts.append(part)

        cmd = [PYTHON] + cmd_parts

        steps.append({"name": entry["name"], "cmd": cmd})

    return steps


# ── 执行与日志 ────────────────────────────────────────────────

def run_step(step: dict, index: int, total: int, log_file) -> dict:
    """执行单个步骤，返回结果"""
    name = step["name"]
    cmd = step["cmd"]
    cmd_str = " ".join(str(c) for c in cmd)

    header = (
        f"{'=' * 50}\n"
        f"[{index}/{total}] {name}\n"
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"命令: {cmd_str}\n"
        f"{'-' * 50}\n"
    )
    print(header, end="")
    log_file.write(header)

    start = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=600,  # 10分钟超时
        )
        elapsed = time.time() - start
        output = result.stdout
        if result.stderr:
            output += result.stderr
        success = result.returncode == 0
        status = "SUCCESS" if success else f"FAILED (exit_code: {result.returncode})"
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        output = "超时（600秒）"
        success = False
        status = "TIMEOUT"
    except Exception as e:
        elapsed = time.time() - start
        output = str(e)
        success = False
        status = f"ERROR: {e}"

    footer = (
        f"{output}\n"
        f"{'-' * 50}\n"
        f"状态: {status}\n"
        f"耗时: {elapsed:.1f}s\n"
        f"{'=' * 50}\n\n"
    )
    print(footer, end="")
    log_file.write(footer)

    return {"name": name, "success": success, "status": status, "elapsed": elapsed}


def write_summary(results: list[dict], start_time: datetime, log_file):
    """写入汇总"""
    end_time = datetime.now()
    total_elapsed = (end_time - start_time).total_seconds()
    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    summary = (
        f"\n{'=' * 50}\n"
        f"全量刷新汇总\n"
        f"{'=' * 50}\n"
        f"开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"总耗时: {total_elapsed:.1f}s\n"
        f"成功: {len(succeeded)}/{len(results)}\n"
    )
    if failed:
        summary += f"失败: {', '.join(r['name'] for r in failed)}\n"
    summary += f"{'=' * 50}\n"

    print(summary)
    log_file.write(summary)


# ── 主入口 ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="全量数据刷新")
    parser.add_argument("--date", help="基准日期 YYYYMMDD，默认今天")
    parser.add_argument("--dry-run", action="store_true", help="只打印步骤，不执行")
    args = parser.parse_args()

    today = args.date or datetime.now().strftime("%Y%m%d")
    periods = get_periods(today)

    print(f"基准日期: {today}")
    print(f"自动 period: {periods}")

    steps = load_registry(today, periods)

    if args.dry_run:
        print(f"\n共 {len(steps)} 个步骤:")
        for i, s in enumerate(steps, 1):
            print(f"  [{i}] {s['name']}")
            print(f"      {' '.join(str(c) for c in s['cmd'])}")
        return

    # 创建日志
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_name = f"full_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = LOGS_DIR / log_name

    start_time = datetime.now()
    results = []

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"全量数据刷新 - {today}\n")
        log_file.write(f"Period: {periods}\n\n")

        for i, step in enumerate(steps, 1):
            result = run_step(step, i, len(steps), log_file)
            results.append(result)

        write_summary(results, start_time, log_file)

    print(f"\n日志: {log_path}")


if __name__ == "__main__":
    main()
