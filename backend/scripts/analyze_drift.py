"""Statistical drift analysis over graded predictions.

Audit findings NEW-BE-11 (four of nine thresholds had a drift check) and
NEW-BE-12 (the confidence score was linear in sample size and carried no
inferential meaning).

What changed:

* Confidence now comes from a bootstrap interval rather than a formula that
  only knew how many rows it had seen. A change is proposed only when the
  configured threshold sits outside the interval for winning trades, which is
  the actual question being asked: "is the current gate demonstrably wrong?"
* Three fundamental thresholds gained checks: `max_pe`, `eps_cagr_min` and
  `revenue_cagr_min`.
* `debt_equity_max` and `roe_min` still have no check, and the reason is
  recorded below rather than left as a silent gap.

Uses only numpy and pandas, both already dependencies.
"""
import os
import sys

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.gate_thresholds import GATE_THRESHOLDS as TH

load_dotenv(override=True)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

MIN_SAMPLE = 30
MIN_SUBSET = 10          # per-metric minimum once nulls are dropped
BOOTSTRAP_DRAWS = 2000
# Fixed seed, and a fresh generator per call rather than one shared stream:
# a shared generator advances between checks, so the same dataset would grade
# differently depending on how many checks ran before it.
BOOTSTRAP_SEED = 20260818

# Thresholds with no drift check, and why. Both are stored in SilverMetrics as
# booleans (`debt_flag`, `roe_vs_cost_of_capital`) rather than as the raw ratio,
# so the ledger holds no distribution to measure. Checking them means recording
# the raw values first; until then, saying so beats a fabricated check.
UNCHECKABLE = {
    "debt_equity_max": "silver_state stores debt_flag (bool), not the raw ratio",
    "roe_min": "silver_state stores roe_vs_cost_of_capital (bool), not raw ROE",
}


def bootstrap_quantile_ci(values: np.ndarray, q: float, draws: int = BOOTSTRAP_DRAWS):
    """Percentile interval for a quantile, by resampling with replacement.

    Returns (low, high, point). A threshold inside this interval is statistically
    indistinguishable from what the winning trades actually did, so leave it alone.
    """
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(values)
    estimates = np.quantile(
        rng.choice(values, size=(draws, n), replace=True), q, axis=1
    )
    return (
        float(np.percentile(estimates, 2.5)),
        float(np.percentile(estimates, 97.5)),
        float(np.quantile(values, q)),
    )


def confidence_from_interval(low: float, high: float, point: float) -> float:
    """Tightness of the interval relative to the estimate, as a 50-95 score.

    A narrow interval around a well-separated estimate is worth more than a wide
    one from the same number of rows, which is exactly what the old linear
    formula could not express.
    """
    if point == 0:
        return 50.0
    relative_width = abs(high - low) / abs(point)
    score = 95.0 - (relative_width * 100.0)
    return round(float(min(95.0, max(50.0, score))), 1)


def propose(metric: str, current: float, suggested: float, reason: str, sample: int,
            low: float, high: float, point: float):
    confidence = confidence_from_interval(low, high, point)
    supabase.table("threshold_insights").insert({
        "metric": metric,
        "timeframe": "swing",
        "current_threshold": float(current),
        "suggested_threshold": float(round(suggested, 3)),
        "confidence_score": confidence,
        "reasoning": (
            f"{reason} Bootstrap 95% interval for winners: "
            f"[{low:.2f}, {high:.2f}] from {sample} graded rows. "
            f"The configured gate of {current} sits outside it."
        ),
    }).execute()
    print(f" INSIGHT: {metric} {current} -> {round(suggested, 3)} (confidence {confidence})")


def check_threshold(wins: pd.DataFrame, column: str, metric: str, quantile: float,
                    direction: str, reason: str, margin: float = 0.0):
    """Propose a move only when the gate lies outside the winners' interval.

    direction 'ceiling': the gate should sit at or above what winners did.
    direction 'floor':   the gate should sit at or below what winners did.
    """
    if column not in wins.columns:
        return
    values = wins[column].dropna().to_numpy(dtype=float)
    if len(values) < MIN_SUBSET:
        print(f" skipped {metric}: only {len(values)} graded rows carry this metric")
        return

    current = float(TH[metric])
    low, high, point = bootstrap_quantile_ci(values, quantile)

    if direction == "ceiling" and high < (current - margin):
        propose(metric, current, point,
                f"{reason} Winners cluster below the configured ceiling.",
                len(values), low, high, point)
    elif direction == "floor" and low > (current + margin):
        propose(metric, current, point,
                f"{reason} Winners clear a materially higher bar than the gate requires.",
                len(values), low, high, point)


def analyze_system_drift():
    print("INITIALISING STATISTICAL DRIFT ENGINE")

    logs = (
        supabase.table("algorithmic_ledger")
        .select("timeframe, actual_outcome, silver_state, pipeline_version")
        .neq("actual_outcome", "PENDING")
        .neq("actual_outcome", "DRAW")
        .execute()
        .data
    )

    if len(logs) < MIN_SAMPLE:
        print(f"Only {len(logs)} graded rows. Need {MIN_SAMPLE} for significance.")
        return

    df = pd.DataFrame([{
        "timeframe": log["timeframe"],
        "outcome": log["actual_outcome"],
        "version": log.get("pipeline_version"),
        "rsi": log["silver_state"].get("rsi_14"),
        "vol": log["silver_state"].get("current_volume") or 0,
        "avg_vol": max(1, log["silver_state"].get("volume_avg_20") or 1),
        "sma_gap_pct": log["silver_state"].get("sma_gap_pct"),
        "stock_vs_sector_rs": log["silver_state"].get("stock_vs_sector_rs"),
        "trailing_pe": log["silver_state"].get("trailing_pe"),
        "eps_cagr_5y": log["silver_state"].get("eps_cagr_5y"),
        "revenue_cagr_5y": log["silver_state"].get("revenue_cagr_5y"),
        "revenue_cagr_3y": log["silver_state"].get("revenue_cagr_3y"),
    } for log in logs])

    df["vol_ratio"] = df["vol"] / df["avg_vol"]
    df["abs_sma_gap"] = df["sma_gap_pct"].abs()

    # Predictions made under different rulesets are not one population. Report
    # the mix so a reader knows whether the sample is comparable.
    versions = df["version"].dropna().unique()
    if len(versions) > 1:
        print(f" NOTE: sample spans {len(versions)} pipeline versions: {', '.join(map(str, versions))}")

    wins = df[df["outcome"] == "WIN"]
    losses = df[df["outcome"] == "LOSS"]
    print(f" Auditing {len(wins)} wins against {len(losses)} losses")

    if len(wins) < MIN_SUBSET:
        print(f" Not enough winning trades ({len(wins)}) to measure against.")
        return

    # --- Technical gates ---------------------------------------------------
    check_threshold(wins, "rsi", "rsi_overbought", 0.90, "ceiling",
                    "90% of winners entered below this RSI.", margin=3.0)

    vol_low, vol_high, vol_point = bootstrap_quantile_ci(
        wins["vol_ratio"].dropna().to_numpy(dtype=float), 0.50
    )
    if vol_low > (float(TH["volume_min_ratio"]) + 0.4):
        propose("volume_min_ratio", TH["volume_min_ratio"], vol_point - 0.2,
                "The median winning trade needed materially more volume than the gate demands.",
                len(wins), vol_low, vol_high, vol_point)

    check_threshold(wins, "abs_sma_gap", "death_cross_gap_pct", 0.90, "ceiling",
                    "Winning trades show smaller moving-average gaps than the gate allows.",
                    margin=0.2)
    check_threshold(wins, "stock_vs_sector_rs", "sector_rs_min", 0.10, "floor",
                    "Winners consistently outperform their sector by more than the gate requires.",
                    margin=0.05)

    # --- Fundamental gates, previously unchecked ---------------------------
    check_threshold(wins, "trailing_pe", "max_pe", 0.90, "ceiling",
                    "Winners were bought at materially lower valuations than the ceiling permits.",
                    margin=5.0)
    check_threshold(wins, "eps_cagr_5y", "eps_cagr_min", 0.10, "floor",
                    "Winners compound earnings faster than the configured floor.",
                    margin=1.0)
    check_threshold(wins, "revenue_cagr_5y", "revenue_cagr_min", 0.10, "floor",
                    "Winners grow revenue faster than the configured floor.",
                    margin=1.0)

    for metric, why in UNCHECKABLE.items():
        print(f" no check for {metric}: {why}")

    print("DRIFT ANALYSIS COMPLETE")


if __name__ == "__main__":
    analyze_system_drift()
