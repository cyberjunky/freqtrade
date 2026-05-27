"""
BloFin exchange adapter.

BloFin is a perpetual-swap-only futures exchange. This module specialises the
generic :class:`Exchange` for its quirks:

* No native ``fetchOrder`` — emulated via open + closed order lookups.
* No ``fetchLeverageTiers`` — tiers are derived from each market's metadata.
* ``set_leverage`` and order placement require an explicit ``marginMode`` param.
* ``fetch_balance`` must address the ``futures`` account explicitly.
* Position mode is forced to net (one-way) so a pair carries a single position
  whose direction can flip — this matches Freqtrade's trade model.
"""

import logging
from datetime import datetime

import ccxt

from freqtrade.constants import BuySell
from freqtrade.enums import CandleType, MarginMode, TradingMode
from freqtrade.exceptions import (
    DDosProtection,
    ExchangeError,
    InvalidOrderException,
    OperationalException,
    RetryableOrderError,
    TemporaryError,
)
from freqtrade.exchange import Exchange
from freqtrade.exchange.common import API_FETCH_ORDER_RETRY_COUNT, retrier
from freqtrade.exchange.exchange_types import (
    CcxtBalances,
    CcxtOrder,
    FtHas,
    LeverageTier,
    OHLCVResponse,
)
from freqtrade.misc import deep_merge_dicts


logger = logging.getLogger(__name__)


# Substrings that identify the "position mode already configured" error returned
# by BloFin when set_position_mode is called against the current mode. Used to
# distinguish a benign no-op from a real exchange error during init.
_POSITION_MODE_ALREADY_SET_HINTS = (
    "already",
    "position mode",
    "position_mode",
)


def _patch_ccxt_blofin_has() -> None:
    """
    Advertise ``fetchOrder=True`` on every ccxt BloFin instance.

    Freqtrade's :func:`check_exchange.check_exchange` runs
    :func:`validate_exchange` against a raw ccxt instance *before* any
    subclass is instantiated. BloFin's ccxt has ``fetchOrder=None`` (and only
    exposes the plural ``fetchOpenOrders``/``fetchClosedOrders``), so without
    this patch validation rejects the exchange outright with
    ``"missing: fetchOrder"`` — our :meth:`Blofin.additional_exchange_init`
    patch only runs *after* validation, far too late.

    We override ``describe`` (where ccxt assembles ``has``) on all three ccxt
    submodules; the patch is idempotent so re-imports stay no-ops.
    """
    import ccxt as _ccxt_sync

    try:
        import ccxt.async_support as _ccxt_async
    except ImportError:
        _ccxt_async = None  # type: ignore[assignment]
    try:
        import ccxt.pro as _ccxt_pro
    except ImportError:
        _ccxt_pro = None  # type: ignore[assignment]

    def _make_patched(orig):
        def _patched(self):
            desc = orig(self)
            desc.setdefault("has", {})["fetchOrder"] = True
            return desc

        _patched._ft_patched = True  # type: ignore[attr-defined]
        return _patched

    for mod in (_ccxt_sync, _ccxt_async, _ccxt_pro):
        if mod is None:
            continue
        cls = getattr(mod, "blofin", None)
        if cls is None:
            continue
        if getattr(cls.describe, "_ft_patched", False):
            continue
        cls.describe = _make_patched(cls.describe)


_patch_ccxt_blofin_has()


class Blofin(Exchange):
    """BloFin exchange class.

    Contains adjustments needed for Freqtrade to work with BloFin swap trading.
    BloFin only supports perpetual swap markets (no spot, no margin).

    Cross-margin is offered by the exchange but intentionally not declared as
    supported here — our liquidation-price calculation only covers isolated
    margin (see :meth:`dry_run_liquidation_price`).
    """

    _ft_has: FtHas = {
        "stoploss_on_exchange": False,
        "order_time_in_force": ["GTC", "FOK", "IOC"],
        # BloFin's REST candles endpoint accepts up to 1440 per request (default 500);
        # ccxt's hardcoded "max 100" comment is wrong — it forwards whatever we ask.
        # See: https://docs.blofin.com (Public Data → Get Candlesticks).
        "ohlcv_candle_limit": 1440,
        "trades_has_history": True,
        # WS disabled: empirically, candle reuse never succeeds for blofin in a
        # long-running multi-pair bot (confirmed over a 10h live run — every pair
        # falls back to REST on every 5m boundary). ccxt's ohlcv cache accumulates
        # in isolation, but in freqtrade's context the watch tasks cycle
        # (cleanup_expired/_unwatch + reset_connections -> ohlcvs.clear()) and wipe
        # the per-pair history before it reaches the >=2 candles the reuse check
        # needs. Net result with WS on: zero reuse, just connection overhead + log
        # spam. REST fallback already serves correct data, so run REST-only.
        "ws_enabled": False,
    }

    _ft_has_futures: FtHas = {
        "tickers_have_quoteVolume": True,
        "stoploss_on_exchange": False,
        "funding_fee_candle_limit": 100,
    }

    _supported_trading_mode_margin_pairs: list[tuple[TradingMode, MarginMode]] = [
        (TradingMode.FUTURES, MarginMode.ISOLATED),
    ]

    # Conservative default maintenance margin rate when BloFin's market metadata
    # does not expose one. BloFin's published tier-1 rate is 0.5% for majors and
    # up to ~2% for thin alts; 2% errs on the side of an earlier (safer)
    # calculated liquidation price.
    _DEFAULT_MAINT_MARGIN_RATE: float = 0.02

    @property
    def _ccxt_config(self) -> dict:
        # Be explicit about swap mode — ccxt's BloFin currently defaults to swap,
        # but pinning it survives future ccxt default changes.
        config: dict = {}
        if self.trading_mode == TradingMode.FUTURES:
            config.update({"options": {"defaultType": "swap"}})
        return deep_merge_dicts(config, super()._ccxt_config)

    @retrier
    def additional_exchange_init(self) -> None:
        """
        Post-init hook: patch the ccxt ``has`` dict and set position mode to net.

        BloFin's ccxt adapter advertises ``fetchOrder = None`` because the REST
        endpoint does not support fetch-by-id directly. Our :meth:`fetch_order`
        override emulates it, so we flip the ``has`` flag to ``True`` to keep
        Freqtrade's order-handling machinery from routing into the broken path.

        TODO: revisit the ``has["fetchOrder"]`` patch once ccxt gains native
        BloFin fetchOrder support; the emulation can be removed at that point.
        """
        self._api.has["fetchOrder"] = True
        if self._api_async:
            self._api_async.has["fetchOrder"] = True

        if self._config.get("dry_run") or self.trading_mode != TradingMode.FUTURES:
            return

        try:
            res = self._api.set_position_mode(hedged=False)
            self._log_exchange_response("set_position_mode", res)
        except ccxt.DDoSProtection as e:
            raise DDosProtection(e) from e
        except ccxt.ExchangeError as e:
            # Only swallow the "already configured" response — anything else
            # (auth, schema, rate-limit-as-ExchangeError) must surface.
            msg = str(e).lower()
            if any(hint in msg for hint in _POSITION_MODE_ALREADY_SET_HINTS):
                logger.info("BloFin position mode already set to net: %s", e)
            else:
                raise TemporaryError(
                    f"Could not set position mode due to {e.__class__.__name__}. Message: {e}"
                ) from e
        except ccxt.OperationFailed as e:
            raise TemporaryError(
                f"Could not set position mode due to {e.__class__.__name__}. Message: {e}"
            ) from e
        except ccxt.BaseError as e:
            raise OperationalException(e) from e

    def _get_params(
        self,
        side: BuySell,
        ordertype: str,
        leverage: float,
        reduceOnly: bool,
        time_in_force: str = "GTC",
    ) -> dict:
        """Extend base params with BloFin-required futures fields."""
        params = super()._get_params(
            side=side,
            ordertype=ordertype,
            leverage=leverage,
            reduceOnly=reduceOnly,
            time_in_force=time_in_force,
        )
        if self.trading_mode == TradingMode.FUTURES and self.margin_mode:
            params["marginMode"] = self.margin_mode.value  # "isolated"
            params["positionSide"] = "net"  # one-way mode — no split long/short
        return params

    @retrier
    def _lev_prep(self, pair: str, leverage: float, side: BuySell, accept_fail: bool = False):
        """
        Set margin mode then leverage before order creation.

        BloFin's ``set_leverage`` requires the ``marginMode`` param; the base
        class doesn't pass it, so we re-implement here.
        """
        if self.trading_mode == TradingMode.SPOT or self.margin_mode is None:
            return
        if self._config.get("dry_run"):
            return

        # Margin mode is account-wide on BloFin; pair/symbol is accepted but ignored.
        self.set_margin_mode(pair, self.margin_mode, accept_fail)

        if not self.exchange_has("setLeverage"):
            return

        try:
            res = self._api.set_leverage(
                leverage=int(leverage),
                symbol=pair,
                params={"marginMode": self.margin_mode.value},
            )
            self._log_exchange_response("set_leverage", res)
        except ccxt.DDoSProtection as e:
            raise DDosProtection(e) from e
        except (ccxt.BadRequest, ccxt.OperationRejected, ccxt.InsufficientFunds) as e:
            if not accept_fail:
                raise TemporaryError(
                    f"Could not set leverage due to {e.__class__.__name__}. Message: {e}"
                ) from e
        except (ccxt.OperationFailed, ccxt.ExchangeError) as e:
            raise TemporaryError(
                f"Could not set leverage due to {e.__class__.__name__}. Message: {e}"
            ) from e
        except ccxt.BaseError as e:
            raise OperationalException(e) from e

    def _search_order_in_list(
        self, orders: list[CcxtOrder], order_id: str, label: str
    ) -> CcxtOrder | None:
        """Return order from ``orders`` matching ``order_id`` (with amount conversion)."""
        for order in orders:
            if str(order["id"]) == str(order_id):
                self._log_exchange_response(label, order)
                return self._order_contracts_to_amount(order)
        return None

    @retrier(retries=API_FETCH_ORDER_RETRY_COUNT)
    def fetch_order(self, order_id: str, pair: str, params: dict | None = None) -> CcxtOrder:
        """
        Fetch a single order by ID.

        BloFin's ccxt has no working ``fetchOrder``; we emulate it by searching
        ``fetchOpenOrders`` first (most lookups are for live orders), falling
        back to ``fetchClosedOrders``. The ``orderId`` filter is passed to both
        queries so an order can't fall outside the result window under heavy
        activity.
        """
        if self._config["dry_run"]:
            return self.fetch_dry_run_order(order_id)

        filter_params = {"orderId": order_id}

        try:
            open_orders = self._api.fetch_open_orders(pair, params=filter_params)
            if found := self._search_order_in_list(open_orders, order_id, "fetch_order_open"):
                return found
        except ccxt.InvalidOrder as e:
            raise InvalidOrderException(
                f"Invalid order lookup (pair: {pair} id: {order_id}). Message: {e}"
            ) from e
        except ccxt.DDoSProtection as e:
            raise DDosProtection(e) from e
        except (ccxt.OperationFailed, ccxt.ExchangeError) as e:
            raise TemporaryError(
                f"Could not fetch open orders due to {e.__class__.__name__}. Message: {e}"
            ) from e
        except ccxt.BaseError as e:
            raise OperationalException(e) from e

        try:
            # Pass orderId on the closed query too — without it the order can
            # scroll past the limit=100 window during busy periods.
            closed_orders = self._api.fetch_closed_orders(
                pair, limit=100, params=filter_params
            )
            if found := self._search_order_in_list(closed_orders, order_id, "fetch_order_closed"):
                return found
        except ccxt.DDoSProtection as e:
            raise DDosProtection(e) from e
        except (ccxt.OperationFailed, ccxt.ExchangeError) as e:
            raise TemporaryError(
                f"Could not fetch closed orders due to {e.__class__.__name__}. Message: {e}"
            ) from e
        except ccxt.BaseError as e:
            raise OperationalException(e) from e

        raise RetryableOrderError(f"Order {order_id} not found on BloFin for pair {pair}.")

    def _extract_maint_margin_rate(self, market: dict) -> float:
        """
        Extract the maintenance margin rate from a market's metadata.

        BloFin's instruments endpoint exposes ``maintMarginRate`` (and synonyms)
        in ``market['info']``. We probe a few known keys defensively because
        ccxt has renamed the field across versions. Falls back to
        :attr:`_DEFAULT_MAINT_MARGIN_RATE` when nothing usable is found.
        """
        info = market.get("info") or {}
        for key in ("maintMarginRate", "maintenanceMarginRate", "mmr"):
            raw = info.get(key)
            if raw is None:
                continue
            try:
                rate = float(raw)
            except (TypeError, ValueError):
                continue
            if rate > 0:
                return rate
        return self._DEFAULT_MAINT_MARGIN_RATE

    def load_leverage_tiers(self) -> dict[str, list[dict]]:
        """
        Build leverage tiers from market data.

        BloFin does not support ``fetchLeverageTiers`` or
        ``fetchMarketLeverageTiers``. Each market's max leverage is exposed in
        ``market['limits']['leverage']['max']`` and the maintenance margin rate
        is read from ``market['info']`` when present.

        ``maintAmt`` is unavailable on BloFin (no tiered notional schedule), so
        we set it to ``None``; downstream
        :meth:`Exchange.get_maintenance_ratio_and_amt` handles this correctly.

        Markets without a declared max leverage fall back to ``1.0`` and are
        warned about in the logs — silently assuming high leverage can cause
        oversized positions on edge-case symbols.
        """
        if self.trading_mode != TradingMode.FUTURES:
            return {}

        stake = self._config.get("stake_currency", "USDT")
        tiers: dict[str, list[LeverageTier]] = {}
        missing_lev: list[str] = []

        for symbol, market in self.markets.items():
            if not self.market_is_future(market):
                continue
            if market.get("quote") != stake:
                continue

            limits_lev = (market.get("limits") or {}).get("leverage") or {}
            raw_max = limits_lev.get("max")
            if raw_max is None:
                missing_lev.append(symbol)
                max_lev = 1.0
            else:
                max_lev = float(raw_max)

            mm_rate = self._extract_maint_margin_rate(market)

            tiers[symbol] = [
                {
                    "minNotional": 0.0,
                    "maxNotional": None,  # BloFin's schedule is flat — no upper cap
                    "maintenanceMarginRate": mm_rate,
                    "maxLeverage": max_lev,
                    "maintAmt": None,
                }
            ]

        if missing_lev:
            shown = ", ".join(missing_lev[:10])
            ellipsis = "…" if len(missing_lev) > 10 else ""
            logger.warning(
                "BloFin: %d markets without leverage info — defaulted to 1x: %s%s",
                len(missing_lev),
                shown,
                ellipsis,
            )
        logger.info("BloFin: Built leverage tiers for %d swap markets.", len(tiers))
        return tiers

    @retrier
    def get_balances(self, params: dict | None = None) -> CcxtBalances:
        """
        Fetch futures account balance.

        BloFin separates funding and futures wallets; we default to the
        ``futures`` account but merge in caller-supplied params so explicit
        overrides win.
        """
        merged_params = {"accountType": "futures", **(params or {})}
        try:
            balances = self._api.fetch_balance(merged_params)
            balances.pop("info", None)
            balances.pop("free", None)
            balances.pop("total", None)
            balances.pop("used", None)
            self._log_exchange_response("fetch_balance", balances, add_info=merged_params)
            return balances
        except ccxt.DDoSProtection as e:
            raise DDosProtection(e) from e
        except (ccxt.OperationFailed, ccxt.ExchangeError) as e:
            raise TemporaryError(
                f"Could not get balance due to {e.__class__.__name__}. Message: {e}"
            ) from e
        except ccxt.BaseError as e:
            raise OperationalException(e) from e

    def get_tickers(
        self,
        symbols: list[str] | None = None,
        *,
        cached: bool = False,
        market_type: TradingMode | None = None,
    ):
        """
        Wrap the base implementation to populate ``quoteVolume`` on every ticker.

        BloFin reports ``baseVolume`` in *contracts* (not base currency) and leaves
        ``quoteVolume = None``. Freqtrade's VolumePairList sorts by quoteVolume —
        without this fixup every pair is rejected. The correct USDT volume for a
        linear swap is ``baseVolume × contractSize × last``.
        """
        tickers = super().get_tickers(symbols=symbols, cached=cached, market_type=market_type)
        for symbol, ticker in tickers.items():
            if ticker.get("quoteVolume") is not None:
                continue
            base_vol = ticker.get("baseVolume")
            last = ticker.get("last") or ticker.get("close")
            if base_vol is None or last is None:
                continue
            market = self.markets.get(symbol) or {}
            # Linear-only: the formula assumes USDT/USDC-settled perpetuals.
            # Inverse contracts use a reciprocal calc we don't need (freqtrade
            # rejects inverse upstream).
            if market.get("inverse"):
                continue
            try:
                contract_size = float(market.get("contractSize") or 1.0)
                ticker["quoteVolume"] = float(base_vol) * contract_size * float(last)
            except (TypeError, ValueError):
                continue
        return tickers

    # Markers identifying BloFin's Cloudflare challenge / 403 block page. These
    # come back as a full HTML document instead of JSON; we collapse them to a
    # single log line instead of dumping the whole page on every retry.
    _CLOUDFLARE_MARKERS = (
        "_cf_chl",
        "cf-chl",
        "challenge-platform",
        "cloudflare",
        "enable javascript and cookies",
        "restricted countries",
        "403 forbidden",
    )

    def _is_cloudflare_block(self, text: str) -> bool:
        low = text.lower()
        return any(marker in low for marker in self._CLOUDFLARE_MARKERS)

    async def _async_get_candle_history(
        self,
        pair: str,
        timeframe: str,
        candle_type: CandleType,
        since_ms: int | None = None,
    ) -> OHLCVResponse:
        """
        Wrap the base OHLCV fetch to collapse BloFin's Cloudflare 403 challenge
        pages into a single concise log line.

        BloFin sits behind Cloudflare, which intermittently answers the public
        candles endpoint with a full HTML challenge page instead of JSON. The
        base class embeds that entire page in the exception message, flooding
        the log on every retry. We detect the page and re-raise a short
        DDosProtection (retryable, with backoff) so the request still recovers
        once Cloudflare lets it through, without the HTML wall.
        """
        try:
            return await super()._async_get_candle_history(
                pair, timeframe, candle_type, since_ms
            )
        except (DDosProtection, TemporaryError, OperationalException) as e:
            if self._is_cloudflare_block(str(e)):
                raise DDosProtection(
                    f"BloFin OHLCV blocked by Cloudflare (403 challenge) for "
                    f"{pair} {timeframe} {candle_type} — retrying with backoff."
                ) from None
            raise

    def get_funding_fees(
        self, pair: str, amount: float, is_short: bool, open_date: datetime
    ) -> float:
        """
        Return funding fees for a futures position.

        In live mode we read the exchange's funding history directly via ccxt's
        ``fetchFundingHistory`` (which BloFin supports). In dry-run we return
        ``0.0`` silently: BloFin's ccxt does not expose ``fetchMarkOHLCV``, so
        the base-class dry-run path that simulates funding from
        funding-rate × mark-price candles cannot run. Funding is small enough
        relative to PnL that this approximation is acceptable for backtests.
        """
        if self.trading_mode != TradingMode.FUTURES:
            return 0.0
        if self._config.get("dry_run"):
            # No mark OHLCV available on BloFin → can't simulate. Stay quiet.
            return 0.0
        try:
            return self._get_funding_fees_from_exchange(pair, open_date)
        except ExchangeError:
            logger.warning("Could not update funding fees for %s.", pair)
            return 0.0

    def get_maintenance_ratio_and_amt(
        self, pair: str, notional_value: float
    ) -> tuple[float, float | None]:
        """
        Look up maintenance margin from our locally-built leverage tiers.

        The base implementation gates on ``exchange_has("fetchLeverageTiers")``
        and falls through to ``raise ExchangeError`` when the exchange does
        not advertise that capability. BloFin doesn't expose it (we synthesize
        tiers in :meth:`load_leverage_tiers`), so without this override every
        ``get_liquidation_price`` call would log "Unable to calculate
        liquidation price" and silently leave trades with no liquidation
        watchdog — a real risk in live futures trading.
        """
        if pair not in self._leverage_tiers:
            # Pair was filtered out at load time (wrong quote / non-future).
            # Use the conservative default so callers still get a usable value.
            return (self._DEFAULT_MAINT_MARGIN_RATE, None)

        pair_tiers = self._leverage_tiers[pair]
        for tier in reversed(pair_tiers):
            if notional_value >= tier["minNotional"]:
                return (tier["maintenanceMarginRate"], tier["maintAmt"])
        # minNotional=0 is guaranteed by load_leverage_tiers, so this is
        # unreachable in practice — but stay defensive.
        first = pair_tiers[0]
        return (first["maintenanceMarginRate"], first["maintAmt"])

    def dry_run_liquidation_price(
        self,
        pair: str,
        open_rate: float,
        is_short: bool,
        amount: float,
        stake_amount: float,
        leverage: float,
        wallet_balance: float,
        open_trades: list,
    ) -> float | None:
        """
        Compute an isolated-perpetual liquidation price for dry-run/backtest.

        Reference: BloFin "Risk Management → Liquidation" docs. The USDT-margined
        formula matches Bybit's USDT formula:

            Long:  liq = open_rate - (initial_margin - maintenance_margin) / amount
            Short: liq = open_rate + (initial_margin - maintenance_margin) / amount

        Extra margin top-ups are not modelled here — callers should treat the
        returned value as the liquidation price for the original collateral only.
        Inverse contracts are not supported.

        :param pair: Pair to calculate liquidation price for
        :param open_rate: Entry price of the position
        :param is_short: ``True`` for short positions
        :param amount: Position size in base currency (leverage already applied)
        :param stake_amount: Collateral in settle currency
        :param leverage: Leverage used for this position
        :param wallet_balance: Wallet/margin balance backing this position
        :param open_trades: Other open trades sharing the wallet (unused for isolated)
        """
        market = self.markets[pair]
        mm_ratio, _ = self.get_maintenance_ratio_and_amt(pair, stake_amount)

        if self.trading_mode != TradingMode.FUTURES or self.margin_mode != MarginMode.ISOLATED:
            raise OperationalException(
                "Freqtrade only supports isolated futures for leverage trading"
            )
        if market.get("inverse"):
            raise OperationalException("Freqtrade does not yet support inverse contracts")

        position_value = amount * open_rate
        initial_margin = position_value / leverage
        maintenance_margin = position_value * mm_ratio
        margin_diff_per_contract = (initial_margin - maintenance_margin) / amount

        if is_short:
            return open_rate + margin_diff_per_contract
        return open_rate - margin_diff_per_contract
