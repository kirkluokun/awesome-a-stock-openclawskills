# fetchers/_shared/env.py
"""Auto-load .env by searching upward from a start path."""

from pathlib import Path
from dotenv import load_dotenv


def load_env_auto(start: Path | None = None, stop_at: Path | None = None) -> Path | None:
    """Search upward for .env and load it if found.

    Args:
        start: starting directory (or file path); defaults to this file's dir.
        stop_at: optional directory to stop at (inclusive).

    Returns:
        Path to .env if found, else None.
    """
    if start is None:
        start = Path(__file__).resolve().parent
    start = Path(start)
    if start.is_file():
        cur = start.parent
    else:
        cur = start

    stop_at = Path(stop_at) if stop_at else None

    while True:
        env_path = cur / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            return env_path
        if stop_at and cur == stop_at:
            break
        if cur == cur.parent:
            break
        cur = cur.parent

    return None
