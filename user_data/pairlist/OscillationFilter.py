"""
OscillationFilter — keeps pairs with regular, frequent up/down price cycles.

Designed for grid strategies: rejects pairs that trend in one direction or only
oscillate slowly (once every few days). Measures oscillation at the intraday
level (default 1h candles) so the filter matches the actual timescale of a
5m/15m grid.

Four metrics (computed over the full lookback window AND a short recent window):
  oscillation_ratio   — fraction of candles where the close changes direction.
                        Higher = more back-and-forth action.
  reversals_per_day   — average number of direction reversals per 24 h.
                        Directly controls "how close together" the swings are.
  choppiness_index    — 100*log10(ΣTR / range) / log10(n).
                        61.8 = random walk, 38.2 = strong trend.
  spike_ratio         — max single-candle range / mean candle range.
                        High values = isolated spike candles that blow grids.

The recent-window check (default last 24 h) uses its own thresholds so a pair
that oscillated for 6 days but just broke out intraday is still rejected.
"""

import logging
import math
from datetime import timedelta

import numpy as np
from pandas import DataFrame

from freqtrade.constants import ListPairsWithTimeframes
from freqtrade.exceptions import OperationalException
from freqtrade.exchange import timeframe_to_minutes
from freqtrade.exchange.exchange_types import Tickers
from freqtrade.plugins.pairlist.IPairList import IPairList, PairlistParameter, SupportsBacktesting
from freqtrade.util import FtTTLCache, dt_floor_day, dt_now, dt_ts


logger = logging.getLogger(f"freqtrade.plugins.pairlist.{__name__}")


class OscillationFilter(IPairList):
    """
    Pairlist filter that selects pairs with tight, regular oscillation.
    Ideal as a post-filter for grid/DCA strategies after VolumePairList.

    Two-window design:
      Full window  (lookback_days)  — catches chronic trendiness / low choppiness
      Recent window (recent_hours)  — catches intraday breakouts on pairs that were
                                      oscillatory earlier in the day/week
    Both windows must pass their respective thresholds.
    """

    supports_backtesting = SupportsBacktesting.NO

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._days: int = self._pairlistconfig.get("lookback_days", 7)
        self._timeframe: str = self._pairlistconfig.get("timeframe", "1h")
        self._min_oscillation: float = self._pairlistconfig.get("min_oscillation_ratio", 0.40)
        self._min_reversals_per_day: float = self._pairlistconfig.get("min_reversals_per_day", 3.0)
        self._max_spike_ratio: float = self._pairlistconfig.get("max_spike_ratio", 2.5)
        self._min_choppiness: float = self._pairlistconfig.get("min_choppiness", 52.0)
        self._max_doji_ratio: float = self._pairlistconfig.get("max_doji_ratio", 0.3)
        self._doji_threshold: float = self._pairlistconfig.get("doji_threshold", 0.001)

        # Recent-window parameters — catches intraday breakouts
        self._recent_hours: int = self._pairlistconfig.get("recent_hours", 24)
        self._recent_min_oscillation: float = self._pairlistconfig.get(
            "recent_min_oscillation_ratio", 0.30
        )
        self._recent_min_choppiness: float = self._pairlistconfig.get(
            "recent_min_choppiness", 45.0
        )

        self._def_candletype = self._config["candle_type_def"]

        self._pair_cache: FtTTLCache = FtTTLCache(maxsize=1000, ttl=self.refresh_period)

        # Candle-count sanity check against exchange limit
        tf_minutes = timeframe_to_minutes(self._timeframe)
        candles_needed = (self._days * 24 * 60) // tf_minutes
        candle_limit = self._exchange.ohlcv_candle_limit(self._timeframe, self._def_candletype)

        if self._days < 2:
            raise OperationalException("OscillationFilter requires lookback_days >= 2")
        if candles_needed > candle_limit:
            raise OperationalException(
                f"OscillationFilter: {self._days}d × {self._timeframe} = {candles_needed} candles "
                f"exceeds exchange limit ({candle_limit}). Reduce lookback_days."
            )

    def short_desc(self) -> str:
        return (
            f"{self.name} - {self._timeframe}/{self._days}d | "
            f"osc>={self._min_oscillation:.0%} "
            f"rev/day>={self._min_reversals_per_day:.1f} "
            f"chop>={self._min_choppiness:.0f} "
            f"spike<={self._max_spike_ratio:.1f}x "
            f"doji<={self._max_doji_ratio:.0%} | "
            f"recent {self._recent_hours}h: "
            f"osc>={self._recent_min_oscillation:.0%} "
            f"chop>={self._recent_min_choppiness:.0f}"
        )

    @staticmethod
    def description() -> str:
        return "Filter pairs by intraday oscillation frequency (grid-strategy friendly)."

    @staticmethod
    def available_parameters() -> dict[str, PairlistParameter]:
        return {
            "lookback_days": {
                "type": "number",
                "default": 7,
                "description": "Lookback Days",
                "help": "Number of days of candles to analyse.",
            },
            "timeframe": {
                "type": "string",
                "default": "1h",
                "description": "Candle Timeframe",
                "help": (
                    "Timeframe to use for oscillation measurement. "
                    "Use '1h' for grids on 5m–15m. Use '4h' for grids on 1h."
                ),
            },
            "min_oscillation_ratio": {
                "type": "number",
                "default": 0.40,
                "description": "Min Oscillation Ratio",
                "help": (
                    "Minimum fraction of candles where the close direction reverses (0–1). "
                    "0.40 = 40% of candles must change direction."
                ),
            },
            "min_reversals_per_day": {
                "type": "number",
                "default": 3.0,
                "description": "Min Reversals Per Day",
                "help": (
                    "Minimum average number of close-direction reversals per 24 h. "
                    "3.0 = at least one reversal every 8 h. "
                    "Higher = tighter / more frequent oscillation required."
                ),
            },
            "max_spike_ratio": {
                "type": "number",
                "default": 2.5,
                "description": "Max Spike Ratio",
                "help": (
                    "Maximum ratio of the single worst candle range to the mean range. "
                    "2.5 = the biggest candle may be at most 2.5× the average."
                ),
            },
            "min_choppiness": {
                "type": "number",
                "default": 52.0,
                "description": "Min Choppiness Index",
                "help": (
                    "Minimum Choppiness Index (0–100). "
                    "61.8 = random walk, 52 = moderately ranging, 38.2 = strong trend."
                ),
            },
            "max_doji_ratio": {
                "type": "number",
                "default": 0.3,
                "description": "Max Doji Ratio",
                "help": (
                    "Maximum fraction of candles allowed to be doji (0–1). "
                    "0.3 = at most 30% of candles may have a near-zero body. "
                    "Filters low-liquidity assets like XAUT that barely move."
                ),
            },
            "doji_threshold": {
                "type": "number",
                "default": 0.001,
                "description": "Doji Body Threshold",
                "help": (
                    "A candle is a doji when |close - open| / close < this value. "
                    "0.001 = body smaller than 0.1% of price counts as doji."
                ),
            },
            "recent_hours": {
                "type": "number",
                "default": 24,
                "description": "Recent Window (hours)",
                "help": (
                    "Number of most-recent candle hours to evaluate separately. "
                    "Catches intraday breakouts on pairs that oscillated historically "
                    "but are now trending. 24 = check the last day independently."
                ),
            },
            "recent_min_oscillation_ratio": {
                "type": "number",
                "default": 0.30,
                "description": "Recent Min Oscillation Ratio",
                "help": (
                    "Min oscillation ratio for the recent window. "
                    "Can be looser than the full-window threshold since the recent "
                    "window has fewer candles. 0.30 = at least 30% must reverse."
                ),
            },
            "recent_min_choppiness": {
                "type": "number",
                "default": 45.0,
                "description": "Recent Min Choppiness Index",
                "help": (
                    "Min Choppiness Index for the recent window. "
                    "38.2 = strong trend; set above that to reject breakout pairs. "
                    "45.0 catches sustained intraday trends while allowing short spikes."
                ),
            },
            **IPairList.refresh_period_parameter(),
        }

    @property
    def needstickers(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Core filter
    # ------------------------------------------------------------------

    def filter_pairlist(self, pairlist: list[str], tickers: Tickers) -> list[str]:
        needed_pairs: ListPairsWithTimeframes = [
            (p, self._timeframe, self._def_candletype)
            for p in pairlist
            if p not in self._pair_cache
        ]

        since_ms = dt_ts(dt_floor_day(dt_now()) - timedelta(days=self._days))
        candles = self._exchange.refresh_ohlcv_with_cache(needed_pairs, since_ms=since_ms)

        result: list[str] = []
        for p in pairlist:
            pair_candles = candles.get((p, self._timeframe, self._def_candletype), None)
            metrics = self._calculate_metrics(p, pair_candles)

            if metrics is None:
                self.log_once(f"OscillationFilter: removed {p} — no candle data.", logger.info)
                continue

            osc_ratio, reversals_per_day, choppiness, spike_ratio, doji_ratio, recent_osc, recent_chop = metrics
            if self._validate_pair(p, osc_ratio, reversals_per_day, choppiness, spike_ratio, doji_ratio, recent_osc, recent_chop):
                result.append(p)

        # Log summary only when the passing count changes — filter_pairlist is called on
        # every heartbeat tick, so a constant INFO log floods the logfile.
        summary = f"OscillationFilter: {len(result)}/{len(pairlist)} pairs passed."
        self.log_once(summary, logger.info)
        return result

    # ------------------------------------------------------------------
    # Metric computation
    # ------------------------------------------------------------------

    @staticmethod
    def _osc_and_chop(df: DataFrame, tf_minutes: int) -> tuple[float, float, float] | None:
        """Compute (osc_ratio, reversals_per_day, choppiness) for a candle slice."""
        closes = df["close"].values
        high = df["high"].values
        low = df["low"].values

        diff = np.diff(closes)
        nonzero = diff[diff != 0]
        if len(nonzero) < 4:
            return None

        reversal_mask = nonzero[1:] * nonzero[:-1] < 0
        reversals = int(reversal_mask.sum())
        osc_ratio = reversals / (len(nonzero) - 1)

        candles_per_day = (24 * 60) / tf_minutes
        reversals_per_day = reversals / (len(df) / candles_per_day)

        prev_close = np.empty_like(high)
        prev_close[0] = df["open"].values[0]
        prev_close[1:] = closes[:-1]

        tr = np.maximum(
            high - low,
            np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
        )
        sum_tr = float(tr.sum())
        price_range = float(high.max() - low.min())
        n = len(df)

        if price_range > 0 and sum_tr > 0 and n > 1:
            choppiness = 100.0 * math.log10(sum_tr / price_range) / math.log10(n)
        else:
            choppiness = 0.0

        return osc_ratio, reversals_per_day, choppiness

    def _calculate_metrics(
        self, pair: str, candles: DataFrame | None
    ) -> tuple[float, float, float, float, float, float, float] | None:
        if (cached := self._pair_cache.get(pair, None)) is not None:
            return cached  # type: ignore[return-value]

        if candles is None or candles.empty:
            return None

        df = candles.copy()
        tf_minutes = timeframe_to_minutes(self._timeframe)

        # ---- Full-window metrics ------------------------------------------
        full = self._osc_and_chop(df, tf_minutes)
        if full is None:
            return None
        osc_ratio, reversals_per_day, choppiness = full

        closes = df["close"].values
        high = df["high"].values
        low = df["low"].values
        opens = df["open"].values

        # ---- Spike ratio ----------------------------------------------
        range_pct = (high - low) / np.where(closes > 0, closes, 1.0)
        mean_range = float(range_pct.mean())
        spike_ratio = float(range_pct.max()) / mean_range if mean_range > 0 else 0.0

        # ---- Doji ratio -----------------------------------------------
        body_ratio = np.abs(closes - opens) / np.where(closes > 0, closes, 1.0)
        doji_ratio = float((body_ratio < self._doji_threshold).mean())

        # ---- Recent-window metrics (last recent_hours candles) ----------
        recent_candles = int((self._recent_hours * 60) / tf_minutes)
        if len(df) >= recent_candles:
            recent_df = df.iloc[-recent_candles:]
            recent = self._osc_and_chop(recent_df, tf_minutes)
            recent_osc = recent[0] if recent else osc_ratio
            recent_chop = recent[2] if recent else choppiness
        else:
            # Not enough candles for recent window — fall back to full metrics
            recent_osc = osc_ratio
            recent_chop = choppiness

        metrics = (osc_ratio, reversals_per_day, choppiness, spike_ratio, doji_ratio, recent_osc, recent_chop)
        self._pair_cache[pair] = metrics
        return metrics

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_pair(
        self,
        pair: str,
        osc_ratio: float,
        reversals_per_day: float,
        choppiness: float,
        spike_ratio: float,
        doji_ratio: float,
        recent_osc: float,
        recent_chop: float,
    ) -> bool:
        failures: list[str] = []

        # Full-window checks
        if osc_ratio < self._min_oscillation:
            failures.append(f"osc={osc_ratio:.2f} < {self._min_oscillation:.2f}")
        if reversals_per_day < self._min_reversals_per_day:
            failures.append(
                f"rev/day={reversals_per_day:.1f} < {self._min_reversals_per_day:.1f}"
            )
        if choppiness < self._min_choppiness:
            failures.append(f"chop={choppiness:.1f} < {self._min_choppiness:.1f}")
        if spike_ratio > self._max_spike_ratio:
            failures.append(f"spike={spike_ratio:.1f}x > {self._max_spike_ratio:.1f}x")
        if doji_ratio > self._max_doji_ratio:
            failures.append(f"doji={doji_ratio:.0%} > {self._max_doji_ratio:.0%}")

        # Recent-window checks (catches intraday breakouts)
        if recent_osc < self._recent_min_oscillation:
            failures.append(
                f"recent_osc={recent_osc:.2f} < {self._recent_min_oscillation:.2f} "
                f"(last {self._recent_hours}h trending)"
            )
        if recent_chop < self._recent_min_choppiness:
            failures.append(
                f"recent_chop={recent_chop:.1f} < {self._recent_min_choppiness:.1f} "
                f"(last {self._recent_hours}h trending)"
            )

        if failures:
            self.log_once(
                f"OscillationFilter: removed {pair} — {' | '.join(failures)}",
                logger.info,
            )
            return False

        logger.debug(
            f"OscillationFilter PASS {pair} | "
            f"osc={osc_ratio:.2f} rev/day={reversals_per_day:.1f} "
            f"chop={choppiness:.1f} spike={spike_ratio:.1f}x doji={doji_ratio:.0%} | "
            f"recent osc={recent_osc:.2f} chop={recent_chop:.1f}"
        )
        return True
