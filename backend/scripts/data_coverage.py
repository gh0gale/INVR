"""How much of the verdict is decided by real data?

Runs Bronze -> Silver -> Gold (no LLM, no Supabase) for a basket of tickers and
timeframes and reports, for every gate the timeframe defines, how often it was
actually evaluated - as opposed to skipped for missing data, or scored on a
default. A gate that is silently absent in most runs is a verdict that is
quietly decided by fewer signals than the design claims.

    python -m scripts.data_coverage                   # default basket
    python -m scripts.data_coverage TCS INFY --tf swing

Uses its own temporary cache so stale cached data cannot flatter the result.
"""
import argparse
import asyncio
import os
import sys
import tempfile
from collections import Counter, defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("INVR_CACHE_DIR", tempfile.mkdtemp(prefix="invr-coverage-"))

from scripts._log import get_logger  # noqa: E402
from app.services.bronze_service import build_bronze_payload  # noqa: E402
from app.services.gold_service import evaluate_hard_gates  # noqa: E402
from app.services.silver_service import compute_silver_metrics  # noqa: E402

logger = get_logger(__name__)

DEFAULT_TICKERS = ["RELIANCE", "TCS", "HDFCBANK", "MARUTI", "HINDUNILVR",
                   "SUNPHARMA", "TATASTEEL", "LT", "BHARTIARTL", "NTPC"]

# Every gate gold_service can emit per timeframe. long_term does not fetch
# circuit limits (router.py), so it has no circuit gate to expect.
GATES = {
    "swing": ["circuit", "volume", "trend", "sector", "rsi", "balance_sheet"],
    "positional": ["circuit", "volume", "death_cross", "revenue_growth", "capital_efficiency"],
    "long_term": ["volume", "secular_trend", "valuation", "fcf_quality", "eps_growth"],
}

# Silver fields the verdict, the confidence or the narrative leans on.
FIELDS = {
    "swing": ["stock_vs_sector_rs", "market_regime", "rsi_14", "debt_to_equity",
              "pe_vs_sector_avg", "institutional_bias"],
    "positional": ["sma_200", "revenue_cagr_3y", "profit_cagr_3y", "opm_trend", "roe_pct",
                   "valuation_comfort", "stock_vs_sector_rs", "market_regime"],
    "long_term": ["sma_200", "revenue_cagr_5y", "eps_cagr_5y", "fcf_conversion", "roe_consistency_5y",
                  "debt_trajectory", "trailing_pe", "pe_band_vs_growth", "stock_vs_sector_rs", "market_regime"],
}


async def run_one(ticker: str, tf: str):
    bronze = await build_bronze_payload(ticker, tf)
    silver = compute_silver_metrics(bronze)
    gold = evaluate_hard_gates(silver, bronze.circuit_status, 100000.0)
    return bronze, silver, gold


async def main(tickers, timeframes) -> None:
    gate_hits = defaultdict(Counter)
    field_hits = defaultdict(Counter)
    runs = Counter()
    extras = defaultdict(Counter)

    for tf in timeframes:
        for t in tickers:
            try:
                bronze, silver, gold = await run_one(t, tf)
            except Exception as e:  # noqa: BLE001
                logger.warning("%-11s %-10s FAILED %s: %s", t, tf, type(e).__name__, str(e)[:100])
                continue
            runs[tf] += 1
            for g in gold.gate_results:
                gate_hits[tf][g] += 1
            for f in FIELDS[tf]:
                if getattr(silver, f, None) is not None:
                    field_hits[tf][f] += 1
            extras[tf][f"circuit={bronze.circuit_status}"] += 1
            bench = getattr(silver, "benchmark_index", None)
            extras[tf][f"benchmark={bench}"] += 1
            missing = [g for g in GATES[tf] if g not in gold.gate_results]
            logger.info("%-11s %-10s %-11s conf=%5.1f gates=%d/%d  missing=%s",
                        t, tf, gold.verdict, gold.confidence_score,
                        len(gold.gate_results), len(GATES[tf]), ",".join(missing) or "-")

    for tf in timeframes:
        n = runs[tf]
        if not n:
            continue
        logger.info("\n=== %s (%d runs)", tf, n)
        logger.info("  gates evaluated:")
        for g in GATES[tf]:
            logger.info("    %-20s %3d%%", g, round(100 * gate_hits[tf][g] / n))
        logger.info("  silver fields present:")
        for f in FIELDS[tf]:
            logger.info("    %-20s %3d%%", f, round(100 * field_hits[tf][f] / n))
        logger.info("  %s", ", ".join(f"{k} x{v}" for k, v in sorted(extras[tf].items())))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("tickers", nargs="*", default=DEFAULT_TICKERS)
    p.add_argument("--tf", nargs="*", default=["swing", "positional", "long_term"])
    a = p.parse_args()
    asyncio.run(main([t.upper() for t in a.tickers], a.tf))
