from pydantic import BaseModel
from typing import Optional

class SilverMetrics(BaseModel):
    # --- Structural Identifiers ---
    ticker: str
    timeframe: str
    current_price: float
    current_volume: float

    # --- Macro / Top-Down Filters ---
    market_regime: Optional[str] = "neutral"  # "bullish", "bearish", "neutral"

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
    debt_flag: Optional[bool] = None
    institutional_bias: Optional[str] = None  # "buyer", "seller", "neutral"

    # --- Positional & Long-Term Core Fundamentals ---
    revenue_cagr_3y: Optional[float] = None
    profit_cagr_3y: Optional[float] = None
    opm_trend: Optional[str] = None  # "expanding", "stable", "contracting"
    roe_vs_cost_of_capital: Optional[bool] = None
    cfo_vs_net_profit: Optional[float] = None
    promoter_holding_trend: Optional[str] = None  # "accumulating", "stable", "decreasing"
    valuation_comfort: Optional[float] = None

    # --- Long-Term Compounder Metrics ---
    revenue_cagr_5y: Optional[float] = None
    eps_cagr_5y: Optional[float] = None
    fcf_conversion: Optional[float] = None
    roe_consistency_5y: Optional[str] = None  # "consistent_moat", "average", "volatile"
    debt_trajectory: Optional[str] = None  # "deleveraging", "stable", "leveraging"
    book_value_growth: Optional[float] = None
    promoter_conviction_trend: Optional[float] = None
    pe_band_vs_growth: Optional[float] = None
    dividend_consistency: Optional[bool] = None