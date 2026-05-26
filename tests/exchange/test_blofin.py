from datetime import UTC, datetime
from unittest.mock import MagicMock, PropertyMock

import ccxt
import pytest

from freqtrade.enums import MarginMode, TradingMode
from freqtrade.exceptions import (
    InvalidOrderException,
    OperationalException,
    RetryableOrderError,
    TemporaryError,
)
from tests.conftest import EXMS, get_patched_exchange, log_has_re
from tests.exchange.test_exchange import ccxt_exceptionhandlers


# ─── ccxt has-dict patch (pre-validation) ────────────────────────────────


def test_blofin_ccxt_has_fetchorder_patched():
    """
    Importing freqtrade.exchange.blofin must patch ccxt's blofin so that
    fetchOrder=True is advertised on every new instance. Without this,
    freqtrade's check_exchange() rejects the exchange before our class
    can take over.
    """
    import ccxt

    import freqtrade.exchange.blofin  # noqa: F401  # ensure import-time patch ran

    assert ccxt.blofin().has["fetchOrder"] is True
    # async_support must be patched too — check_exchange uses ccxt.pro/async
    import ccxt.async_support

    assert ccxt.async_support.blofin().has["fetchOrder"] is True


# ─── additional_exchange_init ────────────────────────────────────────────


def test_additional_exchange_init_blofin(default_conf, mocker, caplog):
    """Live futures init: patches has flag + sets one-way position mode."""
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = TradingMode.FUTURES
    default_conf["margin_mode"] = MarginMode.ISOLATED
    api_mock = MagicMock()
    api_mock.has = {}
    api_mock.set_position_mode = MagicMock(return_value={"positionMode": "net_mode"})

    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)

    assert exchange._api.has["fetchOrder"] is True
    api_mock.set_position_mode.assert_called_once_with(hedged=False)


def test_blofin_init_dry_run_skips_position_mode(default_conf, mocker):
    """Dry-run still patches has flag but skips the live position-mode call."""
    default_conf["dry_run"] = True
    default_conf["trading_mode"] = TradingMode.FUTURES
    default_conf["margin_mode"] = MarginMode.ISOLATED
    api_mock = MagicMock()
    api_mock.has = {}
    api_mock.set_position_mode = MagicMock()

    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)

    api_mock.set_position_mode.assert_not_called()
    assert exchange._api.has["fetchOrder"] is True


def test_blofin_init_already_set_swallowed(default_conf, mocker, caplog):
    """ExchangeError matching 'already set' hint is logged at INFO, not raised."""
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = TradingMode.FUTURES
    default_conf["margin_mode"] = MarginMode.ISOLATED
    api_mock = MagicMock()
    api_mock.has = {}
    api_mock.set_position_mode = MagicMock(
        side_effect=ccxt.ExchangeError("Position mode is already net_mode")
    )

    get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)
    assert log_has_re(r"BloFin position mode already set", caplog)


def test_blofin_init_real_error_surfaces(default_conf, mocker):
    """An unrelated ExchangeError must NOT be silently swallowed."""
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = TradingMode.FUTURES
    default_conf["margin_mode"] = MarginMode.ISOLATED
    api_mock = MagicMock()
    api_mock.has = {}
    api_mock.set_position_mode = MagicMock(
        side_effect=ccxt.ExchangeError("Auth failed: invalid api key")
    )
    with pytest.raises(TemporaryError, match="Could not set position mode"):
        get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)


def test_additional_exchange_init_exception_blofin(default_conf, mocker):
    """ccxt exception handler coverage for additional_exchange_init."""
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = TradingMode.FUTURES
    default_conf["margin_mode"] = MarginMode.ISOLATED
    api_mock = MagicMock()
    api_mock.has = {}
    ccxt_exceptionhandlers(
        mocker,
        default_conf,
        api_mock,
        "blofin",
        "additional_exchange_init",
        "set_position_mode",
    )


# ─── _ccxt_config ────────────────────────────────────────────────────────


def test_blofin_ccxt_config_futures_pins_swap(default_conf, mocker):
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    cfg = exchange._ccxt_config
    assert cfg["options"]["defaultType"] == "swap"


# ─── _get_params ─────────────────────────────────────────────────────────


def test_blofin_get_params_futures(default_conf, mocker):
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    params = exchange._get_params(
        side="buy", ordertype="limit", leverage=5.0, reduceOnly=False
    )
    assert params["marginMode"] == "isolated"
    assert params["positionSide"] == "net"


def test_blofin_get_params_spot_unmodified(default_conf, mocker):
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    params = exchange._get_params(
        side="buy", ordertype="limit", leverage=1.0, reduceOnly=False
    )
    assert "marginMode" not in params
    assert "positionSide" not in params


def test_blofin_get_params_passes_time_in_force(default_conf, mocker):
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    params = exchange._get_params(
        side="buy", ordertype="limit", leverage=5.0, reduceOnly=False, time_in_force="IOC"
    )
    # base class still drives timeInForce
    assert params.get("timeInForce") == "IOC"
    assert params["marginMode"] == "isolated"


# ─── _lev_prep ───────────────────────────────────────────────────────────


def test_blofin_lev_prep(default_conf, mocker):
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    api_mock = MagicMock()
    api_mock.has = {"setLeverage": True}
    api_mock.set_leverage = MagicMock(return_value={"leverage": 5})

    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)
    exchange.set_margin_mode = MagicMock()
    mocker.patch.object(exchange, "exchange_has", return_value=True)

    exchange._lev_prep("BTC/USDT:USDT", 5, "buy")

    exchange.set_margin_mode.assert_called_once()
    api_mock.set_leverage.assert_called_once_with(
        leverage=5, symbol="BTC/USDT:USDT", params={"marginMode": "isolated"}
    )


def test_blofin_lev_prep_dry_run_noop(default_conf, mocker):
    default_conf["dry_run"] = True
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    api_mock = MagicMock()
    api_mock.set_leverage = MagicMock()
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)
    exchange._lev_prep("BTC/USDT:USDT", 5, "buy")
    api_mock.set_leverage.assert_not_called()


def test_blofin_lev_prep_spot_noop(default_conf, mocker):
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = "spot"
    api_mock = MagicMock()
    api_mock.set_leverage = MagicMock()
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)
    exchange._lev_prep("BTC/USDT", 1, "buy")
    api_mock.set_leverage.assert_not_called()


def test_blofin_lev_prep_accept_fail_swallows(default_conf, mocker):
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    api_mock = MagicMock()
    api_mock.has = {"setLeverage": True}
    api_mock.set_leverage = MagicMock(side_effect=ccxt.BadRequest("invalid leverage"))
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)
    exchange.set_margin_mode = MagicMock()
    mocker.patch.object(exchange, "exchange_has", return_value=True)

    # accept_fail=True: no exception (BadRequest absorbed)
    exchange._lev_prep("BTC/USDT:USDT", 5, "buy", accept_fail=True)

    # accept_fail=False: raises TemporaryError
    with pytest.raises(TemporaryError, match="Could not set leverage"):
        exchange._lev_prep("BTC/USDT:USDT", 5, "buy", accept_fail=False)


# ─── fetch_order ─────────────────────────────────────────────────────────


def test_blofin_fetch_order_finds_in_open(default_conf, mocker, limit_order):
    default_conf["dry_run"] = False
    api_mock = MagicMock()
    api_mock.fetch_open_orders = MagicMock(
        return_value=[{**limit_order["buy"], "id": "abc"}]
    )
    api_mock.fetch_closed_orders = MagicMock()
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)

    order = exchange.fetch_order("abc", "BTC/USDT:USDT")
    assert order["id"] == "abc"
    api_mock.fetch_closed_orders.assert_not_called()
    # orderId hint passed to open lookup
    _, kwargs = api_mock.fetch_open_orders.call_args
    assert kwargs["params"] == {"orderId": "abc"}


def test_blofin_fetch_order_falls_through_to_closed(default_conf, mocker, limit_order):
    """H3: orderId filter must be applied to the closed-orders query too."""
    default_conf["dry_run"] = False
    api_mock = MagicMock()
    api_mock.fetch_open_orders = MagicMock(return_value=[])
    api_mock.fetch_closed_orders = MagicMock(
        return_value=[{**limit_order["buy"], "id": "abc"}]
    )
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)

    order = exchange.fetch_order("abc", "BTC/USDT:USDT")
    assert order["id"] == "abc"
    args, kwargs = api_mock.fetch_closed_orders.call_args
    assert args[0] == "BTC/USDT:USDT"
    assert kwargs.get("limit") == 100
    assert kwargs.get("params") == {"orderId": "abc"}


def test_blofin_fetch_order_not_found_raises_retryable(default_conf, mocker):
    default_conf["dry_run"] = False
    api_mock = MagicMock()
    api_mock.fetch_open_orders = MagicMock(return_value=[])
    api_mock.fetch_closed_orders = MagicMock(return_value=[])
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)
    with pytest.raises(RetryableOrderError, match=r"not found on BloFin"):
        exchange.fetch_order("missing", "BTC/USDT:USDT")


def test_blofin_fetch_order_invalid_raises_invalid_order(default_conf, mocker):
    default_conf["dry_run"] = False
    api_mock = MagicMock()
    api_mock.fetch_open_orders = MagicMock(side_effect=ccxt.InvalidOrder("bad id"))
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)
    with pytest.raises(InvalidOrderException, match="Invalid order lookup"):
        exchange.fetch_order("abc", "BTC/USDT:USDT")


def test_blofin_fetch_order_dry_run_uses_simulator(default_conf, mocker):
    default_conf["dry_run"] = True
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    exchange.fetch_dry_run_order = MagicMock(return_value={"id": "sim-1"})
    out = exchange.fetch_order("sim-1", "BTC/USDT:USDT")
    assert out["id"] == "sim-1"
    exchange.fetch_dry_run_order.assert_called_once_with("sim-1")


# ─── load_leverage_tiers ─────────────────────────────────────────────────


def test_blofin_load_leverage_tiers_parses_info(default_conf, mocker, caplog):
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    default_conf["stake_currency"] = "USDT"
    markets = {
        "BTC/USDT:USDT": {
            "quote": "USDT",
            "swap": True,
            "spot": False,
            "limits": {"leverage": {"max": 100}},
            "info": {"maintMarginRate": "0.005"},
        },
        "ALT/USDT:USDT": {
            "quote": "USDT",
            "swap": True,
            "spot": False,
            "limits": {"leverage": {"max": None}},
            "info": {},
        },
        "ETH/USDC:USDC": {
            "quote": "USDC",  # wrong stake — should be filtered
            "swap": True,
            "spot": False,
            "limits": {"leverage": {"max": 50}},
            "info": {},
        },
    }
    exchange = get_patched_exchange(
        mocker, default_conf, exchange="blofin", mock_markets=markets
    )
    mocker.patch.object(exchange, "market_is_future", return_value=True)

    tiers = exchange.load_leverage_tiers()

    # USDC pair filtered out (wrong stake currency)
    assert "ETH/USDC:USDC" not in tiers
    # BTC: rate parsed from info, leverage from limits
    btc = tiers["BTC/USDT:USDT"][0]
    assert btc["maintenanceMarginRate"] == 0.005
    assert btc["maxLeverage"] == 100.0
    assert btc["maintAmt"] is None
    assert btc["maxNotional"] is None
    assert btc["minNotional"] == 0.0
    # ALT: missing leverage → 1.0 fallback + warning; missing mm → default
    alt = tiers["ALT/USDT:USDT"][0]
    assert alt["maxLeverage"] == 1.0
    assert alt["maintenanceMarginRate"] == 0.02  # _DEFAULT_MAINT_MARGIN_RATE
    assert log_has_re(r"BloFin: 1 markets without leverage info", caplog)


def test_blofin_load_leverage_tiers_spot_returns_empty(default_conf, mocker):
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    # spot mode (default in default_conf)
    assert exchange.load_leverage_tiers() == {}


def test_blofin_extract_maint_margin_rate_synonyms(default_conf, mocker):
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    # maintMarginRate
    assert exchange._extract_maint_margin_rate({"info": {"maintMarginRate": "0.01"}}) == 0.01
    # maintenanceMarginRate
    assert (
        exchange._extract_maint_margin_rate({"info": {"maintenanceMarginRate": 0.015}}) == 0.015
    )
    # mmr
    assert exchange._extract_maint_margin_rate({"info": {"mmr": "0.02"}}) == 0.02
    # garbage values fall back to default
    assert (
        exchange._extract_maint_margin_rate({"info": {"maintMarginRate": "nope"}})
        == exchange._DEFAULT_MAINT_MARGIN_RATE
    )
    assert (
        exchange._extract_maint_margin_rate({"info": {}})
        == exchange._DEFAULT_MAINT_MARGIN_RATE
    )
    # zero is rejected as a sentinel "missing" value
    assert (
        exchange._extract_maint_margin_rate({"info": {"maintMarginRate": "0"}})
        == exchange._DEFAULT_MAINT_MARGIN_RATE
    )


# ─── get_balances ────────────────────────────────────────────────────────


def test_blofin_get_balances_defaults_to_futures(default_conf, mocker):
    default_conf["dry_run"] = False
    api_mock = MagicMock()
    api_mock.fetch_balance = MagicMock(
        return_value={"USDT": {"free": 100.0}, "info": {}, "free": {}, "total": {}, "used": {}}
    )
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)

    result = exchange.get_balances()
    api_mock.fetch_balance.assert_called_once_with({"accountType": "futures"})
    # summary keys stripped, per-currency entry preserved
    assert "info" not in result
    assert "free" not in result
    assert "total" not in result
    assert "used" not in result
    assert result["USDT"]["free"] == 100.0


def test_blofin_get_balances_merges_caller_params(default_conf, mocker):
    """M3: caller-supplied params merge into defaults instead of being discarded."""
    default_conf["dry_run"] = False
    api_mock = MagicMock()
    api_mock.fetch_balance = MagicMock(return_value={"USDT": {"free": 0.0}})
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)

    exchange.get_balances({"foo": "bar"})
    api_mock.fetch_balance.assert_called_once_with({"accountType": "futures", "foo": "bar"})


def test_blofin_get_balances_caller_overrides_account_type(default_conf, mocker):
    """Explicit accountType from caller wins over the default."""
    default_conf["dry_run"] = False
    api_mock = MagicMock()
    api_mock.fetch_balance = MagicMock(return_value={})
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin", api_mock=api_mock)

    exchange.get_balances({"accountType": "funding"})
    api_mock.fetch_balance.assert_called_once_with({"accountType": "funding"})


def test_blofin_get_balances_exception_paths(default_conf, mocker):
    default_conf["dry_run"] = False
    api_mock = MagicMock()
    ccxt_exceptionhandlers(
        mocker,
        default_conf,
        api_mock,
        "blofin",
        "get_balances",
        "fetch_balance",
    )


# ─── get_tickers (quoteVolume fixup) ─────────────────────────────────────


def test_blofin_get_tickers_populates_quote_volume(default_conf, mocker):
    """
    BloFin returns baseVolume in contracts with quoteVolume=None.
    We must compute quoteVolume = baseVolume × contractSize × last.
    """
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    markets = {
        "BTC/USDT:USDT": {
            "symbol": "BTC/USDT:USDT",
            "swap": True,
            "spot": False,
            "quote": "USDT",
            "contractSize": 0.001,
        },
    }
    api_mock = MagicMock()
    api_mock.fetch_tickers = MagicMock(
        return_value={
            "BTC/USDT:USDT": {
                "symbol": "BTC/USDT:USDT",
                "baseVolume": 779574.0,
                "last": 76935.1,
                "quoteVolume": None,
            },
        }
    )
    exchange = get_patched_exchange(
        mocker,
        default_conf,
        exchange="blofin",
        api_mock=api_mock,
        mock_markets=markets,
    )
    mocker.patch.object(exchange, "exchange_has", return_value=True)

    tickers = exchange.get_tickers()
    expected = 779574.0 * 0.001 * 76935.1
    assert abs(tickers["BTC/USDT:USDT"]["quoteVolume"] - expected) < 0.01


def test_blofin_get_tickers_preserves_existing_quote_volume(default_conf, mocker):
    """If ccxt does fill in quoteVolume, we must not overwrite it."""
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    markets = {
        "ETH/USDT:USDT": {
            "symbol": "ETH/USDT:USDT",
            "swap": True,
            "spot": False,
            "quote": "USDT",
            "contractSize": 0.01,
        },
    }
    api_mock = MagicMock()
    api_mock.fetch_tickers = MagicMock(
        return_value={
            "ETH/USDT:USDT": {
                "symbol": "ETH/USDT:USDT",
                "baseVolume": 100.0,
                "last": 3000.0,
                "quoteVolume": 999_999.0,
            },
        }
    )
    exchange = get_patched_exchange(
        mocker,
        default_conf,
        exchange="blofin",
        api_mock=api_mock,
        mock_markets=markets,
    )
    mocker.patch.object(exchange, "exchange_has", return_value=True)

    tickers = exchange.get_tickers()
    assert tickers["ETH/USDT:USDT"]["quoteVolume"] == 999_999.0


def test_blofin_get_tickers_skips_inverse_contracts(default_conf, mocker):
    """Inverse contracts use a reciprocal formula — leave them untouched."""
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    markets = {
        "BTC/USD:USD": {
            "symbol": "BTC/USD:USD",
            "swap": True,
            "spot": False,
            "quote": "USD",
            "contractSize": 100.0,
            "inverse": True,
        },
    }
    api_mock = MagicMock()
    api_mock.fetch_tickers = MagicMock(
        return_value={
            "BTC/USD:USD": {
                "symbol": "BTC/USD:USD",
                "baseVolume": 100.0,
                "last": 50000.0,
                "quoteVolume": None,
            },
        }
    )
    exchange = get_patched_exchange(
        mocker,
        default_conf,
        exchange="blofin",
        api_mock=api_mock,
        mock_markets=markets,
    )
    mocker.patch.object(exchange, "exchange_has", return_value=True)

    tickers = exchange.get_tickers()
    # Must stay None — we don't synthesize values for inverse contracts.
    assert tickers["BTC/USD:USD"]["quoteVolume"] is None


def test_blofin_get_tickers_skips_when_missing_data(default_conf, mocker):
    """Tickers with no last/baseVolume must be left untouched (no crash)."""
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    markets = {
        "X/USDT:USDT": {
            "symbol": "X/USDT:USDT",
            "swap": True,
            "spot": False,
            "quote": "USDT",
            "contractSize": 1.0,
        },
    }
    api_mock = MagicMock()
    api_mock.fetch_tickers = MagicMock(
        return_value={
            "X/USDT:USDT": {
                "symbol": "X/USDT:USDT",
                "baseVolume": None,  # missing
                "last": 1.0,
                "quoteVolume": None,
            },
        }
    )
    exchange = get_patched_exchange(
        mocker,
        default_conf,
        exchange="blofin",
        api_mock=api_mock,
        mock_markets=markets,
    )
    mocker.patch.object(exchange, "exchange_has", return_value=True)

    tickers = exchange.get_tickers()
    assert tickers["X/USDT:USDT"]["quoteVolume"] is None


# ─── get_funding_fees ────────────────────────────────────────────────────


def test_blofin_get_funding_fees_spot_returns_zero(default_conf, mocker):
    """Spot mode: no funding fees, no exchange call."""
    now = datetime.now(UTC)
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    exchange._get_funding_fees_from_exchange = MagicMock()
    result = exchange.get_funding_fees("BTC/USDT:USDT", 1.0, False, now)
    assert result == 0.0
    exchange._get_funding_fees_from_exchange.assert_not_called()


def test_blofin_get_funding_fees_dry_run_returns_zero_silently(default_conf, mocker):
    """
    Dry-run futures: BloFin has no fetchMarkOHLCV so we can't simulate funding.
    Must return 0.0 without calling the exchange or the simulator.
    """
    now = datetime.now(UTC)
    default_conf["dry_run"] = True
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    exchange._get_funding_fees_from_exchange = MagicMock()
    exchange._fetch_and_calculate_funding_fees = MagicMock()
    result = exchange.get_funding_fees("BTC/USDT:USDT", 1.0, False, now)
    assert result == 0.0
    exchange._get_funding_fees_from_exchange.assert_not_called()
    exchange._fetch_and_calculate_funding_fees.assert_not_called()


def test_blofin_get_funding_fees_live_uses_exchange_history(default_conf, mocker):
    """Live futures: read from BloFin's funding history (which ccxt supports)."""
    now = datetime.now(UTC)
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    exchange._get_funding_fees_from_exchange = MagicMock(return_value=2.5)
    result = exchange.get_funding_fees("BTC/USDT:USDT", 1.0, False, now)
    assert result == 2.5
    exchange._get_funding_fees_from_exchange.assert_called_once_with("BTC/USDT:USDT", now)


def test_blofin_get_funding_fees_live_swallows_exchange_error(default_conf, mocker, caplog):
    """Live: ExchangeError logs a warning and returns 0.0."""
    from freqtrade.exceptions import ExchangeError

    now = datetime.now(UTC)
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    exchange._get_funding_fees_from_exchange = MagicMock(
        side_effect=ExchangeError("api boom")
    )
    result = exchange.get_funding_fees("BTC/USDT:USDT", 1.0, False, now)
    assert result == 0.0
    assert log_has_re(r"Could not update funding fees for BTC/USDT:USDT", caplog)


# ─── get_maintenance_ratio_and_amt ───────────────────────────────────────


def test_blofin_maintenance_ratio_from_locally_built_tiers(default_conf, mocker):
    """
    Base class gates this on exchange_has('fetchLeverageTiers') which is False
    for BloFin. Our override must read directly from self._leverage_tiers.
    """
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    exchange._leverage_tiers = {
        "BTC/USDT:USDT": [
            {
                "minNotional": 0.0,
                "maxNotional": None,
                "maintenanceMarginRate": 0.005,
                "maxLeverage": 100.0,
                "maintAmt": None,
            }
        ]
    }

    mm, amt = exchange.get_maintenance_ratio_and_amt("BTC/USDT:USDT", 10_000.0)
    assert mm == 0.005
    assert amt is None


def test_blofin_maintenance_ratio_unknown_pair_returns_default(default_conf, mocker):
    """Pair not in tiers (e.g. wrong quote) → conservative default, no raise."""
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    exchange._leverage_tiers = {}

    mm, amt = exchange.get_maintenance_ratio_and_amt("WTF/USDT:USDT", 1_000.0)
    assert mm == exchange._DEFAULT_MAINT_MARGIN_RATE
    assert amt is None


# ─── dry_run_liquidation_price ───────────────────────────────────────────


def test_blofin_liquidation_price_long(default_conf, mocker):
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    mocker.patch(
        f"{EXMS}.markets",
        PropertyMock(return_value={"BTC/USDT:USDT": {"inverse": False}}),
    )
    mocker.patch.object(exchange, "get_maintenance_ratio_and_amt", return_value=(0.005, None))

    # 100 BTC @ 50000, lev=10:
    #   position_value = 5_000_000
    #   initial_margin = 500_000
    #   maintenance_margin = 25_000
    #   diff_per_contract = (500_000 - 25_000) / 100 = 4750
    #   liq (long) = 50000 - 4750 = 45250
    liq = exchange.dry_run_liquidation_price(
        pair="BTC/USDT:USDT",
        open_rate=50000.0,
        is_short=False,
        amount=100.0,
        stake_amount=500_000.0,
        leverage=10.0,
        wallet_balance=500_000.0,
        open_trades=[],
    )
    assert liq is not None
    assert abs(liq - 45250.0) < 0.01


def test_blofin_liquidation_price_short(default_conf, mocker):
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    mocker.patch(
        f"{EXMS}.markets",
        PropertyMock(return_value={"BTC/USDT:USDT": {"inverse": False}}),
    )
    mocker.patch.object(exchange, "get_maintenance_ratio_and_amt", return_value=(0.005, None))

    liq = exchange.dry_run_liquidation_price(
        pair="BTC/USDT:USDT",
        open_rate=50000.0,
        is_short=True,
        amount=100.0,
        stake_amount=500_000.0,
        leverage=10.0,
        wallet_balance=500_000.0,
        open_trades=[],
    )
    assert liq is not None
    # symmetrical to long: 50000 + 4750 = 54750
    assert abs(liq - 54750.0) < 0.01


def test_blofin_liquidation_price_inverse_rejected(default_conf, mocker):
    default_conf["trading_mode"] = "futures"
    default_conf["margin_mode"] = "isolated"
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    mocker.patch(
        f"{EXMS}.markets",
        PropertyMock(return_value={"BTC/USDT:USDT": {"inverse": True}}),
    )
    mocker.patch.object(exchange, "get_maintenance_ratio_and_amt", return_value=(0.005, None))
    with pytest.raises(OperationalException, match="inverse"):
        exchange.dry_run_liquidation_price(
            pair="BTC/USDT:USDT",
            open_rate=50000.0,
            is_short=False,
            amount=1.0,
            stake_amount=5000.0,
            leverage=10.0,
            wallet_balance=5000.0,
            open_trades=[],
        )


def test_blofin_liquidation_price_spot_rejected(default_conf, mocker):
    exchange = get_patched_exchange(mocker, default_conf, exchange="blofin")
    mocker.patch(
        f"{EXMS}.markets",
        PropertyMock(return_value={"BTC/USDT:USDT": {"inverse": False}}),
    )
    mocker.patch.object(exchange, "get_maintenance_ratio_and_amt", return_value=(0.005, None))
    with pytest.raises(OperationalException, match="isolated futures"):
        exchange.dry_run_liquidation_price(
            pair="BTC/USDT:USDT",
            open_rate=50000.0,
            is_short=False,
            amount=1.0,
            stake_amount=5000.0,
            leverage=10.0,
            wallet_balance=5000.0,
            open_trades=[],
        )


# ─── supported margin pairs ──────────────────────────────────────────────


def test_blofin_only_supports_isolated_futures(default_conf, mocker):
    """H1: cross-margin must NOT be advertised as supported."""
    # Don't let patch_exchange override the class-level supported-modes list.
    exchange = get_patched_exchange(
        mocker, default_conf, exchange="blofin", mock_supported_modes=False
    )
    pairs = exchange._supported_trading_mode_margin_pairs
    assert (TradingMode.FUTURES, MarginMode.ISOLATED) in pairs
    assert (TradingMode.FUTURES, MarginMode.CROSS) not in pairs
    assert (TradingMode.SPOT, MarginMode.NONE) not in pairs
