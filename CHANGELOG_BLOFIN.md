# Changelog

All notable changes to this project are documented here.

---

## [Unreleased] — 2026-05-13

### Added

#### BloFin Swap Exchange Support (`freqtrade/exchange/blofin.py`)

New `Blofin(Exchange)` class enabling perpetual swap trading on BloFin via freqtrade.

BloFin is a swap-only exchange with several deviations from the standard freqtrade exchange model. The following were handled:

| Problem | Solution |
|---------|---------|
| `fetchOrder: None` in ccxt blofin | `fetch_order()` override: searches `fetchOpenOrders` then `fetchClosedOrders` by order ID |
| `fetchLeverageTiers: False` | `load_leverage_tiers()` override: derives max leverage from `market['limits']['leverage']['max']` |
| `set_leverage` requires `marginMode` param | `_lev_prep()` override: passes `marginMode` explicitly to `set_leverage` |
| Margin mode is account-wide | `_lev_prep()` calls base `set_margin_mode()` which ignores symbol on BloFin |
| Futures balance in separate account | `get_balances()` override: fetches with `accountType='futures'` |
| Position mode must be set once | `additional_exchange_init()` calls `set_position_mode(hedged=False)` for net/one-way mode |
| Order params need `marginMode` + `positionSide` | `_get_params()` override: appends both fields for futures orders |

**Supported trading modes:** `futures` with `isolated` or `cross` margin.

**Default position mode:** net (one-way) — one position per symbol. Direction flips require closing the existing position first.

**Leverage tiers:** Built from market data at startup. One flat tier per symbol using the exchange-reported max leverage.

#### Exchange Registry Updates

- `freqtrade/exchange/__init__.py` — exports `Blofin`
- `freqtrade/exchange/common.py` — adds `"blofin"` to `SUPPORTED_EXCHANGES`

#### Example Configuration (`user_data/config_blofin.json`)

Ready-to-use config for BloFin swap trading:
- `trading_mode: futures`, `margin_mode: isolated`
- `stake_currency: USDT`, `stake_amount: 10`
- `dry_run: true` — safe default; change to `false` for live trading
- Requires `password` (API passphrase) in addition to `key` and `secret`

### Notes

- **No changes to `MovingGridStrategy`** — the strategy is exchange-agnostic. BloFin's contract sizing is handled transparently by freqtrade's `amount_to_contracts()` / `contracts_to_amount()` utilities using the market's `contractSize` field.
- Stop-loss on exchange is disabled (`stoploss_on_exchange: false`) — BloFin uses a dedicated TPSL API endpoint not yet wired into freqtrade's stoploss flow.
- WebSocket order streaming is not used — freqtrade polls via REST, which is compatible with BloFin's REST API.
