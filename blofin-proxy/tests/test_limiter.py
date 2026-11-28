"""Tests for the async token bucket rate limiter."""

import asyncio
import time

import pytest

from blofin_proxy.limiter import TokenBucket


def test_invalid_config():
    with pytest.raises(ValueError):
        TokenBucket(rate=0)
    with pytest.raises(ValueError):
        TokenBucket(rate=8, window=0)


async def test_burst_is_immediate():
    bucket = TokenBucket(rate=4, window=1.0)
    start = time.monotonic()
    for _ in range(4):
        await bucket.acquire()
    assert time.monotonic() - start < 0.2


async def test_pacing_beyond_burst():
    # 4 tokens per 0.4s -> refill 10/s. After a 4-token burst, the next 4
    # acquires must be paced out over ~0.4s total.
    bucket = TokenBucket(rate=4, window=0.4)
    start = time.monotonic()
    for _ in range(8):
        await bucket.acquire()
    elapsed = time.monotonic() - start
    assert 0.3 <= elapsed < 1.5


async def test_concurrent_acquires_are_serialized():
    bucket = TokenBucket(rate=4, window=0.4)
    start = time.monotonic()
    await asyncio.gather(*[bucket.acquire() for _ in range(8)])
    elapsed = time.monotonic() - start
    assert 0.3 <= elapsed < 1.5


async def test_refill_caps_at_capacity():
    bucket = TokenBucket(rate=2, window=0.2)
    await asyncio.sleep(0.5)  # bucket may not accumulate beyond 2 tokens
    start = time.monotonic()
    for _ in range(4):  # 2 instant + 2 paced at 10/s -> ~0.2s
        await bucket.acquire()
    elapsed = time.monotonic() - start
    assert 0.12 <= elapsed < 1.0
