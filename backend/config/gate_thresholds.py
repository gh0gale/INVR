# config/gate_thresholds.py

# Audit trail of automated threshold adjustments
GATE_THRESHOLDS_HISTORY = [
    {"date": "2026-07-10T19:38:42.299797", "metric": "volume_min_ratio", "old": 0.5, "new": 0.73, "reason": "Reality Check: The median winning trade has a volume ratio of 0.93x. Your current gate of 0.5x is letting extremely low-liquidity/low-conviction trades pass."},

]

GATE_THRESHOLDS = {
    "death_cross_gap_pct": 0.5,    # Minimum SMA gap % to confirm a deep death cross
    "rsi_oversold": 30.0,          # Below this = deeply oversold (WARN)
    "rsi_overbought": 70.0,        # Above this = overbought (FAIL)
    "sector_rs_min": -0.05,        # Stock must not underperform sector by > 5%
    "volume_min_ratio": 0.73,       # Volume must be > 50% of average
    "debt_equity_max": 1.5,        # Long-term conservative threshold
    "roe_min": 15.0,               # Minimum ROE for positional/long-term quality
    "revenue_cagr_min": 0.10,      # Target 10% CAGR for growth
    "eps_cagr_min": 0.12,          # Target 12% EPS CAGR
    "max_pe": 50.0                 # Hard valuation ceiling
}