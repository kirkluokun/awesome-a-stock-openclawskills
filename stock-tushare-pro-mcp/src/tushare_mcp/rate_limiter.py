"""
频率限制器

Tushare Pro API 有调用频率限制，这里用简单的时间间隔控制。
默认最小间隔 300ms，避免触发服务端限流。
"""

import time
import threading


class RateLimiter:
    """
    线程安全的频率限制器

    Args:
        min_interval: 两次调用之间的最小间隔（秒）
    """

    def __init__(self, min_interval: float = 0.3) -> None:
        self._min_interval = min_interval
        self._last_call: float = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        """等待直到可以发起下一次调用"""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()
