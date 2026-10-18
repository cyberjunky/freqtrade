# Improvements

All notable changes this fork makes on top of upstream freqtrade `develop` are documented here.

---

## [Unreleased] — 2026-08-15

### Hyperliquid

- **`RateLimitExceeded` now gets backoff, not just `DDoSProtection`.** In ccxt, `RateLimitExceeded`
  is a sibling of `DDoSProtection` (both inherit from `NetworkError`), not a subclass of it. Every
  exchange exception handler in freqtrade only caught `DDoSProtection`, so a 429 from Hyperliquid's
  `/info` endpoint fell through to a plain `TemporaryError` — which the retrier retries
  *immediately, with no delay*, hammering an endpoint that just told it to back off. Widened all 47
  occurrences of `except ccxt.DDoSProtection` across 10 exchange files (`exchange.py`,
  `hyperliquid.py`, `blofin.py`, `binance.py`, `bybit.py`, `bitget.py`, `okx.py`, `gate.py`,
  `kraken.py`, `krakenfutures.py`) to also catch `ccxt.RateLimitExceeded`.
- **Quieter websocket noise.** Transient Hyperliquid WS disconnect/reconnect chatter no longer spams
  the logs at warning level.

### BloFin swap exchange support (`freqtrade/exchange/blofin.py`)

`Blofin(Exchange)` — perpetual swap trading on BloFin, futures-only (`isolated` margin), one-way
(net) position mode. BloFin deviates from freqtrade's exchange model in several ways, each handled
by an override:

| Problem | Solution |
|---------|---------|
| `fetchOrder` unsupported by ccxt's BloFin adapter | `fetch_order()` searches `fetchOpenOrders` then `fetchClosedOrders` by order ID |
| ccxt's `describe()` advertises `fetchOrder: None`, so freqtrade's pre-flight `validate_exchange` check rejects the exchange before our subclass even loads | `describe()` patched at import time on all three ccxt submodules (sync/async/pro) to advertise `fetchOrder: True` |
| `fetchLeverageTiers` unsupported | `load_leverage_tiers()` derives one flat tier per symbol from `market['limits']['leverage']['max']`, with a conservative 2% default maintenance margin rate when the exchange doesn't expose one |
| `set_leverage` requires an explicit `marginMode` param | `_lev_prep()` passes it explicitly |
| Margin mode is account-wide, not per-symbol | `_lev_prep()` calls the base `set_margin_mode()`, which BloFin ignores the symbol on |
| Position mode must be set once at startup | `additional_exchange_init()` calls `set_position_mode(hedged=False)` |
| Order params need `marginMode` + `positionSide` | `_get_params()` appends both for futures orders |
| Public endpoints sit behind Cloudflare, which serves a JS challenge / 429 HTML page to non-browser clients | A real browser `User-Agent` is set on both sync and async ccxt clients; Cloudflare 403/429/1015 HTML responses are detected and collapsed into a single retryable `DDosProtection` (with backoff) instead of dumping the whole page on every retry |
| ccxt's `fetch_ohlcv` never sends BloFin's `after` cursor, so only the most recent ~500 candles come back regardless of `since` — no real history | `_async_get_candle_history()` paginates the REST candle endpoint directly with `after`, enabling real historic backfill |
| ccxt advertises `fetchMarkOHLCV`/`fetchIndexOHLCV` as unsupported | Routed to BloFin's `/market/mark-price-candles` and `/market/index-candles` endpoints directly, enabling futures backtesting (which needs mark candles) |
| Candle limit undocumented in ccxt (hardcoded comment claims max 100) | `ohlcv_candle_limit` raised to 1440 — BloFin's REST endpoint accepts it |
| Volume column off-by-one | `_fetch_blofin_ohlcv` guarded index 5 with `len(r) > 6` (needs 7 columns to read the 6th). Native BloFin responses have 9 columns so this passed by luck, but a 6-column reply (e.g. from a caching proxy) silently zeroed volume on every candle — disabling any strategy gate on `volume > 0` with no error anywhere. Fixed to `len(r) > 5`. |
| `baseVolume` reported in contracts, not base currency; `quoteVolume` left `None` | `get_tickers()` synthesizes `quoteVolume = baseVolume × contractSize × last` for linear swaps so `VolumePairList` has something to sort on |
| Futures balance lives in a separate account view | `get_balances()` fetches with `accountType='swap'` (trading-account equity/available-margin view, not the wallet-holdings view) |
| No `fetchFundingHistory` in dry-run | Funding fees are read live via `fetchFundingHistory`; dry-run returns `0.0` since BloFin has no `fetchMarkOHLCV` to simulate from |
| WebSocket `watch_ohlcv` | Disabled (`ws_enabled: False`) — empirically, candle reuse never succeeds for BloFin in a long-running multi-pair bot (confirmed over a 10h live run); REST-only avoids the connection overhead and log spam for zero benefit |

### Custom pairlist handlers from `user_data/pairlist/`

Custom `IPairList` subclasses placed in `user_data/pairlist/` are discovered and loaded by
`PairListResolver`, mirroring how strategies load from `user_data/strategies/`.

**Usage:** create `user_data/pairlist/MyPairList.py` with a class extending `IPairList`, then
reference it by class name in the config: `"pairlists": [{"method": "MyPairList"}]`.

| File | Change |
|------|--------|
| `freqtrade/constants.py` | Added `USERPATH_PAIRLISTS = "pairlist"` |
| `freqtrade/resolvers/pairlist_resolver.py` | Set `user_subdir = USERPATH_PAIRLISTS` |
| `freqtrade/configuration/directory_operations.py` | `freqtrade create-userdir` now creates `user_data/pairlist/` |
| `freqtrade/config_schema/config_schema.py` + `build_helpers/schema.json` | `pairlists[].method` accepts arbitrary strings (`anyOf` string-with-enum-hint + plain string), not just the built-in `AVAILABLE_PAIRLISTS` enum |

Example handler tracked at `user_data/pairlist/OscillationFilter.py`, filtering pairs by choppiness
(range-bound oscillation) rather than trend. Current live config:

```json
{
    "method": "OscillationFilter",
    "lookback_days": 7,
    "timeframe": "1h",
    "min_oscillation_ratio": 0.3,
    "min_reversals_per_day": 2.0,
    "max_spike_ratio": 8.0,
    "min_choppiness": 42.0,
    "max_doji_ratio": 0.3,
    "recent_hours": 24,
    "recent_min_oscillation_ratio": 0.25,
    "recent_min_choppiness": 40.0,
    "refresh_period": 1800
}
```

### Misc

- **SQLite connection pool widened** (`freqtrade/persistence/models.py`). File-backed SQLite kept
  SQLAlchemy's default `QueuePool` of 5 + 10 overflow, shared by the bot loop, the API server, and
  the RPC threads. A slow exchange cycle (retries against a rate-limited endpoint, say) parks
  connections long enough to exhaust it — the API server then dies with `QueuePool limit of size 5
  overflow 10 reached` while the bot keeps trading, so the UI shows no trades as though the database
  had emptied. SQLite tolerates many readers and serialises writes itself, so a wider pool
  (`pool_size=20`, `max_overflow=40`, `pool_timeout=60`) costs nothing.

### Proxmox deployment (`proxmox/freqtrade-ve.sh`)

Self-contained PVE host script that provisions an unprivileged Debian 13 (trixie) LXC, installs
freqtrade (this fork or stock `develop`), bind-mounts `user_data` from the host so it stays visible
in an editor over SSH, ships a `freqtrade@.service` template for running multiple bots, and sets up
a scheduled `vzdump` backup job. Iterated since the initial script to: pick storage pools
interactively (with usage shown), default to 4 vCPU / 4G / 16G with SSH enabled, run the bot as the
non-root provisioning user with a matching sshd drop-in, generate the `en_US.UTF-8` / `C.UTF-8`
locales (silences SSH `LANG`-forward warnings), install the `hyperopt` extra so scipy-using
strategies load, and read the freqtrade systemd unit's `--db-url`/`--logfile` from config instead of
forcing them.
