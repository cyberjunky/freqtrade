import logging

import ccxt

from freqtrade.constants import BuySell
from freqtrade.enums import MarginMode, TradingMode
from freqtrade.exceptions import (
    DDosProtection,
    InvalidOrderException,
    OperationalException,
    RetryableOrderError,
    TemporaryError,
)
from freqtrade.exchange import Exchange
from freqtrade.exchange.common import API_FETCH_ORDER_RETRY_COUNT, retrier
from freqtrade.exchange.exchange_types import CcxtBalances, CcxtOrder, FtHas, LeverageTier


logger = logging.getLogger(__name__)


class Blofin(Exchange):
    """BloFin exchange class.

    Contains adjustments needed for Freqtrade to work with BloFin swap trading.
    BloFin only supports perpetual swap markets (no spot, no margin).

    Key differences from standard exchanges:
    - No fetchOrder support — emulated via fetchOpenOrders + fetchClosedOrders
    - No fetchLeverageTiers — derived from market data instead
    - set_leverage requires marginMode parameter
    - set_margin_mode is account-wide (symbol is ignored)
    - fetchBalance requires accountType='futures' for swap balance
    """

    _ft_has: FtHas = {
        "stoploss_on_exchange": False,
        "order_time_in_force": ["GTC", "FOK", "IOC"],
        "ohlcv_candle_limit": 100,
        "trades_has_history": True,
        "ws_enabled": True,
    }

    _ft_has_futures: FtHas = {
        "tickers_have_quoteVolume": True,
        "stoploss_on_exchange": False,
        "funding_fee_candle_limit": 100,
    }

    _supported_trading_mode_margin_pairs: list[tuple[TradingMode, MarginMode]] = [
        (TradingMode.FUTURES, MarginMode.CROSS),
        (TradingMode.FUTURES, MarginMode.ISOLATED),
    ]

    @retrier
    def additional_exchange_init(self) -> None:
        """
        Post-init hook: patch ccxt has dict and set position mode to net (one-way).
        Called after the ccxt API object is ready.
        """
        # BloFin lacks fetchOrder in ccxt, but our override handles it.
        # Patching has prevents freqtrade from routing to the broken emulated path.
        self._api.has["fetchOrder"] = True
        if self._api_async:
            self._api_async.has["fetchOrder"] = True

        if self._config.get("dry_run") or self.trading_mode != TradingMode.FUTURES:
            return

        try:
            # One-way (net) mode: a single position per symbol, direction can flip.
            # This aligns with freqtrade's single-trade-per-pair model.
            res = self._api.set_position_mode(hedged=False)
            self._log_exchange_response("set_position_mode", res)
        except ccxt.ExchangeError as e:
            # BloFin returns an error when the mode is already set — safe to ignore.
            logger.info("BloFin position mode already set to net: %s", e)
        except ccxt.DDoSProtection as e:
            raise DDosProtection(e) from e
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
            params["marginMode"] = self.margin_mode.value  # "isolated" or "cross"
            params["positionSide"] = "net"  # one-way mode — no separate long/short positions
        return params

    @retrier
    def _lev_prep(self, pair: str, leverage: float, side: BuySell, accept_fail: bool = False):
        """
        Set margin mode then leverage before order creation.
        BloFin's set_leverage requires marginMode; base class does not pass it.
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
        for order in orders:
            if str(order["id"]) == str(order_id):
                self._log_exchange_response(label, order)
                return self._order_contracts_to_amount(order)
        return None

    @retrier(retries=API_FETCH_ORDER_RETRY_COUNT)
    def fetch_order(self, order_id: str, pair: str, params: dict | None = None) -> CcxtOrder:
        """
        Fetch a single order by ID.
        BloFin's ccxt has fetchOrder=None; we emulate it by searching
        fetchOpenOrders (active) then fetchClosedOrders (filled/cancelled).
        """
        if self._config["dry_run"]:
            return self.fetch_dry_run_order(order_id)

        try:
            # Pass orderId hint so BloFin API can filter server-side where supported.
            open_orders = self._api.fetch_open_orders(pair, params={"orderId": order_id})
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
            # Fallback: search recent closed/filled orders.
            # limit=100 covers most cases; older orders may be missed.
            closed_orders = self._api.fetch_closed_orders(pair, limit=100)
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

    def load_leverage_tiers(self) -> dict[str, list[dict]]:
        """
        Build leverage tiers from market data.
        BloFin does not support fetchLeverageTiers or fetchMarketLeverageTiers.
        Each market's max leverage is available in market['limits']['leverage']['max'].
        """
        if self.trading_mode != TradingMode.FUTURES:
            return {}

        stake = self._config.get("stake_currency", "USDT")
        tiers: dict[str, list[LeverageTier]] = {}

        for symbol, market in self.markets.items():
            if not self.market_is_future(market):
                continue
            if market.get("quote") != stake:
                continue

            max_lev = float((market.get("limits") or {}).get("leverage", {}).get("max") or 20.0)
            tiers[symbol] = [
                {
                    "minNotional": 0.0,
                    "maxNotional": None,  # No upper cap — BloFin tier is flat
                    "maintenanceMarginRate": 0.005,
                    "maxLeverage": max_lev,
                    "maintAmt": None,
                }
            ]

        logger.info("BloFin: Built leverage tiers for %d swap markets.", len(tiers))
        return tiers

    @retrier
    def get_balances(self, params: dict | None = None) -> CcxtBalances:
        """
        Fetch futures account balance.
        BloFin separates funding and futures balances; we always query the futures account.
        """
        try:
            balances = self._api.fetch_balance({"accountType": "futures"})
            balances.pop("info", None)
            balances.pop("free", None)
            balances.pop("total", None)
            balances.pop("used", None)
            self._log_exchange_response("fetch_balance", balances)
            return balances
        except ccxt.DDoSProtection as e:
            raise DDosProtection(e) from e
        except (ccxt.OperationFailed, ccxt.ExchangeError) as e:
            raise TemporaryError(
                f"Could not get balance due to {e.__class__.__name__}. Message: {e}"
            ) from e
        except ccxt.BaseError as e:
            raise OperationalException(e) from e
