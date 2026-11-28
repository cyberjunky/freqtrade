"""aiohttp server: cached market routes, /health, and a verbatim catch-all."""

from __future__ import annotations

import logging
import time

from aiohttp import web

from .cache import CandleBook, TTLCache, bar_to_seconds
from .feed import FeedManager
from .upstream import UpstreamClient

logger = logging.getLogger(__name__)

MARKET_PREFIX = "/api/v1/market/"

# Static TTLs per market endpoint (seconds). Candles and tickers are WS-fed and
# handled by dedicated routes; mark-price/index candles derive TTL from `bar`.
_TTL_TABLE = {
    "books": 1.0,
    "trades": 2.0,
    "mark-price": 2.0,
    "instruments": 300.0,
    "position-tiers": 300.0,
    "funding-rate": 60.0,
    "funding-rate-history": 60.0,
}

_HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "te", "upgrade"}
_FORWARD_DROP = _HOP_BY_HOP | {"host", "content-length"}
# cached bodies are re-served without Content-Encoding, so fetch them uncompressed
_PLAIN = {"Accept-Encoding": "identity"}


def make_app(
    *,
    upstream: UpstreamClient,
    cache: TTLCache,
    book: CandleBook,
    feed: FeedManager | None,
) -> web.Application:
    app = web.Application()
    app["upstream"] = upstream
    app["cache"] = cache
    app["book"] = book
    app["feed"] = feed
    app["started"] = time.monotonic()

    app.router.add_get("/health", health)
    app.router.add_get(MARKET_PREFIX + "candles", candles)
    app.router.add_get(MARKET_PREFIX + "tickers", tickers)
    app.router.add_get(MARKET_PREFIX + "{endpoint}", market_cached)
    app.router.add_route("*", "/{tail:.*}", catch_all)
    return app


async def health(request: web.Request) -> web.Response:
    app = request.app
    feed: FeedManager | None = app["feed"]
    upstream: UpstreamClient = app["upstream"]
    cache: TTLCache = app["cache"]
    book: CandleBook = app["book"]
    return web.json_response(
        {
            "status": "ok",
            "uptime_sec": round(time.monotonic() - app["started"], 1),
            "upstream_requests": upstream.request_count,
            "cache": cache.stats(),
            "ws": feed.status() if feed is not None else {"started": False},
            "candle_books": [f"{inst}/{bar}" for inst, bar in book.keys()],
        }
    )


async def _cached_get(request: web.Request, ttl: float) -> web.Response:
    """Serve a GET from the TTL cache, coalescing misses into one upstream call."""
    app = request.app
    upstream: UpstreamClient = app["upstream"]
    cache: TTLCache = app["cache"]

    async def fetch() -> tuple[bytes, str]:
        status, headers, body = await upstream.request(
            "GET", request.path, request.query_string, headers=_PLAIN
        )
        if status != 200:
            raise web.HTTPBadGateway(
                text=f"upstream returned {status}: {body[:500]!r}",
                content_type="text/plain",
            )
        return body, str(headers.get("Content-Type", "application/json"))

    body, content_type = await cache.get_or_fetch(request.path_qs, ttl, fetch)
    return web.Response(body=body, headers={"Content-Type": content_type})


async def candles(request: web.Request) -> web.Response:
    """WS-fed candles; on a cold key, seed from REST and start the watcher."""
    app = request.app
    book: CandleBook = app["book"]
    cache: TTLCache = app["cache"]
    upstream: UpstreamClient = app["upstream"]
    feed: FeedManager | None = app["feed"]

    inst_id = request.query.get("instId")
    bar = request.query.get("bar", "1m")
    try:
        limit = max(1, min(300, int(request.query.get("limit", "100"))))
    except ValueError:
        limit = 100

    if not inst_id:
        # Not a well-formed candles request; forward verbatim.
        return await catch_all(request)
    if "before" in request.query or "after" in request.query:
        # history page: the WS book only holds recent rows
        return await _cached_get(request, 300.0)

    rows = book.rest_rows(inst_id, bar, limit)
    if not rows:
        try:
            seed_ttl = max(5.0, bar_to_seconds(bar) / 4)
        except ValueError:
            seed_ttl = 5.0

        async def fetch_seed() -> list[list[str]]:
            status, _, body = await upstream.request(
                "GET", MARKET_PREFIX + "candles", request.query_string, headers=_PLAIN
            )
            if status != 200:
                raise web.HTTPBadGateway(
                    text=f"upstream returned {status}: {body[:500]!r}",
                    content_type="text/plain",
                )
            import json

            payload = json.loads(body)
            if str(payload.get("code")) != "0":
                raise web.HTTPBadGateway(
                    text=f"upstream error: {body[:500]!r}", content_type="text/plain"
                )
            return payload.get("data", [])

        data = await cache.get_or_fetch("seed:" + request.path_qs, seed_ttl, fetch_seed)
        book.seed(inst_id, bar, data)
        rows = book.rest_rows(inst_id, bar, limit)

    if feed is not None:
        await feed.ensure_candles(inst_id, bar)
    return web.json_response({"code": "0", "msg": "success", "data": rows})


async def tickers(request: web.Request) -> web.Response:
    """WS-fed tickers when available; otherwise TTL 5s cached passthrough."""
    app = request.app
    feed: FeedManager | None = app["feed"]
    inst_id = request.query.get("instId")

    if feed is not None:
        await feed.ensure_tickers()
    if inst_id and feed is not None and inst_id in feed.tickers:
        t = feed.tickers[inst_id]

        def s(value: object) -> str:
            return "" if value is None else f"{value:.12g}" if isinstance(value, float) else str(value)

        row = {
            "instId": inst_id,
            "last": s(t.get("last")),
            "lastSz": "0",
            "askPx": s(t.get("ask")),
            "askSz": s(t.get("askVolume") or 0),
            "bidPx": s(t.get("bid")),
            "bidSz": s(t.get("bidVolume") or 0),
            "open24h": s(t.get("open")),
            "high24h": s(t.get("high")),
            "low24h": s(t.get("low")),
            "volCcy24h": s(t.get("quoteVolume")),
            "vol24h": s(t.get("baseVolume")),
            "ts": str(t.get("timestamp") or int(time.time() * 1000)),
        }
        return web.json_response({"code": "0", "msg": "success", "data": [row]})
    return await _cached_get(request, 5.0)


async def market_cached(request: web.Request) -> web.Response:
    endpoint = request.match_info["endpoint"]
    ttl = _TTL_TABLE.get(endpoint)
    if ttl is None and endpoint in ("mark-price-candles", "index-candles"):
        bar = request.query.get("bar", "1m")
        try:
            ttl = max(5.0, bar_to_seconds(bar) / 4)
        except ValueError:
            ttl = 5.0
    if ttl is None:
        # Unknown market endpoint: forward verbatim, uncached.
        return await catch_all(request)
    return await _cached_get(request, ttl)


async def catch_all(request: web.Request) -> web.Response:
    """Forward any request verbatim and stream the upstream response back.

    Covers every private/signed endpoint unchanged: BloFin signs
    path+method+timestamp+body, not the Host header.
    """
    upstream: UpstreamClient = request.app["upstream"]
    body = await request.read() if request.can_read_body else None
    headers = {
        k: v for k, v in request.headers.items() if k.lower() not in _FORWARD_DROP
    }
    try:
        async with upstream.stream(
            request.method, request.path, request.query_string, body, headers
        ) as resp:
            out = web.StreamResponse(status=resp.status, reason=resp.reason)
            for k, v in resp.headers.items():
                if k.lower() not in _HOP_BY_HOP:
                    out.headers[k] = v
            await out.prepare(request)
            async for chunk in resp.content.iter_chunked(65536):
                await out.write(chunk)
            await out.write_eof()
            return out
    except TimeoutError:
        raise web.HTTPGatewayTimeout(text="upstream timeout") from None
