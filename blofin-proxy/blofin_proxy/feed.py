"""WebSocket feed manager backed by a single ccxt.pro.blofin instance."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from .cache import CandleBook

logger = logging.getLogger(__name__)

_TF_UNITS = {"m": "m", "H": "h", "D": "d", "W": "w", "M": "M"}


def bar_to_ccxt_timeframe(bar: str) -> str:
    """Map a BloFin bar (``5m``, ``1H``, ``1D``) to a ccxt timeframe (``5m``, ``1h``, ``1d``)."""
    unit = bar[-1]
    if unit not in _TF_UNITS:
        raise ValueError(f"unknown bar unit: {bar!r}")
    return bar[:-1] + _TF_UNITS[unit]


class FeedManager:
    """Idempotent WS watcher manager.

    One shared ``ccxt.pro.blofin`` connection multiplexes ``watch_ohlcv`` per
    (symbol, timeframe) and one ``watch_tickers`` loop. Watchers reconnect with
    exponential backoff; after a gap the candle key is reseeded from REST once
    via the ``on_reseed`` callback.
    """

    def __init__(
        self,
        book: CandleBook,
        on_reseed: Callable[[str, str], Awaitable[None]] | None = None,
    ) -> None:
        self.book = book
        self.tickers: dict[str, dict[str, Any]] = {}
        self.last_error: str | None = None
        self._on_reseed = on_reseed
        self._ex: Any = None
        self._tasks: dict[tuple, asyncio.Task] = {}
        self._id_to_symbol: dict[str, str] = {}
        self._started = False
        self._stopped = False

    async def start(self) -> None:
        """Create the ccxt.pro instance and load markets once at startup."""
        import ccxt.pro as ccxtpro  # imported lazily: heavy module

        self._ex = ccxtpro.blofin({"enableRateLimit": True})
        markets = await self._ex.load_markets()
        self._id_to_symbol = {m["id"]: m["symbol"] for m in markets.values()}
        self._started = True
        logger.info("feed started, %d markets loaded", len(self._id_to_symbol))

    @property
    def started(self) -> bool:
        return self._started

    async def ensure_candles(self, inst_id: str, bar: str) -> None:
        """Idempotently spawn a ``watch_ohlcv`` loop for (instId, bar)."""
        if not self._started or self._stopped:
            return
        key = ("candles", inst_id, bar)
        if key in self._tasks and not self._tasks[key].done():
            return
        symbol = self._id_to_symbol.get(inst_id)
        if symbol is None:
            logger.warning("no market for instId %s, skipping candle watcher", inst_id)
            return
        try:
            timeframe = bar_to_ccxt_timeframe(bar)
        except ValueError:
            logger.warning("unsupported bar %s, skipping candle watcher", bar)
            return
        self._tasks[key] = asyncio.create_task(
            self._watch_candles(inst_id, bar, symbol, timeframe)
        )
        logger.info("watching candles %s %s (%s %s)", inst_id, bar, symbol, timeframe)

    async def ensure_tickers(self) -> None:
        """Idempotently spawn the single ``watch_tickers`` loop."""
        if not self._started or self._stopped:
            return
        key = ("tickers",)
        if key in self._tasks and not self._tasks[key].done():
            return
        self._tasks[key] = asyncio.create_task(self._watch_tickers())
        logger.info("watching tickers")

    async def _watch_candles(
        self, inst_id: str, bar: str, symbol: str, timeframe: str
    ) -> None:
        backoff = 1.0
        had_gap = False
        while not self._stopped:
            try:
                if had_gap and self._on_reseed is not None:
                    # Reseed from REST once so a WS gap cannot leave a hole.
                    await self._on_reseed(inst_id, bar)
                    had_gap = False
                ohlcv = await self._ex.watch_ohlcv(symbol, timeframe)
                backoff = 1.0
                if ohlcv:
                    self.book.update(inst_id, bar, ohlcv[-1])
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - reconnect on any WS error
                self.last_error = f"candles {inst_id} {bar}: {exc}"
                logger.warning("candle watcher error: %s (retry in %.0fs)", exc, backoff)
                had_gap = True
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)

    async def _watch_tickers(self) -> None:
        backoff = 1.0
        while not self._stopped:
            try:
                tickers = await self._ex.watch_tickers()
                backoff = 1.0
                for symbol, ticker in tickers.items():
                    market = self._ex.market(symbol)
                    self.tickers[market["id"]] = ticker
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - reconnect on any WS error
                self.last_error = f"tickers: {exc}"
                logger.warning("ticker watcher error: %s (retry in %.0fs)", exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)

    def status(self) -> dict[str, Any]:
        return {
            "started": self._started,
            "watchers": {
                "/".join(str(part) for part in key): not task.done()
                for key, task in self._tasks.items()
            },
            "tickers_cached": len(self.tickers),
            "last_error": self.last_error,
        }

    async def close(self) -> None:
        self._stopped = True
        for task in self._tasks.values():
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()
        if self._ex is not None:
            await self._ex.close()
        self._started = False
