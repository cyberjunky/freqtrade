from datetime import UTC, datetime

import numpy as np
import pandas as pd

from freqtrade.rpc.rpc import resample_analyzed_dataframe


def _base(n=96, start="2026-11-21 00:00"):
    dates = pd.date_range(start, periods=n, freq="5min", tz=UTC)
    return pd.DataFrame(
        {
            "date": dates,
            "open": np.arange(n, dtype=float),
            "high": np.arange(n, dtype=float) + 0.5,
            "low": np.arange(n, dtype=float) - 0.5,
            "close": np.arange(n, dtype=float) + 0.1,
            "volume": 1.0,
            "rsi_4h": [float(i // 48) for i in range(n)],
            "enter_short": [1 if i == 10 else 0 for i in range(n)],
            "enter_tag": ["x" if i == 10 else None for i in range(n)],
        }
    )


def test_resample_groups_base_candles():
    res = resample_analyzed_dataframe(_base(), "4h")
    assert list(res["date"]) == [
        datetime(2026, 11, 21, 0, tzinfo=UTC),
        datetime(2026, 11, 21, 4, tzinfo=UTC),
    ]
    first = res.iloc[0]
    assert first["open"] == 0 and first["close"] == 47.1
    assert first["high"] == 47.5 and first["low"] == -0.5
    assert first["volume"] == 48
    assert first["enter_short"] == 1 and first["enter_tag"] == "x"
    assert res.iloc[1]["enter_short"] == 0 and res.iloc[1]["rsi_4h"] == 1


def test_resample_uses_exchange_candles_and_keeps_open_candle():
    ohlcv = pd.DataFrame(
        {
            "date": pd.date_range("2026-11-20 16:00", periods=3, freq="4h", tz=UTC),
            "open": [100.0, 101.0, 102.0],
            "high": [110.0, 111.0, 112.0],
            "low": [90.0, 91.0, 92.0],
            "close": [105.0, 106.0, 107.0],
            "volume": [9.0, 9.0, 9.0],
        }
    )
    res = resample_analyzed_dataframe(_base(), "4h", ohlcv)
    assert len(res) == 4  # 16:00, 20:00 without indicators, 00:00 from exchange, 04:00 still open
    assert np.isnan(res.iloc[0]["rsi_4h"])
    assert res.iloc[2]["open"] == 102.0 and res.iloc[2]["enter_short"] == 1
    assert res.iloc[3]["open"] == 48.0


def test_resample_empty():
    assert resample_analyzed_dataframe(pd.DataFrame(columns=["date"]), "4h").empty
