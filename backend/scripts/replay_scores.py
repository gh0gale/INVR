"""Does the verdict predict anything? Offline replay of the price-only engine.

Phase 0 of docs/verdict_engine_plan.md. Walks a large-cap NSE universe through
the real Silver and Gold code at weekly sample dates and measures how well the
engine's output ranks forward return in excess of the NIFTY 50.

Read-only: no Supabase, no LLM, no ledger rows. Needs the network (yfinance).

    python -m scripts.replay_scores                 # swing and positional
    python -m scripts.replay_scores --horizon swing

Metric: mean cross-sectional Spearman IC (one rank correlation per sample date,
then averaged), with a 95% moving-block bootstrap interval over dates, so
overlapping outcome windows are not counted as independent evidence.

Known biases, printed with every run:
* Survivorship: the universe is today's large caps; companies that fell out of
  the index are absent.
* Price-only: fundamentals are None, so fundamental gates skip. yfinance
  fundamentals are today's values and replaying them would leak the future.
* No transaction costs, slippage or taxes.
"""
import argparse
import os
import sys
from datetime import timedelta
from typing import Callable, Optional

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.bronze import BronzePayload
from app.services.gold_service import evaluate_hard_gates
from app.services.scoring_service import score_v2
from app.services.silver_service import compute_silver_metrics
from scripts._log import get_logger

logger = get_logger(__name__)

# Large-cap NSE names approximating the NIFTY 50. Not an authoritative index
# list: membership changes, and a symbol yfinance no longer serves is skipped.
UNIVERSE = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO",
    "BAJFINANCE", "BAJAJFINSV", "BEL", "BHARTIARTL", "CIPLA", "COALINDIA",
    "DRREDDY", "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
    "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "INDUSINDBK", "INFY",
    "ITC", "JSWSTEEL", "KOTAKBANK", "LT", "M&M", "MARUTI", "NESTLEIND", "NTPC",
    "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SHRIRAMFIN", "SUNPHARMA",
    "TATACONSUM", "TATASTEEL", "TCS", "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO",
]
BENCHMARK = "^NSEI"

# Bars the live pipeline hands Silver per horizon (router.PIPELINE_CONFIG
# periods: swing 6mo, positional 1y of daily bars), and the benchmark window
# Bronze fetches (SECTOR_PERIOD: 2y). Matching them keeps the replayed
# indicators equal to what a live request computes.
PRICE_BARS = {"swing": 126, "positional": 250}
BENCHMARK_BARS = 500
# Calendar days to maturity, as scripts/grade_ledger.py grades them.
FORWARD_DAYS = {"swing": 15, "positional": 90}
SAMPLE_EVERY_BARS = 5   # weekly samples; daily ones would overlap almost fully
MIN_NAMES_PER_DATE = 10
BOOTSTRAP_DRAWS = 2000

VERDICT_ORDINAL = {"STRONG BUY": 2, "BUY ON DIP": 1, "MONITOR": 0, "CAUTION": -1, "AVOID": -2}


def score_both(bronze: BronzePayload) -> dict:
    """v1 and v2 on the same Silver metrics, so differences are the engine's."""
    silver = compute_silver_metrics(bronze)
    gold = evaluate_hard_gates(silver, bronze.circuit_status, 0.0)
    v2 = score_v2(silver, bronze.circuit_status)
    return {
        "verdict": gold.verdict,
        "v1_ordinal": VERDICT_ORDINAL[gold.verdict],
        "v1_confidence": gold.confidence_score,
        "v2_verdict": v2.verdict,
        "v2_ordinal": VERDICT_ORDINAL[v2.verdict],
        "v2_composite": v2.composite,
    }


# name -> (scorer, score columns it emits)
SCORERS: dict[str, tuple[Callable[[BronzePayload], dict], tuple[str, ...]]] = {
    "engine": (score_both, ("v1_ordinal", "v1_confidence", "v2_ordinal", "v2_composite")),
}

# Paired comparisons reported as a difference of per-date ICs.
COMPARISONS = [("v2_composite", "v1_ordinal"), ("v2_ordinal", "v1_ordinal")]


def forward_close(closes: pd.Series, at: pd.Timestamp, days: int) -> Optional[float]:
    """Close of the first bar on or after `at + days`, or None past the data."""
    target = at + timedelta(days=days)
    pos = closes.index.searchsorted(target)
    return None if pos >= len(closes) else float(closes.iloc[pos])


def excess_return(p0: float, p1: float, b0: float, b1: float) -> float:
    return (p1 / p0 - 1.0) - (b1 / b0 - 1.0)


def per_date_ic(samples: pd.DataFrame, score_col: str, min_names: int = MIN_NAMES_PER_DATE) -> pd.Series:
    """Spearman correlation of score with excess return, one value per date.

    Dates with too few names, or where every name got the same score (no
    ranking information), are dropped rather than counted as zero.
    """
    def _ic(group: pd.DataFrame) -> float:
        if len(group) < min_names or group[score_col].nunique() < 2:
            return np.nan
        return group[score_col].rank().corr(group["excess"].rank())

    ics = samples.groupby("date")[[score_col, "excess"]].apply(_ic)
    return ics.dropna().sort_index()


def block_bootstrap_ci(values: np.ndarray, block: int, draws: int = BOOTSTRAP_DRAWS,
                       seed: int = 0) -> tuple[float, float]:
    """95% interval of the mean, resampling contiguous blocks of dates."""
    n = len(values)
    if n == 0:
        return (np.nan, np.nan)
    block = max(1, min(block, n))
    rng = np.random.default_rng(seed)
    blocks_needed = -(-n // block)
    means = np.empty(draws)
    for d in range(draws):
        starts = rng.integers(0, n - block + 1, size=blocks_needed)
        sample = np.concatenate([values[s:s + block] for s in starts])[:n]
        means[d] = sample.mean()
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def _download(symbols: list[str]) -> dict[str, pd.DataFrame]:
    import yfinance as yf

    def _get(batch: list[str]) -> dict[str, pd.DataFrame]:
        raw = yf.download(batch, period="5y", interval="1d", group_by="ticker",
                          auto_adjust=False, progress=False, threads=True)
        got = {}
        for sym in batch:
            if sym in raw.columns.get_level_values(0):
                df = raw[sym].dropna()
                if len(df) > 0:
                    got[sym] = df
        return got

    frames = _get(symbols)
    # A threaded batch often loses a few symbols to Yahoo throttling ("possibly
    # delisted" for INFY or SBIN); one sequential retry recovers most of them.
    missing = [s for s in symbols if s not in frames]
    for sym in missing:
        frames.update(_get([sym]))
    for sym in symbols:
        if sym not in frames:
            logger.info(f"no data for {sym}, skipped")
    return frames


def collect_samples(horizon: str, prices: dict[str, pd.DataFrame], bench: pd.DataFrame) -> pd.DataFrame:
    bars, fwd_days = PRICE_BARS[horizon], FORWARD_DAYS[horizon]
    bench_close = bench["Close"]
    rows = []
    for sym, df in prices.items():
        closes = df["Close"]
        for i in range(max(bars, 200) - 1, len(df), SAMPLE_EVERY_BARS):
            at = df.index[i]
            p1 = forward_close(closes, at, fwd_days)
            b_pos = bench_close.index.searchsorted(at, side="right") - 1
            if p1 is None or b_pos < 0:
                continue
            b1 = forward_close(bench_close, bench_close.index[b_pos], fwd_days)
            if b1 is None:
                continue
            bronze = BronzePayload(
                ticker=sym, timeframe=horizon, circuit_status="not_checked",
                benchmark_index="NIFTY 50",
                price_history=df.iloc[i + 1 - bars:i + 1],
                sector_history=bench.iloc[max(0, b_pos + 1 - BENCHMARK_BARS):b_pos + 1],
                fundamentals=None, institutional_activity=None,
            )
            row = {"date": at.date(), "ticker": sym,
                   "excess": excess_return(float(closes.iloc[i]), p1,
                                           float(bench_close.iloc[b_pos]), b1)}
            for name, (scorer, _) in SCORERS.items():
                try:
                    row.update(scorer(bronze))
                except Exception as e:  # one bad slice must not end the run
                    logger.info(f"{name} failed on {sym} {at.date()}: {e}")
            rows.append(row)
    return pd.DataFrame(rows)


def report(horizon: str, samples: pd.DataFrame) -> None:
    block = max(1, round(FORWARD_DAYS[horizon] / 7))
    logger.info(f"\n=== {horizon}: {len(samples)} samples, {samples['ticker'].nunique()} names, "
                f"{samples['date'].nunique()} dates, {FORWARD_DAYS[horizon]}d forward ===")
    for _, cols in SCORERS.values():
        for col in cols:
            if col not in samples:
                continue
            ics = per_date_ic(samples.dropna(subset=[col]), col)
            lo, hi = block_bootstrap_ci(ics.to_numpy(), block)
            logger.info(f"{col:>16}: mean IC {ics.mean():+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]  "
                        f"over {len(ics)} dates")
    for new, old in COMPARISONS:
        if new not in samples or old not in samples:
            continue
        paired = samples.dropna(subset=[new, old])
        diff = (per_date_ic(paired, new) - per_date_ic(paired, old)).dropna()
        lo, hi = block_bootstrap_ci(diff.to_numpy(), block)
        logger.info(f"{new} - {old}: mean IC diff {diff.mean():+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]")
    for col, label in (("verdict", "v1"), ("v2_verdict", "v2")):
        if col not in samples:
            continue
        buckets = samples.groupby(col)["excess"].agg(["count", "mean", "median"])
        buckets = buckets.reindex([v for v in VERDICT_ORDINAL if v in buckets.index])
        logger.info(f"excess return vs NIFTY 50 by {label} verdict:\n" + buckets.to_string(
            float_format=lambda x: f"{x:+.4f}"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--horizon", choices=sorted(PRICE_BARS), action="append")
    parser.add_argument("--from-csv", action="store_true",
                        help="re-report the samples a previous run saved, without downloading")
    args = parser.parse_args()
    horizons = args.horizon or sorted(PRICE_BARS)
    out_dir = os.path.join(os.getenv("INVR_CACHE_DIR") or ".local_cache", "replay")

    logger.info("Biases: survivorship (today's large caps), price-only, no costs.")
    if args.from_csv:
        for horizon in horizons:
            report(horizon, pd.read_csv(os.path.join(out_dir, f"replay_{horizon}.csv")))
        return
    symbols = [f"{s}.NS" for s in UNIVERSE]
    frames = _download(symbols + [BENCHMARK])
    bench = frames.pop(BENCHMARK, None)
    if bench is None:
        logger.info("NIFTY 50 history unavailable; cannot compute excess returns.")
        return

    os.makedirs(out_dir, exist_ok=True)
    for horizon in horizons:
        samples = collect_samples(horizon, frames, bench)
        if samples.empty:
            logger.info(f"{horizon}: no samples")
            continue
        report(horizon, samples)
        path = os.path.join(out_dir, f"replay_{horizon}.csv")
        samples.to_csv(path, index=False)
        logger.info(f"samples written to {path}")


if __name__ == "__main__":
    main()
