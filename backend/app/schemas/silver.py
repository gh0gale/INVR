from pydantic import BaseModel
from typing import Optional

class SilverMetrics(BaseModel):
    # --- Structural Identifiers ---
    ticker: str
    timeframe: str
    current_price: float
    current_volume: float

    # --- Macro / Top-Down Filters ---
    # None when no benchmark had 200 bars. It used to default to "neutral", so
    # every ledger row reported a regime that was never computed (DATA-03).
    market_regime: Optional[str] = None  # "bullish", "bearish", "neutral"
    # The index stock_vs_sector_rs and market_regime were measured against.
    benchmark_index: Optional[str] = None

    # --- Core Technical Metrics ---
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    atr_14: Optional[float] = None
    volume_avg_20: Optional[float] = None
    stock_vs_sector_rs: Optional[float] = None
    sma_gap_pct: Optional[float] = None

    # --- Swing Specific Fundamentals & Flows ---
    pe_vs_sector_avg: Optional[float] = None
    trailing_pe: Optional[float] = None
    debt_flag: Optional[bool] = None
    # Raw ratio behind debt_flag, normalised to a multiple (1.5 = 1.5x equity).
    # Recorded because a boolean has no distribution to resample, which is why
    # `debt_equity_max` had no drift check (audit NEW-BE-11b).
    debt_to_equity: Optional[float] = None
    institutional_bias: Optional[str] = None  # "buyer", "seller", "neutral"

    # --- Positional & Long-Term Core Fundamentals ---
    # NOTE: fields are declared here only once silver_service actually populates
    # them. Five placeholders were removed on 2026-08-18 (audit NEW-BE-13); they
    # had never been computed and serialised as null into every ledger row.
    revenue_cagr_3y: Optional[float] = None
    profit_cagr_3y: Optional[float] = None
    opm_trend: Optional[str] = None  # "expanding", "stable", "contracting"
    roe_vs_cost_of_capital: Optional[bool] = None
    # Raw ROE behind the flag, normalised to a percentage (18.0 = 18%).
    # Same reason as debt_to_equity above.
    roe_pct: Optional[float] = None
    valuation_comfort: Optional[float] = None

    # --- Long-Term Compounder Metrics ---
    revenue_cagr_5y: Optional[float] = None
    eps_cagr_5y: Optional[float] = None
    fcf_conversion: Optional[float] = None
    roe_consistency_5y: Optional[str] = None  # "consistent_moat", "average", "volatile"
    debt_trajectory: Optional[str] = None  # "deleveraging", "stable", "leveraging"
    pe_band_vs_growth: Optional[float] = None
