"""Rate limiter for enforcing delays between API calls."""

from __future__ import annotations

import threading
import time

from ..config import config


class RateLimiter:
    """Thread-safe rate limiter enforcing a minimum delay between calls.

    Uses a last-call timestamp. The slot is reserved *before* sleeping, so
    two concurrent waiters queue behind each other instead of both passing
    through the same window together.
    """

    def __init__(self, delay_seconds: float | None = None) -> None:
        """Initialize rate limiter.

        Args:
            delay_seconds: Minimum seconds between allowed calls. Defaults
                to ``config.default_rate_limit`` when None.
        """
        self.delay_seconds = float(
            config.default_rate_limit if delay_seconds is None else delay_seconds
        )
        self._last_call: float = 0.0
        self._lock = threading.Lock()

    def wait(self) -> float:
        """Block until the rate limit allows a call.

        Returns:
            The delay waited in seconds (0.0 if none was needed).
        """
        with self._lock:
            now = time.time()
            wait_time = max(0.0, self.delay_seconds - (now - self._last_call))
            # Reserve the slot before sleeping: concurrent waiters see the
            # pushed-forward timestamp and queue behind this caller instead
            # of passing through the same window together.
            self._last_call = now + wait_time

        if wait_time > 0:
            # Sleep outside the lock so other callers can at least reserve
            # their own (later) slot while we wait.
            time.sleep(wait_time)
        return wait_time

    def reset(self) -> None:
        """Reset the rate limiter, allowing an immediate call."""
        with self._lock:
            self._last_call = 0.0
