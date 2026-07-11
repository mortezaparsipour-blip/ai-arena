"""Rate limiter for enforcing delays between API calls."""

from __future__ import annotations

import threading
import time
from typing import Optional


class RateLimiter:
    """Thread-safe rate limiter enforcing a minimum delay between calls.

    Uses a simple token-bucket-like approach with a last-call timestamp.
    """

    def __init__(self, delay_seconds: float = 60.0) -> None:
        """Initialize rate limiter.

        Args:
            delay_seconds: Minimum seconds between allowed calls.
        """
        self.delay_seconds = delay_seconds
        self._last_call: float = 0.0
        self._lock = threading.Lock()

    def wait(self) -> float:
        """Block until the rate limit allows a call.

        Returns:
            The actual delay waited in seconds.
        """
        with self._lock:
            now = time.time()
            elapsed = now - self._last_call
            if elapsed < self.delay_seconds:
                wait_time = self.delay_seconds - elapsed
                time.sleep(wait_time)
                self._last_call = time.time()
                return wait_time
            self._last_call = now
            return 0.0

    def reset(self) -> None:
        """Reset the rate limiter, allowing an immediate call."""
        with self._lock:
            self._last_call = 0.0
