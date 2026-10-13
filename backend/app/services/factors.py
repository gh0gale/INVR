"""Factor library for the v2 verdict engine (docs/verdict_engine_plan.md, Phase 1).

Each factor turns Silver metrics into a graded score in [-1, 1], or None when
its input is missing. Pure functions, no I/O.

Convention: where a configured threshold exists, the threshold maps to 0. So
"RSI exactly at the overbought line" is neutral, deeper is negative, and the
Engine Room's threshold edits still move the engine.

ponytail: every curve is piecewise linear. Shape them better only if the replay
shows a factor's IC improves.
"""
from typing import Callable, Optional

from app.schemas.gold import FactorResult
from app.schemas.silver import SilverMetrics
from config.gate_thresholds import GATE_THRESHOLDS as TH

# Scales for factors with no configured threshold.
TREND_ATR_SPAN = 2.0          # price this many ATR above/below the SMA = +/-1
SECULAR_SPAN = 0.20           # 20% above/below the 200 SMA = +/-1
MA_GAP_SPAN_PCT = 2.0         # 50/200 gap of +/-2% = +/-1
VOLUME_STRONG_RATIO = 1.5     # institutional confirmation, as v1's override
FCF_GOOD = 0.6                # v1's fcf_quality line
PEG_FAIR = 1.5


def ramp(x: float, lo: float, mid: float, hi: float) -> float:
    """-1 at lo, 0 at mid, +1 at hi, linear between, clipped outside."""
    if x <= mid:
        return max(-1.0, (x - mid) / (mid - lo))
    return min(1.0, (x - mid) / (hi - mid))


def _result(name: str, score: Optional[float], reason: str, watch: Optional[str] = None) -> FactorResult:
    if score is None:
        return FactorResult(name=name, reason="no data")
    return FactorResult(name=name, score=round(score, 4), reason=reason,
                        watch_item=watch if score < 0 else None)


def trend_20(s: SilverMetrics) -> FactorResult:
    if not s.sma_20 or not s.atr_14:
        return _result("trend_20", None, "")
    d = (s.current_price - s.sma_20) / s.atr_14
    return _result("trend_20", ramp(d, -TREND_ATR_SPAN, 0.0, TREND_ATR_SPAN),
                   f"price {d:+.1f} ATR from the 20-period SMA",
                   f"Wait for a close above the 20-period SMA (₹{s.sma_20:.2f}).")


def rsi(s: SilverMetrics) -> FactorResult:
    if s.rsi_14 is None:
        return _result("rsi", None, "")
    lo, hi = TH["rsi_oversold"], TH["rsi_overbought"]
    mid, half = (lo + hi) / 2, (hi - lo) / 2
    if s.rsi_14 >= mid:
        score, watch = 1 - (s.rsi_14 - mid) / half, "Momentum is stretched. Wait for a pullback."
    else:
        # Oversold is a warning, not a verdict, as in v1: floored at -0.5.
        score, watch = max(-0.5, 1 - (mid - s.rsi_14) / half), "Momentum is oversold. Wait for a confirmed reversal."
    return _result("rsi", max(-1.0, score), f"RSI {s.rsi_14:.1f}", watch)


def volume(s: SilverMetrics) -> FactorResult:
    if not s.current_volume or not s.volume_avg_20:
        return _result("volume", None, "")
    ratio = s.current_volume / s.volume_avg_20
    floor = TH["volume_min_ratio"]
    return _result("volume", ramp(ratio, floor / 2, floor, VOLUME_STRONG_RATIO),
                   f"volume {ratio:.2f}x its 20-period average",
                   f"Wait for volume above {int(s.volume_avg_20 * floor):,} to confirm participation.")


def relative_strength(s: SilverMetrics) -> FactorResult:
    if s.stock_vs_sector_rs is None:
        return _result("relative_strength", None, "")
    th = TH["sector_rs_min"]
    return _result("relative_strength", ramp(s.stock_vs_sector_rs, 2 * th, th, -th),
                   f"{s.stock_vs_sector_rs * 100:+.1f}% vs {s.benchmark_index or 'benchmark'}",
                   "Wait for the stock to stop lagging its benchmark.")


def ma_alignment(s: SilverMetrics) -> FactorResult:
    if s.sma_gap_pct is None:
        return _result("ma_alignment", None, "")
    return _result("ma_alignment", ramp(s.sma_gap_pct, -MA_GAP_SPAN_PCT, 0.0, MA_GAP_SPAN_PCT),
                   f"50-day SMA {s.sma_gap_pct:+.2f}% vs 200-day",
                   "Wait for the 50-day SMA to reclaim the 200-day SMA.")


def secular_trend(s: SilverMetrics) -> FactorResult:
    if not s.sma_200:
        return _result("secular_trend", None, "")
    d = (s.current_price - s.sma_200) / s.sma_200
    return _result("secular_trend", ramp(d, -SECULAR_SPAN, 0.0, SECULAR_SPAN),
                   f"price {d * 100:+.1f}% vs the 200-period SMA",
                   f"Wait for a recovery above the 200-period SMA (₹{s.sma_200:.2f}).")


def _growth(name: str, value: Optional[float], target_pct: float, label: str) -> FactorResult:
    if value is None:
        return _result(name, None, "")
    return _result(name, ramp(value, 0.0, target_pct, 2 * target_pct),
                   f"{label} {value:.1f}% vs {target_pct:.0f}% target",
                   f"{label} is below the {target_pct:.0f}% target.")


def revenue_growth_3y(s: SilverMetrics) -> FactorResult:
    return _growth("revenue_growth_3y", s.revenue_cagr_3y, TH["revenue_cagr_min"] * 100, "3y revenue growth")


def revenue_growth_5y(s: SilverMetrics) -> FactorResult:
    return _growth("revenue_growth_5y", s.revenue_cagr_5y, TH["revenue_cagr_min"] * 100, "5y revenue growth")


def profit_growth_3y(s: SilverMetrics) -> FactorResult:
    return _growth("profit_growth_3y", s.profit_cagr_3y, TH["eps_cagr_min"] * 100, "3y profit growth")


def eps_growth_5y(s: SilverMetrics) -> FactorResult:
    return _growth("eps_growth_5y", s.eps_cagr_5y, TH["eps_cagr_min"] * 100, "5y EPS growth")


def roe(s: SilverMetrics) -> FactorResult:
    if s.roe_pct is None:
        return _result("roe", None, "")
    th = TH["roe_min"]
    return _result("roe", ramp(s.roe_pct, 0.0, th, 2 * th), f"ROE {s.roe_pct:.1f}%",
                   f"Return on equity is below the {th:.0f}% quality bar.")


def leverage(s: SilverMetrics) -> FactorResult:
    if s.debt_to_equity is None:
        return _result("leverage", None, "")
    th = TH["debt_equity_max"]
    return _result("leverage", -ramp(s.debt_to_equity, 0.0, th, 2 * th),
                   f"debt/equity {s.debt_to_equity:.2f}x",
                   f"Debt/equity is above the {th}x ceiling. Size the position smaller.")


def valuation(s: SilverMetrics) -> FactorResult:
    if s.trailing_pe is None:
        return _result("valuation", None, "")
    th = TH["max_pe"]
    return _result("valuation", -ramp(s.trailing_pe, th / 2, th, 2 * th),
                   f"P/E {s.trailing_pe:.1f} vs {th:.0f} ceiling",
                   f"P/E is above the {th:.0f} ceiling.")


def fcf_quality(s: SilverMetrics) -> FactorResult:
    if s.fcf_conversion is None:
        return _result("fcf_quality", None, "")
    return _result("fcf_quality", ramp(s.fcf_conversion, 0.0, FCF_GOOD, 1.0),
                   f"FCF conversion {s.fcf_conversion:.2f}",
                   "Free cash flow lags reported profit.")


def peg(s: SilverMetrics) -> FactorResult:
    if s.pe_band_vs_growth is None:
        return _result("peg", None, "")
    return _result("peg", -ramp(s.pe_band_vs_growth, PEG_FAIR / 2, PEG_FAIR, 2 * PEG_FAIR),
                   f"P/E to EPS growth {s.pe_band_vs_growth:.2f}",
                   "Valuation is high for the growth rate.")


def _label(name: str, value: Optional[str], scores: dict, watch: str) -> FactorResult:
    if value not in scores:
        return _result(name, None, "")
    return _result(name, scores[value], value.replace("_", " "), watch)


def margin_trend(s: SilverMetrics) -> FactorResult:
    return _label("margin_trend", s.opm_trend,
                  {"expanding": 1.0, "stable": 0.0, "contracting": -1.0},
                  "Operating margins are contracting.")


def roe_consistency(s: SilverMetrics) -> FactorResult:
    return _label("roe_consistency", s.roe_consistency_5y,
                  {"consistent_moat": 1.0, "average": 0.0},
                  "")


def debt_trajectory(s: SilverMetrics) -> FactorResult:
    return _label("debt_trajectory", s.debt_trajectory,
                  {"deleveraging": 1.0, "stable": 0.0, "leveraging": -1.0},
                  "Debt is rising.")


FACTORS: dict[str, Callable[[SilverMetrics], FactorResult]] = {
    f.__name__: f for f in (
        trend_20, rsi, volume, relative_strength, ma_alignment, secular_trend,
        revenue_growth_3y, revenue_growth_5y, profit_growth_3y, eps_growth_5y,
        roe, leverage, valuation, fcf_quality, peg,
        margin_trend, roe_consistency, debt_trajectory,
    )
}
