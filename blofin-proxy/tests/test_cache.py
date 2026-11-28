"""Tests for TTLCache (TTL expiry, single-flight) and CandleBook."""

import asyncio

import pytest

from blofin_proxy.cache import CandleBook, TTLCache, bar_to_seconds


# --- bar_to_seconds -------------------------------------------------------


@pytest.mark.parametrize(
    "bar,seconds",
    [
        ("1m", 60),
        ("5m", 300),
        ("15m", 900),
        ("1H", 3600),
        ("4H", 14400),
        ("1D", 86400),
        ("1W", 604800),
    ],
)
def test_bar_to_seconds(bar, seconds):
    assert bar_to_seconds(bar) == seconds


def test_bar_to_seconds_invalid():
    with pytest.raises(ValueError):
        bar_to_seconds("5x")
    with pytest.raises(ValueError):
        bar_to_seconds("m")


# --- TTLCache -------------------------------------------------------------


async def test_ttl_cache_hit_within_ttl():
    cache = TTLCache()
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        return "value"

    assert await cache.get_or_fetch("k", 60.0, fetch) == "value"
    assert await cache.get_or_fetch("k", 60.0, fetch) == "value"
    assert calls == 1
    assert cache.hits == 1
    assert cache.misses == 1


async def test_ttl_cache_expiry():
    cache = TTLCache()
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        return calls

    assert await cache.get_or_fetch("k", 0.05, fetch) == 1
    assert await cache.get_or_fetch("k", 0.05, fetch) == 1
    await asyncio.sleep(0.08)
    assert await cache.get_or_fetch("k", 0.05, fetch) == 2
    assert calls == 2


async def test_single_flight_coalesces_concurrent_misses():
    cache = TTLCache()
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return {"code": "0"}

    results = await asyncio.gather(
        *[cache.get_or_fetch("k", 60.0, fetch) for _ in range(10)]
    )
    assert calls == 1
    assert all(r == {"code": "0"} for r in results)


async def test_failed_fetch_not_cached():
    cache = TTLCache()
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("boom")
        return "ok"

    with pytest.raises(RuntimeError):
        await cache.get_or_fetch("k", 60.0, fetch)
    assert await cache.get_or_fetch("k", 60.0, fetch) == "ok"
    assert calls == 2


# --- CandleBook -----------------------------------------------------------

# BloFin REST shape: newest-first, all strings.
REST_ROWS = [
    ["1700000900000", "102", "112", "92", "107", "12"],
    ["1700000600000", "101", "111", "91", "106", "11"],
    ["1700000300000", "100", "110", "90", "105", "10"],
]


def test_seed_and_rest_rows_ordering():
    book = CandleBook()
    book.seed("BTC-USDT", "5m", REST_ROWS)
    rows = book.rest_rows("BTC-USDT", "5m", 10)
    assert [r[0] for r in rows] == [
        "1700000900000",
        "1700000600000",
        "1700000300000",
    ]
    assert rows[0] == ["1700000900000", "102", "112", "92", "107", "12"]


def test_rest_rows_limit():
    book = CandleBook()
    book.seed("BTC-USDT", "5m", REST_ROWS)
    rows = book.rest_rows("BTC-USDT", "5m", 2)
    assert len(rows) == 2
    assert rows[0][0] == "1700000900000"


def test_rest_rows_empty_book():
    book = CandleBook()
    assert book.rest_rows("BTC-USDT", "5m", 10) == []


def test_update_replaces_in_progress_candle():
    book = CandleBook()
    book.seed("BTC-USDT", "5m", REST_ROWS)
    # Same timestamp as the newest candle -> replace, not append.
    book.update("BTC-USDT", "5m", [1700000900000, 102.0, 120.0, 95.0, 118.0, 30.0])
    rows = book.rest_rows("BTC-USDT", "5m", 10)
    assert len(rows) == 3
    assert rows[0] == ["1700000900000", "102", "120", "95", "118", "30"]


def test_update_appends_new_candle():
    book = CandleBook()
    book.seed("BTC-USDT", "5m", REST_ROWS)
    book.update("BTC-USDT", "5m", [1700001200000, 107.0, 115.0, 106.0, 114.0, 5.0])
    rows = book.rest_rows("BTC-USDT", "5m", 10)
    assert len(rows) == 4
    assert rows[0][0] == "1700001200000"
    assert rows[1][0] == "1700000900000"


def test_update_out_of_order_keeps_sorted():
    book = CandleBook()
    book.update("BTC-USDT", "5m", [1700000900000, 1, 2, 0.5, 1.5, 1])
    book.update("BTC-USDT", "5m", [1700000300000, 1, 2, 0.5, 1.5, 1])
    book.update("BTC-USDT", "5m", [1700000600000, 1, 2, 0.5, 1.5, 1])
    rows = book.rest_rows("BTC-USDT", "5m", 10)
    assert [r[0] for r in rows] == [
        "1700000900000",
        "1700000600000",
        "1700000300000",
    ]


def test_trim_to_max_len():
    book = CandleBook(max_len=3)
    for i in range(5):
        book.update("BTC-USDT", "5m", [1700000000000 + i * 300000, 1, 2, 0.5, 1.5, 1])
    rows = book.rest_rows("BTC-USDT", "5m", 10)
    assert len(rows) == 3
    assert rows[0][0] == "1700001200000"
    assert rows[-1][0] == "1700000600000"
