"""Shared async token bucket rate limiter for upstream REST calls."""

from __future__ import annotations

import asyncio
import time


class TokenBucket:
    """Async token bucket.

    Allows ``rate`` tokens per ``window`` seconds. The first ``rate`` acquires
    are immediate (burst); afterwards callers are paced so the average rate
    never exceeds the configured limit. The bucket may go negative internally,
    which serialises waiters so they are served in arrival order.
    """

    def __init__(self, rate: int = 8, window: float = 2.0) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self.rate = rate
        self.window = window
        self._capacity = float(rate)
        self._tokens = float(rate)
        self._refill_per_sec = rate / window
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until one token is available, then consume it."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_per_sec)
            self._last = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return

            deficit = 1.0 - self._tokens
            wait = deficit / self._refill_per_sec
            # Reserve the token (bucket goes negative) so concurrent waiters
            # queue behind us instead of all waking at the same instant.
            self._tokens -= 1.0
            await asyncio.sleep(wait)
