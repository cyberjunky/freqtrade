"""TTL cache with single-flight coalescing, plus a WS-fed candle book."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

_BAR_UNITS = {
    "m": 60,
    "H": 3600,
    "D": 86400,
    "W": 604800,
    "M": 30 * 86400,  # BloFin '1M' calendar month, approximated for TTL math
}


def bar_to_seconds(bar: str) -> int:
    """Convert a BloFin bar value (``1m``, ``5m``, ``1H``, ``4H``, ``1D`` ...) to seconds."""
    if len(bar) < 2:
        raise ValueError(f"invalid bar: {bar!r}")
    unit = bar[-1]
    if unit not in _BAR_UNITS:
        raise ValueError(f"unknown bar unit: {bar!r}")
    amount = int(bar[:-1])
    if amount <= 0:
        raise ValueError(f"invalid bar amount: {bar!r}")
    return amount * _BAR_UNITS[unit]


def _num(value: float) -> str:
    """Format a float the way BloFin REST renders numeric strings."""
    return f"{value:.12g}"


class TTLCache:
    """Key -> (value, expiry) cache with single-flight ``get_or_fetch``.

    Concurrent misses for the same key await one shared fetch instead of each
    hitting upstream. Failed fetches are not cached.
    """

    def __init__(self) -> None:
        self._values: dict[str, tuple[Any, float]] = {}
        self._inflight: dict[str, asyncio.Task[Any]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        """Return the cached value if present and fresh, else ``None``."""
        entry = self._values.get(key)
        if entry is not None and entry[1] > time.monotonic():
            return entry[0]
        return None

    def put(self, key: str, value: Any, ttl: float) -> None:
        self._values[key] = (value, time.monotonic() + ttl)

    async def get_or_fetch(
        self, key: str, ttl: float, fetch: Callable[[], Awaitable[Any]]
    ) -> Any:
        """Return the cached value, or coalesce concurrent misses into one fetch."""
        entry = self._values.get(key)
        if entry is not None and entry[1] > time.monotonic():
            self.hits += 1
            return entry[0]
        self.misses += 1
        task = self._inflight.get(key)
        if task is None:
            task = asyncio.ensure_future(self._run(key, ttl, fetch))
            self._inflight[key] = task
        # Shield so one cancelled waiter does not cancel the shared fetch for
        # the other waiters.
        return await asyncio.shield(task)

    async def _run(self, key: str, ttl: float, fetch: Callable[[], Awaitable[Any]]) -> Any:
        try:
            value = await fetch()
            self._values[key] = (value, time.monotonic() + ttl)
            return value
        finally:
            self._inflight.pop(key, None)

    def stats(self) -> dict[str, int]:
        now = time.monotonic()
        fresh = sum(1 for _, expiry in self._values.values() if expiry > now)
        return {
            "entries": len(self._values),
            "fresh": fresh,
            "hits": self.hits,
            "misses": self.misses,
            "inflight": len(self._inflight),
        }


class CandleBook:
    """Per ``(instId, bar)`` candle storage fed by WS updates and REST seeds.

    Internally candles are ``[ts_ms, open, high, low, close, volume]`` with
    ``ts_ms`` as int and the rest as floats, keyed by timestamp so a WS update
    for the in-progress candle replaces it in place.
    """

    def __init__(self, max_len: int = 500) -> None:
        self._books: dict[tuple[str, str], dict[int, list[float]]] = {}
        self._max_len = max_len

    def seed(self, inst_id: str, bar: str, rows: list[list[str]]) -> None:
        """Replace the book from BloFin REST rows (newest-first, all strings)."""
        candles: dict[int, list[float]] = {}
        for row in rows:
            ts = int(row[0])
            candles[ts] = [float(row[i]) for i in range(1, 6)]
        self._books[(inst_id, bar)] = candles
        self._trim(inst_id, bar)

    def update(self, inst_id: str, bar: str, candle: list | tuple) -> None:
        """Apply one WS candle (``[ts_ms, o, h, l, c, vol]``, ccxt numeric shape).

        An existing timestamp is replaced (in-progress candle); a new
        timestamp is appended.
        """
        ts = int(candle[0])
        key = (inst_id, bar)
        book = self._books.setdefault(key, {})
        book[ts] = [float(candle[i]) for i in range(1, 6)]
        self._trim(inst_id, bar)

    def _trim(self, inst_id: str, bar: str) -> None:
        book = self._books[(inst_id, bar)]
        if len(book) > self._max_len:
            for ts in sorted(book)[: len(book) - self._max_len]:
                del book[ts]

    def has(self, inst_id: str, bar: str) -> bool:
        return bool(self._books.get((inst_id, bar)))

    def keys(self) -> list[tuple[str, str]]:
        return list(self._books)

    def rest_rows(self, inst_id: str, bar: str, limit: int) -> list[list[str]]:
        """Return BloFin REST-shaped rows: newest-first, all values as strings."""
        book = self._books.get((inst_id, bar))
        if not book:
            return []
        rows = []
        for ts in sorted(book, reverse=True)[:limit]:
            o, h, low, c, vol = book[ts]
            rows.append([str(ts), _num(o), _num(h), _num(low), _num(c), _num(vol)])
        return rows
