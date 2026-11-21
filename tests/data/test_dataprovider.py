from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from pandas import DataFrame

from freqtrade.data.dataprovider import DataProvider
from freqtrade.enums import CandleType, RunMode
from freqtrade.exceptions import ExchangeError, OperationalException
from freqtrade.plugins.pairlistmanager import PairListManager
from freqtrade.util import dt_utc
from tests.conftest import EXMS, get_patched_exchange, log_has_re


@pytest.mark.parametrize(
    "candle_type",
    [
        "mark",
        "",
    ],
)
def test_dp_ohlcv(mocker, default_conf, ohlcv_history, candle_type):
    default_conf["runmode"] = RunMode.DRY_RUN
    timeframe = default_conf["timeframe"]
    exchange = get_patched_exchange(mocker, default_conf)
    candletype = CandleType.from_string(candle_type)
    exchange._klines[("XRP/BTC", timeframe, candletype)] = ohlcv_history
    exchange._klines[("UNITTEST/BTC", timeframe, candletype)] = ohlcv_history

    dp = DataProvider(default_conf, exchange)
    assert dp.runmode == RunMode.DRY_RUN
    assert ohlcv_history.equals(dp.ohlcv("UNITTEST/BTC", timeframe, candle_type=candletype))
    assert isinstance(dp.ohlcv("UNITTEST/BTC", timeframe, candle_type=candletype), DataFrame)
    assert dp.ohlcv("UNITTEST/BTC", timeframe, candle_type=candletype) is not ohlcv_history
    assert dp.ohlcv("UNITTEST/BTC", timeframe, copy=False, candle_type=candletype) is ohlcv_history
    assert not dp.ohlcv("UNITTEST/BTC", timeframe, candle_type=candletype).empty
    assert dp.ohlcv("NONSENSE/AAA", timeframe, candle_type=candletype).empty

    # Test with and without parameter
    assert dp.ohlcv("UNITTEST/BTC", timeframe, candle_type=candletype).equals(
        dp.ohlcv("UNITTEST/BTC", candle_type=candle_type)
    )

    default_conf["runmode"] = RunMode.LIVE
    dp = DataProvider(default_conf, exchange)
    assert dp.runmode == RunMode.LIVE
    assert isinstance(dp.ohlcv("UNITTEST/BTC", timeframe, candle_type=candle_type), DataFrame)

    default_conf["runmode"] = RunMode.BACKTEST
    dp = DataProvider(default_conf, exchange)
    assert dp.runmode == RunMode.BACKTEST
    assert dp.ohlcv("UNITTEST/BTC", timeframe, candle_type=candle_type).empty


def test_historic_ohlcv(mocker, default_conf, ohlcv_history):
    historymock = MagicMock(return_value=ohlcv_history)
    mocker.patch("freqtrade.data.dataprovider.load_pair_history", historymock)

    dp = DataProvider(default_conf, None)
    data = dp.historic_ohlcv("UNITTEST/BTC", "5m")
    assert isinstance(data, DataFrame)
    assert historymock.call_count == 1
    assert historymock.call_args_list[0][1]["timeframe"] == "5m"


def test_historic_trades(mocker, default_conf, trades_history_df):
    historymock = MagicMock(return_value=trades_history_df)
    mocker.patch(
        "freqtrade.data.history.datahandlers.featherdatahandler.FeatherDataHandler._trades_load",
        historymock,
    )

    dp = DataProvider(default_conf, None)
    # Live mode..
    with pytest.raises(OperationalException, match=r"Exchange is not available to DataProvider\."):
        dp.trades("UNITTEST/BTC", "5m")

    exchange = get_patched_exchange(mocker, default_conf)
    dp = DataProvider(default_conf, exchange)
    data = dp.trades("UNITTEST/BTC", "5m")

    assert isinstance(data, DataFrame)
    assert len(data) == 0

    # Switch to backtest mode
    default_conf["runmode"] = RunMode.BACKTEST
    default_conf["dataformat_trades"] = "feather"
    exchange = get_patched_exchange(mocker, default_conf)
    dp = DataProvider(default_conf, exchange)
    data = dp.trades("UNITTEST/BTC", "5m")
    assert isinstance(data, DataFrame)
    assert len(data) == len(trades_history_df)


def test_historic_ohlcv_dataformat(mocker, default_conf, ohlcv_history):
    parquetloadmock = MagicMock(return_value=ohlcv_history)
    featherloadmock = MagicMock(return_value=ohlcv_history)
    mocker.patch(
        "freqtrade.data.history.datahandlers.parquetdatahandler.ParquetDataHandler._ohlcv_load",
        parquetloadmock,
    )
    mocker.patch(
        "freqtrade.data.history.datahandlers.featherdatahandler.FeatherDataHandler._ohlcv_load",
        featherloadmock,
    )

    default_conf["runmode"] = RunMode.BACKTEST
    exchange = get_patched_exchange(mocker, default_conf)
    dp = DataProvider(default_conf, exchange)
    data = dp.historic_ohlcv("UNITTEST/BTC", "5m")
    assert isinstance(data, DataFrame)
    parquetloadmock.assert_not_called()
    featherloadmock.assert_called_once()

    # Switching to dataformat parquet
    parquetloadmock.reset_mock()
    featherloadmock.reset_mock()
    default_conf["dataformat_ohlcv"] = "parquet"
    dp = DataProvider(default_conf, exchange)
    data = dp.historic_ohlcv("UNITTEST/BTC", "5m")
    assert isinstance(data, DataFrame)
    parquetloadmock.assert_called_once()
    featherloadmock.assert_not_called()


@pytest.mark.parametrize(
    "candle_type",
    [
        "mark",
        "futures",
        "",
    ],
)
def test_get_pair_dataframe(mocker, default_conf, ohlcv_history, candle_type):
    default_conf["runmode"] = RunMode.DRY_RUN
    timeframe = default_conf["timeframe"]
    exchange = get_patched_exchange(mocker, default_conf)
    candletype = CandleType.from_string(candle_type)
    exchange._klines[("XRP/BTC", timeframe, candletype)] = ohlcv_history
    exchange._klines[("UNITTEST/BTC", timeframe, candletype)] = ohlcv_history

    dp = DataProvider(default_conf, exchange)
    assert dp.runmode == RunMode.DRY_RUN
    assert ohlcv_history.equals(
        dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candle_type)
    )
    assert ohlcv_history.equals(
        dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candletype)
    )
    assert isinstance(
        dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candle_type), DataFrame
    )
    assert (
        dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candle_type)
        is not ohlcv_history
    )
    assert not dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candle_type).empty
    assert dp.get_pair_dataframe("NONSENSE/AAA", timeframe, candle_type=candle_type).empty

    # Test with and without parameter
    assert dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candle_type).equals(
        dp.get_pair_dataframe("UNITTEST/BTC", candle_type=candle_type)
    )

    default_conf["runmode"] = RunMode.LIVE
    dp = DataProvider(default_conf, exchange)
    assert dp.runmode == RunMode.LIVE
    assert isinstance(
        dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candle_type), DataFrame
    )
    assert dp.get_pair_dataframe("NONSENSE/AAA", timeframe, candle_type=candle_type).empty

    historymock = MagicMock(return_value=ohlcv_history)
    mocker.patch("freqtrade.data.dataprovider.load_pair_history", historymock)
    default_conf["runmode"] = RunMode.BACKTEST
    dp = DataProvider(default_conf, exchange)
    assert dp.runmode == RunMode.BACKTEST
    df = dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candle_type)
    assert isinstance(df, DataFrame)
    assert len(df) == 3  # ohlcv_history mock has just 3 rows

    dp._set_dataframe_max_date(ohlcv_history.iloc[-1]["date"])
    df = dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type=candle_type)
    assert isinstance(df, DataFrame)
    assert len(df) == 2  # ohlcv_history is limited to 2 rows now


def test_get_pair_dataframe_funding_rate(mocker, default_conf, ohlcv_history, caplog):
    default_conf["runmode"] = RunMode.DRY_RUN
    timeframe = "1h"
    exchange = get_patched_exchange(mocker, default_conf)
    candletype = CandleType.FUNDING_RATE
    # Funding rate data carries a single value, plus "open" as backwards-compat alias
    funding_history = DataFrame(
        {
            "date": ohlcv_history["date"],
            "funding_rate": ohlcv_history["open"],
            "open": ohlcv_history["open"],
        }
    )
    exchange._klines[("XRP/BTC", timeframe, candletype)] = funding_history
    exchange._klines[("UNITTEST/BTC", timeframe, candletype)] = funding_history

    dp = DataProvider(default_conf, exchange)
    assert dp.runmode == RunMode.DRY_RUN
    res = dp.get_pair_dataframe("UNITTEST/BTC", timeframe, candle_type="funding_rate")
    assert funding_history.equals(res)
    assert list(res.columns) == ["date", "funding_rate", "open"]
    msg = r".*funding rate timeframe not matching"
    assert not log_has_re(msg, caplog)

    assert funding_history.equals(
        dp.get_pair_dataframe("UNITTEST/BTC", "5h", candle_type="funding_rate")
    )
    assert log_has_re(msg, caplog)


def test_available_pairs(mocker, default_conf, ohlcv_history):
    exchange = get_patched_exchange(mocker, default_conf)
    timeframe = default_conf["timeframe"]
    exchange._klines[("XRP/BTC", timeframe)] = ohlcv_history
    exchange._klines[("UNITTEST/BTC", timeframe)] = ohlcv_history

    dp = DataProvider(default_conf, exchange)
    assert len(dp.available_pairs) == 2
    assert dp.available_pairs == [
        ("XRP/BTC", timeframe),
        ("UNITTEST/BTC", timeframe),
    ]


def test_emit_df(mocker, default_conf, ohlcv_history):
    mocker.patch("freqtrade.rpc.rpc_manager.RPCManager.__init__", MagicMock())
    rpc_mock = mocker.patch("freqtrade.rpc.rpc_manager.RPCManager", MagicMock())
    send_mock = mocker.patch("freqtrade.rpc.rpc_manager.RPCManager.send_msg", MagicMock())

    dataprovider = DataProvider(default_conf, exchange=None, rpc=rpc_mock)
    dataprovider_no_rpc = DataProvider(default_conf, exchange=None)

    pair = "BTC/USDT"

    # No emit yet
    assert send_mock.call_count == 0

    # Rpc is added, we call emit, should call send_msg
    dataprovider._emit_df(pair, ohlcv_history, False)
    assert send_mock.call_count == 1

    send_mock.reset_mock()
    dataprovider._emit_df(pair, ohlcv_history, True)
    assert send_mock.call_count == 2

    send_mock.reset_mock()

    # No rpc added, emit called, should not call send_msg
    dataprovider_no_rpc._emit_df(pair, ohlcv_history, False)
    assert send_mock.call_count == 0


def test_refresh(mocker, default_conf):
    refresh_mock = mocker.patch(f"{EXMS}.refresh_latest_ohlcv")
    mock_refresh_trades = mocker.patch(f"{EXMS}.refresh_latest_trades")

    exchange = get_patched_exchange(mocker, default_conf, exchange="binance")
    timeframe = default_conf["timeframe"]
    pairs = [("XRP/BTC", timeframe), ("UNITTEST/BTC", timeframe)]

    pairs_non_trad = [("ETH/USDT", timeframe), ("BTC/TUSD", "1h")]

    dp = DataProvider(default_conf, exchange)
    dp.refresh(pairs)
    assert mock_refresh_trades.call_count == 0
    assert refresh_mock.call_count == 1
    assert len(refresh_mock.call_args[0]) == 1
    assert len(refresh_mock.call_args[0][0]) == len(pairs)
    assert refresh_mock.call_args[0][0] == pairs

    refresh_mock.reset_mock()
    dp.refresh(pairs, pairs_non_trad)
    assert mock_refresh_trades.call_count == 0
    assert refresh_mock.call_count == 1
    assert len(refresh_mock.call_args[0]) == 1
    assert len(refresh_mock.call_args[0][0]) == len(pairs) + len(pairs_non_trad)
    assert refresh_mock.call_args[0][0] == pairs + pairs_non_trad

    # Test with public trades
    refresh_mock.reset_mock()
    refresh_mock.reset_mock()
    default_conf["exchange"]["use_public_trades"] = True
    dp.refresh(pairs, pairs_non_trad)
    assert mock_refresh_trades.call_count == 1
    assert refresh_mock.call_count == 1


def test_orderbook(mocker, default_conf, order_book_l2):
    api_mock = MagicMock()
    api_mock.fetch_l2_order_book = order_book_l2
    exchange = get_patched_exchange(mocker, default_conf, api_mock=api_mock)

    dp = DataProvider(default_conf, exchange)
    res = dp.orderbook("ETH/BTC", 5)
    assert order_book_l2.call_count == 1
    assert order_book_l2.call_args_list[0][0][0] == "ETH/BTC"
    assert order_book_l2.call_args_list[0][0][1] >= 5

    assert isinstance(res, dict)
    assert "bids" in res
    assert "asks" in res


def test_market(mocker, default_conf, markets):
    api_mock = MagicMock()
    api_mock.markets = markets
    exchange = get_patched_exchange(mocker, default_conf, api_mock=api_mock)

    dp = DataProvider(default_conf, exchange)
    res = dp.market("ETH/BTC")

    assert isinstance(res, dict)
    assert "symbol" in res
    assert res["symbol"] == "ETH/BTC"

    res = dp.market("UNITTEST/BTC")
    assert res is None


def test_ticker(mocker, default_conf, tickers):
    ticker_mock = MagicMock(return_value=tickers()["ETH/BTC"])
    mocker.patch(f"{EXMS}.fetch_ticker", ticker_mock)
    exchange = get_patched_exchange(mocker, default_conf)
    dp = DataProvider(default_conf, exchange)
    res = dp.ticker("ETH/BTC")
    assert isinstance(res, dict)
    assert "symbol" in res
    assert res["symbol"] == "ETH/BTC"

    ticker_mock = MagicMock(side_effect=ExchangeError("Pair not found"))
    mocker.patch(f"{EXMS}.fetch_ticker", ticker_mock)
    exchange = get_patched_exchange(mocker, default_conf)
    dp = DataProvider(default_conf, exchange)
    res = dp.ticker("UNITTEST/BTC")
    assert res == {}


def test_current_whitelist(mocker, default_conf, tickers):
    # patch default conf to volumepairlist
    default_conf["pairlists"][0] = {"method": "VolumePairList", "number_assets": 5}

    mocker.patch.multiple(EXMS, exchange_has=MagicMock(return_value=True), get_tickers=tickers)
    exchange = get_patched_exchange(mocker, default_conf)

    pairlist = PairListManager(exchange, default_conf)
    dp = DataProvider(default_conf, exchange, pairlist)

    # Simulate volumepairs from exchange.
    pairlist.refresh_pairlist()

    assert dp.current_whitelist() == pairlist._whitelist
    # The identity of the 2 lists should not be identical, but a copy
    assert dp.current_whitelist() is not pairlist._whitelist

    with pytest.raises(OperationalException):
        dp = DataProvider(default_conf, exchange)
        dp.current_whitelist()


def test_get_analyzed_dataframe(mocker, default_conf, ohlcv_history):
    default_conf["runmode"] = RunMode.DRY_RUN

    timeframe = default_conf["timeframe"]
    exchange = get_patched_exchange(mocker, default_conf)

    dp = DataProvider(default_conf, exchange)
    dp._set_cached_df("XRP/BTC", timeframe, ohlcv_history, CandleType.SPOT)
    dp._set_cached_df("UNITTEST/BTC", timeframe, ohlcv_history, CandleType.SPOT)

    assert dp.runmode == RunMode.DRY_RUN
    dataframe, time = dp.get_analyzed_dataframe("UNITTEST/BTC", timeframe)
    assert ohlcv_history.equals(dataframe)
    assert isinstance(time, datetime)

    dataframe, time = dp.get_analyzed_dataframe("XRP/BTC", timeframe)
    assert ohlcv_history.equals(dataframe)
    assert isinstance(time, datetime)

    dataframe, time = dp.get_analyzed_dataframe("NOTHING/BTC", timeframe)
    assert dataframe.empty
    assert isinstance(time, datetime)
    assert time == datetime(1970, 1, 1, tzinfo=UTC)

    # Test backtest mode
    default_conf["runmode"] = RunMode.BACKTEST
    dp._set_dataframe_max_index("XRP/BTC", 1)
    dataframe, time = dp.get_analyzed_dataframe("XRP/BTC", timeframe)

    assert len(dataframe) == 1

    dp._set_dataframe_max_index("XRP/BTC", 2)
    dataframe, time = dp.get_analyzed_dataframe("XRP/BTC", timeframe)
    assert len(dataframe) == 2

    dp._set_dataframe_max_index("XRP/BTC", 3)
    dataframe, time = dp.get_analyzed_dataframe("XRP/BTC", timeframe)
    assert len(dataframe) == 3

    dp._set_dataframe_max_index("XRP/BTC", 500)
    dataframe, time = dp.get_analyzed_dataframe("XRP/BTC", timeframe)
    assert len(dataframe) == len(ohlcv_history)


def test_no_exchange_mode(default_conf):
    dp = DataProvider(default_conf, None)

    message = "Exchange is not available to DataProvider."

    with pytest.raises(OperationalException, match=message):
        dp.refresh([()])

    with pytest.raises(OperationalException, match=message):
        dp.ohlcv("XRP/USDT", "5m", "")

    with pytest.raises(OperationalException, match=message):
        dp.market("XRP/USDT")

    with pytest.raises(OperationalException, match=message):
        dp.ticker("XRP/USDT")

    with pytest.raises(OperationalException, match=message):
        dp.orderbook("XRP/USDT", 20)

    with pytest.raises(OperationalException, match=message):
        dp.available_pairs()

    with pytest.raises(OperationalException, match=message):
        dp.funding_rate("XRP/USDT:USDT")

    with pytest.raises(OperationalException, match=message):
        dp.check_delisting("XRP/USDT")


def test_dp_send_msg(default_conf):
    default_conf["runmode"] = RunMode.DRY_RUN

    default_conf["timeframe"] = "1h"
    dp = DataProvider(default_conf, None)
    msg = "Test message"
    dp.send_msg(msg)

    assert msg in dp._msg_queue
    dp._msg_queue.pop()
    assert msg not in dp._msg_queue
    # Message is not resent due to caching
    dp.send_msg(msg)
    assert msg not in dp._msg_queue
    dp.send_msg(msg, always_send=True)
    assert msg in dp._msg_queue

    default_conf["runmode"] = RunMode.BACKTEST
    dp = DataProvider(default_conf, None)
    dp.send_msg(msg, always_send=True)
    assert msg not in dp._msg_queue


def test_check_delisting(mocker, default_conf_usdt):
    delist_mock = MagicMock(return_value=None)
    exchange = get_patched_exchange(mocker, default_conf_usdt)
    mocker.patch.object(exchange, "check_delisting_time", delist_mock)
    dp = DataProvider(default_conf_usdt, exchange)
    res = dp.check_delisting("ETH/USDT")
    assert res is None
    assert delist_mock.call_count == 1

    delist_mock2 = MagicMock(return_value=dt_utc(2025, 10, 2))
    mocker.patch.object(exchange, "check_delisting_time", delist_mock2)
    res = dp.check_delisting("XRP/USDT")
    assert res == dt_utc(2025, 10, 2)

    assert delist_mock2.call_count == 1
