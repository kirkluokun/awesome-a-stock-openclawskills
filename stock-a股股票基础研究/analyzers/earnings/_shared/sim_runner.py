import os
import subprocess
import sys
from pathlib import Path

from config import DB_PATH


def parse_dates(value: str):
    if not value:
        return []
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]


def run_cmd(cmd):
    subprocess.run(cmd, check=True)


def reset_db(db_path: Path):
    if db_path.exists():
        db_path.unlink()


def build_ingest_cmd(ingest_path: Path, date_str: str, args):
    cmd = [sys.executable, str(ingest_path), "--date", date_str]
    if args.report_rc_file:
        cmd += ["--report-rc-file", args.report_rc_file]
    if args.forecast_file:
        cmd += ["--forecast-file", args.forecast_file]
    if args.express_file:
        cmd += ["--express-file", args.express_file]
    if args.income_file:
        cmd += ["--income-file", args.income_file]
    if args.disclosure_file:
        cmd += ["--disclosure-file", args.disclosure_file]
    if args.only_report_rc:
        cmd.append("--only-report-rc")
    if args.no_vip:
        cmd.append("--no-vip")
    if args.env_path:
        cmd += ["--env-path", args.env_path]
    return cmd


def build_simple_cmd(script_path: Path):
    return [sys.executable, str(script_path)]


def resolve_db_path(root_dir: Path = None):
    """返回数据库路径（使用集中配置）"""
    return DB_PATH


def normalize_path(value: str):
    if not value:
        return value
    return os.path.abspath(value)
