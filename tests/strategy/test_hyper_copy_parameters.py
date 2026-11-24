"""Each strategy instance gets its own parameters, also when a parameter can't be deep-copied
(lite: strategies with CategoricalParameter([ta.SMA, ta.EMA]) or dict.keys() failed to load)."""

import talib.abstract as ta

from freqtrade.strategy.hyper import HyperStrategyMixin
from freqtrade.strategy.parameters import CategoricalParameter, IntParameter


MA_TYPES = {"sma": ta.SMA, "ema": ta.EMA}


class _Strategy(HyperStrategyMixin):
    buy_len = IntParameter(5, 80, default=30, space="buy")
    buy_ma = CategoricalParameter([ta.SMA, ta.EMA], default=ta.SMA, space="buy")
    sell_ma = CategoricalParameter(MA_TYPES.keys(), default="ema", space="sell")


def _copied():
    strategy = _Strategy.__new__(_Strategy)  # only _ft_copy_parameters, not the whole __init__
    strategy._ft_copy_parameters()
    return strategy


def test_uncopyable_parameters_still_load_and_are_the_instances_own():
    strategy = _copied()
    for name in ("buy_len", "buy_ma", "sell_ma"):
        assert getattr(strategy, name) is not getattr(_Strategy, name)
    assert strategy.buy_ma.value is ta.SMA
    assert strategy.sell_ma.value == "ema"


def test_a_value_set_on_one_instance_does_not_leak():
    first, second = _copied(), _copied()
    first.buy_len.value = 50
    first.buy_ma.value = ta.EMA
    assert second.buy_len.value == 30 and second.buy_ma.value is ta.SMA
    assert _Strategy.buy_len.value == 30 and _Strategy.buy_ma.value is ta.SMA
