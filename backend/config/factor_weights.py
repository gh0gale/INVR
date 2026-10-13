# config/factor_weights.py
#
# Verdict engine v2 (docs/verdict_engine_plan.md, Phase 1). One weight table
# per horizon, set by hand and frozen (decision D3): no per-regime, per-risk or
# per-user weights. Seeded from v1's GATE_WEIGHTS and deliberately NOT tuned on
# the Phase 0 replay, which would make the v1 vs v2 comparison in-sample.
#
# Thresholds stay in gate_thresholds.py so the Engine Room keeps tuning them.

RULESET_V2 = "v2.0.0"

FACTOR_WEIGHTS = {
    "intraday": {
        "trend_20": 1.0,
        "rsi": 1.0,
        "volume": 1.5,
    },
    "swing": {
        "trend_20": 1.5,
        "relative_strength": 1.5,
        "rsi": 1.0,
        "volume": 1.5,
        "leverage": 1.5,
    },
    "positional": {
        "ma_alignment": 3.0,
        "volume": 1.5,
        "revenue_growth_3y": 1.0,
        "profit_growth_3y": 1.0,
        "roe": 1.5,
        "margin_trend": 1.0,
    },
    "long_term": {
        "secular_trend": 2.0,
        "volume": 1.5,
        "valuation": 2.0,
        "fcf_quality": 2.0,
        "eps_growth_5y": 2.0,
        "revenue_growth_5y": 1.0,
        "roe_consistency": 1.0,
        "debt_trajectory": 1.0,
        "peg": 1.0,
    },
}

# Composite (weighted mean in [-1, 1], missing factors scored 0) to verdict.
# Checked top-down; the first cutoff the composite reaches wins.
VERDICT_CUTOFFS = [
    ("STRONG BUY", 0.5),
    ("BUY ON DIP", 0.2),
    ("MONITOR", -0.2),
    ("CAUTION", -0.5),
]
FALLBACK_VERDICT = "AVOID"

# Below this share of horizon weight with data, the verdict is capped at MONITOR.
COVERAGE_FLOOR = 0.5
