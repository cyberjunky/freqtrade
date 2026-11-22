"""
PercentChangeFilter — rejects pairs whose 24h ticker change is outside a band.

From the CryptoCoiners trading notes (cryptocoiners/Mijn Trade regels volgens CC.docx):
  "Instappen als: 24h Change tussen -1% en +10%."
and cryptocoiners/stappenplan stijging en daling trade.docx:
  "Munt mag niet meer dan 10% gestegen zijn in de laatste 24h"
  "Munt negatief in de laatste 24h niet handelen"

Neither bot functions 2.pdf nor the CryptoCoiners strategy implement this gate —
entries are only filtered on BB/Stoch/MFI for the trade pair itself, with nothing
rejecting a coin that already pumped/dumped hard over the last 24h. This plugin
fills that gap at the pairlist level, same layer as the existing AgeFilter/
PriceFilter (which the PDF's "pair filters" box also places outside the strategy).

Uses ccxt ticker's 'percentage' field (live 24h change) — not available during
backtesting, so this only takes effect in dry-run/live.
"""

import logging

from freqtrade.exchange.exchange_types import Ticker, Tickers
from freqtrade.plugins.pairlist.IPairList import IPairList, PairlistParameter, SupportsBacktesting


logger = logging.getLogger(f"freqtrade.plugins.pairlist.{__name__}")


class PercentChangeFilter(IPairList):
    """Keeps pairs whose 24h ticker change % falls within [min_change, max_change]."""

    supports_backtesting = SupportsBacktesting.NO

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._min_change: float = self._pairlistconfig.get("min_change", -1.0)
        self._max_change: float = self._pairlistconfig.get("max_change", 10.0)

    @property
    def needstickers(self) -> bool:
        return True

    def short_desc(self) -> str:
        return f"{self.name} - 24h change between {self._min_change:.1f}% and {self._max_change:.1f}%."

    @staticmethod
    def description() -> str:
        return "Filter pairs by 24h percentage change."

    @staticmethod
    def available_parameters() -> dict[str, PairlistParameter]:
        return {
            "min_change": {
                "type": "number",
                "default": -1.0,
                "description": "Min 24h Change %",
                "help": "Reject pairs whose 24h change is below this (e.g. -1.0 = -1%).",
            },
            "max_change": {
                "type": "number",
                "default": 10.0,
                "description": "Max 24h Change %",
                "help": "Reject pairs whose 24h change is above this (e.g. 10.0 = +10%).",
            },
        }

    def filter_pairlist(self, pairlist: list[str], tickers: Tickers) -> list[str]:
        return [pair for pair in pairlist if self._validate_pair(pair, tickers.get(pair))]

    def _validate_pair(self, pair: str, ticker: Ticker | None) -> bool:
        if not ticker or ticker.get("percentage") is None:
            self.log_once(
                f"Removed {pair} from whitelist, because ticker['percentage'] is empty.",
                logger.info,
            )
            return False

        change = ticker["percentage"]
        if change < self._min_change or change > self._max_change:
            self.log_once(
                f"Removed {pair} from whitelist, because 24h change {change:.2f}% "
                f"is outside [{self._min_change:.1f}%, {self._max_change:.1f}%].",
                logger.info,
            )
            return False

        return True

