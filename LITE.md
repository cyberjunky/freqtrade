# Freqtrade Lite

`lite` is a slimmed-down branch of this fork. It was branched from `improvements` right after
merging upstream `develop` (merge commit `ef86a2909`, 2026-11-21). It drops subsystems that are not
needed to backtest, dry-run and trade, and makes those three more accurate, faster and more
stable. All exchanges are kept.

Fork-specific features that predate this branch (BloFin adapter, custom pairlists, rate-limit
backoff) are documented in [IMPROVEMENTS.md](IMPROVEMENTS.md). This file documents only what `lite`
changes on top of that.

**Status legend:** ✅ done · 📋 planned (not started)

---

## 1. Scope decisions

| Area | Decision |
| --- | --- |
| Exchanges | All kept, as upstream plus this fork's BloFin adapter. A first pass removed everything except BloFin, Hyperliquid and Kraken; that was reversed (see 2.5). |
| `strategy-updater`, Edge stubs | Removed. |
| FreqUI | Redesigned (see section 6). |
| FreqAI | Removed. |
| Plotting (`plot-dataframe`, `plot-profit`, plotly) | Removed. FreqUI charts are unaffected. |
| Hyperopt | Kept. |
| Telegram | Kept. |
| REST API, websocket and FreqUI | Kept. |
| Webhook and Discord notifications | Removed. |
| Producer/consumer mode | Removed. |
| Trading and backtest logic | May be redesigned where it is clearly more accurate. Every change that can alter results is listed in section 4. |

---

## 2. What was removed

### 2.1 FreqAI ✅

- **Code:** `freqtrade/freqai/`, `FreqaiModelResolver`, the two FreqAI example strategy templates.
- **CLI:** `list-freqaimodels`, `--freqaimodel`, `--freqaimodel-path`,
  `--freqai-backtest-live-models`.
- **Config:** the `freqai`, `freqaimodel` and `freqaimodel_path` keys are no longer in the schema.
  The `user_data/freqaimodels/` folder is no longer created.
- **Strategy interface:** `feature_engineering_expand_all`, `feature_engineering_expand_basic`,
  `feature_engineering_standard`, `set_freqai_targets`, `populate_any_indicators`,
  `load_freqAI_model` and `ft_bot_cleanup` (which only shut FreqAI down).
- **Other core:** `DataProvider.get_required_startup`, `Exchange.validate_freqai`, the FreqAI
  startup-candle bump and live-model timerange in backtesting, the correlated-pairlist expansion.
- **API:** the `/freqaimodels` endpoint and the `freqaimodel` / `freqai` fields on the backtest and
  pair-history requests. `ft_client.pair_history()` lost its `freqaimodel` parameter.
- **Packaging:** the `freqai` and `freqai_rl` extras, `requirements-freqai*.txt`, the FreqAI
  Dockerfiles, compose file, CI image builds and Renovate groups.
- **Docs and tests:** all `docs/freqai*.md`, `tests/freqai/` and the FreqAI test strategies.

Backtest result files written by older versions still load; the `freqaimodel` metadata keys are
simply no longer written.

### 2.2 Plotting ✅

- **Code:** `freqtrade/plot/`, the `plot-dataframe` and `plot-profit` commands and their options
  (`--indicators1`, `--indicators2`, `--plot-limit`, `--no-trades`, `--trade-source`, …),
  `RunMode.PLOT`, the `user_data/plot/` folder.
- **Packaging:** the `plot` extra (plotly), `requirements-plot.txt`, `docker/Dockerfile.plot` and
  the plot image builds in CI.
- **Docs:** `docs/plotting.md` and the plot command pages. Plotly cells were stripped from the
  strategy-analysis notebook.

**Kept:** the strategy `plot_config` and `plot_annotations` attributes and the `/plot_config` API,
because FreqUI draws its charts from them. Their documentation moved to `docs/freq-ui.md`.

### 2.3 Webhook and Discord ✅

- `freqtrade/rpc/webhook.py`, `freqtrade/rpc/discord.py` and their registration in the RPC manager.
- The `webhook` and `discord` config sections, their secret redaction and the old webhook-setting
  rename shim.
- `docs/webhook-config.md`.

### 2.4 Producer/consumer mode ✅

- `ExternalMessageConsumer`, `ProducerPairList` and the `external_message_consumer` config section.
- The consuming side of `DataProvider`: `get_producer_df`, `get_producer_pairs` and the external
  dataframe storage.
- `docs/producer-consumer.md`.

**Kept:** the server side of the API websocket (`/api/v1/message/ws`, analysed-dataframe and
whitelist messages), because FreqUI uses it for live updates.

### 2.5 Exchanges: removed, then restored ✅

A first pass deleted every exchange adapter except BloFin, Hyperliquid, Kraken and Kraken Futures.
That was reversed: all adapters, the generic ccxt fallback, the Binance helpers (public-data fast
download, bundled leverage tiers, margin-interest formula), `DelistFilter`, `proxy_coin`, the
new-config wizard and the exchange tests are back exactly as on `improvements`. No exchange
behaviour differs from `improvements` except for the changes listed in section 4.

### 2.6 Legacy commands ✅

- **`strategy-updater`** (the interface v2 to v3 converter) and its only dependency,
  `ast-comments`.
- **Edge leftovers:** the hidden `edge` subcommand and the config check that only printed that
  Edge was removed.
- A dataframe `drop` call in backtesting whose result was discarded.

---

## 3. Migration notes

If you move an existing setup to `lite`:

- Remove `freqai`, `webhook`, `discord` and `external_message_consumer` sections from your config;
  the schema no longer accepts them.
- Remove `ProducerPairList` from `pairlists`.
- Strategies must not define the FreqAI hooks listed in 2.1. They are not called.
- Install without the `freqai`, `freqai_rl` and `plot` extras; they no longer exist.
- Strategy callbacks must not modify the `trade` object they receive (see B1 in 4.2).
- The vendored FreqUI (`frequi/`) still shows an "Enable FreqAI" option in its backtesting view.
  Do not use it; the endpoint behind it is gone. Removing the option needs a UI rebuild. 📋

---

## 4. Behaviour changes to trading and backtesting

The items come from a code audit of the remaining core. Each one was re-verified against the code
before it was changed. Items marked ✅ are implemented and covered by tests; 📋 items are not
started.

### 4.1 Accuracy (backtest vs dry-run vs live)

| # | Status | Change | Effect on results |
| --- | --- | --- | --- |
| A1 | ✅ | **Backtest funding window.** A fill is stamped with its candle's open time but happens inside that candle, after a funding event at that timestamp. Backtest no longer charges that event to a position opened in that candle, and on a position adjustment or partial exit the event is charged once, on the size held when it settled. Previously it was charged again on the new size. | Backtest funding fees drop for trades opened on a funding timestamp and for strategies that adjust positions. In the repo's test data one position-adjustment trade went from −0.1467 to −0.1227 USDT, verified by hand against the raw funding events. Live and dry-run are unchanged. |
| A2 | ✅ | **Whole-number leverage.** BloFin, Hyperliquid and Binance only apply integer leverage. The strategy's leverage is now floored once (`Exchange.clamp_leverage`), and that value is used for order sizing and stored on the trade in live, dry-run and backtest. Previously 2.5x was sent to the exchange as 2x while the trade record and the backtest used 2.5x. | Strategies returning fractional leverage on BloFin, Hyperliquid or Binance now backtest at the floored value. Other exchanges are unaffected. |
| A3 | ✅ | **BloFin dry-run funding.** Dry-run now simulates funding from funding rate × mark price, as backtesting does. It used to report 0. | BloFin dry-run profit now includes funding. The simulation path is unit-tested but has not been run against the live BloFin API from this branch. |
| A6 | ✅ | **Dry-run stoploss fee.** A triggered stoploss is charged the taker fee. It was charged maker. | Slightly lower dry-run profit on stopped-out trades, matching live. |
| A7 | ✅ | **Liquidation before stoploss.** When the liquidation price sits between the entry and the stoploss (wide stop, high leverage), a candle that reaches both now exits as a liquidation at the liquidation price. It used to exit as a stoploss at a price the position could never have reached. | Backtests of over-leveraged setups show liquidations (and their worse price) where they previously showed ordinary stoploss exits. No change when the stop sits before the liquidation price. |
| A8 | ✅ | **BloFin candle volume in base currency.** The adapter read the contracts column as volume. One BloFin BTC contract is 0.001 BTC, so BTC volume was 1000 times too high, and volumes were not comparable between pairs with different contract sizes. It now reads the base-currency column (checked against the live API: 12,654 contracts = 12.654 BTC). | Anything using candle `volume` on BloFin changes: volume indicators, volume filters in strategies, and `VolumePairList` in lookback mode. **BloFin candle data downloaded before this fix has the old values; re-download it (`download-data --erase`) before comparing backtests.** |
| A4 | Not changed | A resting limit order that the next candle gaps through never fills in backtest, while live it would fill at the open. Left as is: the current behaviour is the conservative one (it misses favourable fills), and filling at a different price than the order's would touch stake and cost bookkeeping. | — |
| A5 | Not changed | Backtest applies the higher of maker and taker fee to every order. Left as is: whether a limit order at the market price ends up maker or taker live is not knowable from candles, so the worst case is the honest assumption. | — |

### 4.2 Performance

| # | Status | Change |
| --- | --- | --- |
| B1 | ✅ | **No trade copy per callback in backtest and hyperopt.** Live and dry-run still hand each strategy callback a deep copy of the trade to protect it from accidental modification. In backtesting that copy cost far more than the callback and was made per open trade per candle. **Consequence:** a callback that modifies `trade` now changes the real object in backtest, but still only a copy in live. Callbacks must treat `trade` as read-only. |
| B3 | ✅ | Total closed profit in backtest uses the running total instead of re-summing every closed trade on each entry check. |
| B5 | ✅ (part) | Removed the eagerly formatted debug messages on every stoploss update. |
| B4 | ✅ | The pair-lock check made for every backtest entry signal is one pass with early exit instead of building two filtered lists. Also fixed: `unlock_reason` in backtesting ignored the time it was given. |
| B2 | ✅ | **Live candle frame sized by need.** In dry-run and live the per-pair frame is now `startup_candle_count` + 500 candles, at least 1000, instead of the exchange page size (5000 on Hyperliquid, 1440 on BloFin). The strategy analyses the whole frame on every candle, so this cuts that work by about 80% on Hyperliquid and 30% on BloFin. A refresh now requests only the candles since the last one plus 5, not a full page per pair. `exchange.live_candle_limit` sets the frame size explicitly; larger frames are filled with paged calls (up to 5 pages, so 7200 candles on BloFin). The page size is only a per-request limit, not a ceiling. Exchanges with small pages (Kraken, 720) keep exactly what they had. Backtesting and `download-data` are unaffected. **Consequence:** a strategy whose indicators need more history than its `startup_candle_count` declares used to get away with it on Hyperliquid; declare the real value or set `live_candle_limit`. |
| B5 | 📋 (rest) | Repeated filled-order scans; full-history dataframe copy per `get_pair_dataframe` call. |

### 4.3 Stability

| # | Status | Change |
| --- | --- | --- |
| C1 | ✅ | **The bot loop survives unexpected errors.** An unhandled exception in one iteration (for example a pricing error while replacing an order) used to end the process and leave open positions unmanaged. It is now logged, the loop retries after the normal retry timeout, and after 5 consecutive failures trading is stopped with a notification (same as an `OperationalException`; `/start` resumes). The database session is rolled back only for database errors, so a pending record of an order that already exists on the exchange is not discarded. |
| C2 | ✅ | **Retries wait.** A retry after a temporary exchange error now waits a short, growing, jittered delay (about 0.25–1.25 s) instead of firing immediately. BloFin's leverage preparation no longer nests two retry layers (previously up to 25 calls for one failing order). |
| C3 | ✅ | **No untracked entries.** The fee and funding lookups (network calls that can fail) now run before the entry order is placed. Previously they ran between placing the order and saving the trade, so a failure there left a position on the exchange that the bot had no record of. |
| C4 | Not changed | The on-exchange stoploss is cancelled before `confirm_trade_exit` is asked and the exit order placed. Left as is: on spot the stoploss locks the balance the exit amount is computed from, so it has to be cancelled first, and if the exit is denied the stoploss is re-placed on the next loop a few seconds later. |
| C5 | Not changed | The dry-run order store keeps every order for the life of the process. Left as is: dropping closed orders would make a later lookup rebuild them from the database and re-run the fill simulation, which can change a fill that already happened. The memory cost is one small record per order. |

### 4.4 Legacy code 📋

Remaining candidates, to be removed only where nothing kept depends on them: strategy interface
v2 compatibility shims, deprecated-setting handling, legacy backtest-result loaders, deprecated
`/forcebuy` and `/forcesell` API routes. (`strategy-updater` and the Edge stubs are done, see 2.6.
The Bybit/OKX funding-timeframe migration and the margin-interest code stay, because those
exchanges are kept.)

---

## 5. Verification

A local virtualenv (`.venv`, Python 3.14) runs the test suite and `ruff`. Run the suite with
`PYTHONPATH=ft_client` so the REST client tests import.

- **Full suite with the removals, the restored exchanges and the ✅ changes in section 4:**
  4785 passed, 3 failed, 23 skipped. The three failures are environmental: `test_startup_time`
  needs the `freqtrade` executable on `PATH`, and the two `test_pip_audit` tests need `pip_audit`
  installed.
- **Lint:** `ruff check` reports 19 findings, all of which were already present on `improvements`
  in `blofin.py`, `hyperliquid.py` and `test_blofin.py` (mostly line length).
- **Tests added or updated for section 4:** funding window (`test_calculate_funding_fees`,
  `test_backtest_one_detail_futures`, `test_backtest_one_detail_futures_funding_fees`), leverage
  (`test_clamp_leverage`), BloFin dry-run funding, dry-run stoploss fee, liquidation before
  stoploss (`test_ft_stoploss_reached`), entry lookups before the order
  (`test_execute_entry_lookup_failure_places_no_order`), retry delay
  (`test_retrier_delays_temporary_errors`), bot-loop errors
  (`test_worker_process_running_unexpected_error`).
  Also: live candle frame (`test__live_candle_counts`, `test_refresh_latest_ohlcv_live_frame`),
  BloFin candle volume (`test_blofin_candle_volume_is_base_currency`).

Not verified from this branch: a real dry-run or live session. The only live-API check made was
reading two public BloFin candles to confirm which column holds base-currency volume.

---

## 6. FreqUI redesign ✅

The vendored FreqUI (`frequi/`, installed with `freqtrade install-ui --local`) was restructured and
restyled after this fork's Home Assistant Freqtrade app. All existing features are still reachable;
data handling (stores, API calls) is reused, not rewritten.

**Look.** One set of design tokens in `frequi/src/styles/tokens.css`, mapped into the PrimeVue
theme and the chart colours, in dark (default) and light, switchable auto / light / dark:

- Slate backgrounds, panels with a 1px border and no shadow, blue accent.
- IBM Plex Sans for text and IBM Plex Mono for every number, bundled so they work offline.
- Compact 13px density.

**Rules applied everywhere:**

- Profit and loss always carry a sign as well as a colour.
- Live bots carry an amber LIVE badge, dry-run bots a grey DRY-RUN badge.
- Start, stop, pause, reload, force entry and exit, deleting trades and cancelling orders all
  ask for confirmation first.

**Structure:**

- **Top bar:** Overview, one tab per configured bot, and a Tools menu (Backtesting, Pairlist config,
  Download data, Logs, Settings); theme switch, clock, login on the right.
- **Status bar** at the bottom: bots reachable, WebSocket state, bot / UI / API versions.
- **Overview:** Live / Dry-run / All scope, KPI tiles (open trades, open P&L, P&L today, closed P&L,
  win rate, balance), a searchable bots table, balance and profit-per-day charts, open trades across
  bots, cumulative profit and recent activity.
- **Bot page** (`/bot/<id>/<section>`): header with state, mode, strategy and the bot controls, and
  sections Summary, Chart, Trades, Performance, Balance and Bot (status and config, trading rules,
  locks, pairlist, log).
- The draggable grid layouts are replaced by fixed responsive grids; on a phone everything stacks to
  one column and wide tables scroll inside their own box.
- Old paths (`/trade`, `/graph`, `/dashboard`, `/balance`, `/open_trades`, `/trade_history`,
  `/pairlist`) redirect to the matching new page.

**Removed:** the "Enable FreqAI" backtest option and the `/freqaimodels` call (the backend no longer
has FreqAI).

**Checks:**

- Type-check, lint (0 errors; 2 warnings that were already in the custom candle tooltip code), and
  the production build all pass.
- Unit tests: 49 of 49 pass.
- End-to-end tests (Microsoft Edge): 18 of 19 pass. The remaining test compares chart images
  against reference screenshots that only exist for Linux, so it cannot pass on Windows.
- Two end-to-end assertions were made locale-independent. Numbers follow the system number format,
  so this machine (`en-NL`) shows `8070,5` where the Linux CI shows `8070.5`.

**Not verified:** the UI against a real running bot. All checks and screenshots used the mocked API
of the end-to-end tests.