"""candles route: paged history goes upstream, not to the live WS book; cached bodies are fetched uncompressed."""

import asyncio
import json

from aiohttp.test_utils import TestClient, TestServer

from blofin_proxy.cache import CandleBook, TTLCache
from blofin_proxy.server import make_app


class FakeUpstream:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.headers: list[dict | None] = []

    async def request(self, method, path, query_string=None, body=None, headers=None):
        self.calls.append(query_string or "")
        self.headers.append(headers)
        ts = "1000" if "after" in (query_string or "") else "9000"
        data = [[ts, "1", "1", "1", "1", "1", "1", "1", "1"]]
        return 200, {"Content-Type": "application/json"}, json.dumps({"code": "0", "data": data}).encode()


async def _get(app, url):
    async with TestClient(TestServer(app)) as client:
        resp = await client.get(url)
        return resp.status, await resp.json()


def test_history_page_bypasses_live_book():
    up, book = FakeUpstream(), CandleBook()
    book.seed("BTC-USDT", "5m", [["9000", "2", "2", "2", "2", "2", "2", "2", "2"]])
    app = make_app(upstream=up, cache=TTLCache(), book=book, feed=None)
    status, body = asyncio.run(_get(app, "/api/v1/market/candles?instId=BTC-USDT&bar=5m&after=2000&before=999"))
    assert status == 200
    assert body["data"][0][0] == "1000"  # the requested page, not the newest live row
    assert up.calls == ["instId=BTC-USDT&bar=5m&after=2000&before=999"]


def test_live_request_still_served_from_book():
    up, book = FakeUpstream(), CandleBook()
    book.seed("BTC-USDT", "5m", [["9000", "2", "2", "2", "2", "2", "2", "2", "2"]])
    app = make_app(upstream=up, cache=TTLCache(), book=book, feed=None)
    status, body = asyncio.run(_get(app, "/api/v1/market/candles?instId=BTC-USDT&bar=5m&limit=5"))
    assert status == 200
    assert body["data"][0][0] == "9000"
    assert up.calls == []


def test_cached_and_seed_requests_ask_for_uncompressed_bodies():
    up = FakeUpstream()
    app = make_app(upstream=up, cache=TTLCache(), book=CandleBook(), feed=None)

    async def run():
        async with TestClient(TestServer(app)) as client:
            await client.get("/api/v1/market/candles?instId=BTC-USDT&bar=5m&after=2000")  # history page
            await client.get("/api/v1/market/candles?instId=ETH-USDT&bar=5m&limit=5")  # cold live key: seed
            await client.get("/api/v1/market/instruments?instType=SWAP")  # TTL-cached endpoint

    asyncio.run(run())
    assert len(up.headers) == 3
    assert all(h == {"Accept-Encoding": "identity"} for h in up.headers)
