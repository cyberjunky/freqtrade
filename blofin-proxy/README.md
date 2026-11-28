# blofin-proxy

A local WS-fed caching reverse proxy for the BloFin API, built for running
multiple freqtrade bots against BloFin without getting the IP rate-limited.

Each bot independently polling REST (`market/candles`, `mark-price-candles`,
`tickers`, `books`, ...) per pair per few seconds multiplies into a ban:
N bots × M pairs × K timeframes. This proxy collapses that traffic to:

- **one WebSocket connection** (via `ccxt.pro.blofin`) feeding a live candle
  and ticker cache, and
- **single-flight + TTL-cached** upstream REST for everything else, all gated
  by one shared token-bucket rate limiter (default 8 req / 2 s).

Private/signed endpoints (orders, balance, ...) are forwarded **verbatim** —
BloFin signs path+method+timestamp+body, not the Host header, so trading keeps
working through the proxy unchanged.

## Install

```bash
pip install -r requirements.txt   # aiohttp, ccxt>=4.5
```

## Run

```bash
cd blofin-proxy
python -m blofin_proxy --port 8095 --host 127.0.0.1
```

Options: `--upstream` (default `https://openapi.blofin.com`), `--rate`
(default 8), `--rate-window` (default 2.0 s), `--log-level`.

Sanity checks:

```bash
curl "http://127.0.0.1:8095/health"
curl "http://127.0.0.1:8095/api/v1/market/candles?instId=BTC-USDT&bar=5m&limit=5"
```

`/health` reports uptime, WS watcher status, cache hit/miss stats, and the
total upstream request counter (proof that bot traffic collapsed).

## Point freqtrade at the proxy

In each bot's config:

```json
"exchange": {
  "name": "blofin",
  "ccxt_config": {
    "enableRateLimit": false,
    "urls": {"api": {"rest": "http://127.0.0.1:8095"}}
  },
  "ccxt_async_config": {
    "enableRateLimit": false,
    "urls": {"api": {"rest": "http://127.0.0.1:8095"}}
  }
}
```

`enableRateLimit: false` is safe because the proxy is now the single
gatekeeper for upstream REST traffic.

## How endpoints are served

| Endpoint (`/api/v1/market/...`) | Strategy |
|---|---|
| `candles` | WS-fed candle book; cold keys seed from REST (single-flight) and start a watcher |
| `mark-price-candles`, `index-candles` | TTL = max(5 s, bar/4) + single-flight |
| `tickers` | WS-fed when available; TTL 5 s cached fallback |
| `books` | TTL 1 s + single-flight |
| `trades`, `mark-price` | TTL 2 s + single-flight |
| `instruments`, `position-tiers` | TTL 300 s |
| `funding-rate`, `funding-rate-history` | TTL 60 s |
| everything else (any method) | forwarded verbatim, streamed back through the limiter |

## Development

```bash
# from the repo root
.venv/Scripts/python.exe -m pytest blofin-proxy/tests -q
```

Layout: `blofin_proxy/limiter.py` (token bucket), `cache.py` (TTLCache +
CandleBook), `upstream.py` (forwarding client), `server.py` (routes +
catch-all), `feed.py` (ccxt.pro WS watcher manager), `__main__.py` (CLI).
