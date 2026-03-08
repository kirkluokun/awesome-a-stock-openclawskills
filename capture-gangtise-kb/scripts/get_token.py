#!/usr/bin/env python3
"""获取冈特斯 access token（带缓存）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _client import require_configured, get_token

if __name__ == "__main__":
    require_configured()
    token = get_token()
    if token:
        print(token)
    else:
        sys.exit(1)
