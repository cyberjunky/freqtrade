"""CLI entry point: ``python -m blofin_proxy``."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging

from aiohttp import web

from .cache import CandleBook, TTLCache
from .feed import FeedManager
from .limiter import TokenBucket
from .server import MARKET_PREFIX, make_app
from .upstream import UpstreamClient

logger = logging.getLogger("blofin_proxy")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="blofin_proxy",
        description="WS-fed caching reverse proxy for the BloFin REST API.",
    )
    parser.add_argument("--port", type=int, default=8095)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--upstream", default="https://openapi.blofin.com")
    parser.add_argument("--rate", type=int, default=8, help="upstream requests per window")
    parser.add_argument("--rate-window", type=float, default=2.0, help="window in seconds")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> None:
    limiter = TokenBucket(rate=args.rate, window=args.rate_window)
    upstream = UpstreamClient(args.upstream, limiter)
    cache = TTLCache()
    book = CandleBook()

    async def reseed(inst_id: str, bar: str) -> None:
        query = f"instId={inst_id}&bar={bar}&limit=300"
        status, _, body = await upstream.request(
            "GET", MARKET_PREFIX + "candles", query
        )
        if status != 200:
            logger.warning("reseed %s %s failed: upstream %s", inst_id, bar, status)
            return
        payload = json.loads(body)
        if str(payload.get("code")) == "0":
            book.seed(inst_id, bar, payload.get("data", []))
            logger.info("reseeded %s %s from REST", inst_id, bar)

    feed = FeedManager(book, on_reseed=reseed)
    try:
        await feed.start()
    except Exception as exc:  # noqa: BLE001 - WS feed is an optimization, not a hard dep
        logger.warning("WS feed unavailable (%s); serving via REST cache only", exc)
        await feed.close()
        feed = None  # type: ignore[assignment]

    app = make_app(upstream=upstream, cache=cache, book=book, feed=feed)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    logger.info(
        "blofin_proxy listening on http://%s:%d -> %s (rate %d/%ss)",
        args.host, args.port, args.upstream, args.rate, args.rate_window,
    )
    try:
        await asyncio.Event().wait()  # run until cancelled (Ctrl+C)
    finally:
        await runner.cleanup()
        if feed is not None:
            await feed.close()
        await upstream.close()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        logger.info("shutting down")


if __name__ == "__main__":
    main()
