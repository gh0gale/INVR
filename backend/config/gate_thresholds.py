# config/gate_thresholds.py

GATE_THRESHOLDS = {
    "death_cross_gap_pct": 0.5,    # Minimum SMA gap % to confirm a deep death cross
    "rsi_oversold": 30.0,          # Below this = deeply oversold (WARN)
    "rsi_overbought": 70.0,        # Above this = overbought (FAIL)
    "sector_rs_min": -0.05,        # Stock must not underperform sector by > 5%
    "volume_min_ratio": 0.5,       # Volume must be > 50% of average
    "debt_equity_max": 1.5,        # Long-term conservative threshold
    "roe_min": 15.0,               # Minimum ROE for positional/long-term quality
    "revenue_cagr_min": 0.10,      # Target 10% CAGR for growth
    "eps_cagr_min": 0.12,          # Target 12% EPS CAGR
    "max_pe": 50.0                 # Hard valuation ceiling
}