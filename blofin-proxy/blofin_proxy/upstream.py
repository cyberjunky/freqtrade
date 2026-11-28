"""aiohttp forwarding client for upstream BloFin REST, gated by the token bucket."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiohttp

from .limiter import TokenBucket

logger = logging.getLogger(__name__)


class UpstreamClient:
    """Forwards HTTP calls to the upstream BloFin REST API through the limiter.

    Counts every upstream request so ``/health`` can prove traffic collapsed.
    ``auto_decompress`` is disabled so byte-level forwarding stays verbatim
    (a compressed upstream reply is passed on untouched).
    """

    def __init__(self, base_url: str, limiter: TokenBucket, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.limiter = limiter
        self.request_count = 0
        self._session: aiohttp.ClientSession | None = None
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout, auto_decompress=False
            )

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    def _url(self, path: str, query_string: str | None) -> str:
        url = self.base_url + path
        if query_string:
            url += "?" + query_string
        return url

    async def request(
        self,
        method: str,
        path: str,
        query_string: str | None = None,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, aiohttp.typedefs.LooseHeaders, bytes]:
        """Buffered request; returns ``(status, headers, body)``."""
        async with self.stream(method, path, query_string, body, headers) as resp:
            payload = await resp.read()
            return resp.status, resp.headers, payload

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        path: str,
        query_string: str | None = None,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        """Streamed request; yields the live upstream response for chunk copying."""
        await self.start()
        await self.limiter.acquire()
        self.request_count += 1
        url = self._url(path, query_string)
        logger.info("upstream #%d %s %s", self.request_count, method, url)
        async with self._session.request(
            method, url, data=body, headers=headers
        ) as resp:
            yield resp
