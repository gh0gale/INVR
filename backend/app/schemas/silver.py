from pydantic import BaseModel
from typing import Optional

class SilverMetrics(BaseModel):
    # --- Core Identifiers (Used in ALL types) ---
    ticker: str
    current_price: float
    current_volume: float
    
    # --- Trend Indicators ---
    # SMA 20: Micro/Short-term trend. 
    # -> Primary for [Intraday] (100 mins) and [Swing] (1 month).
    sma_20: Optional[float] = None
    
    # SMA 50: Medium-term/Structural support. 
    # -> Primary for [Swing], [Positional], and [Long-Term].
    sma_50: Optional[float] = None
    
    # SMA 200: Macro trend baseline. 
    # -> Primary for [Positional] (Death Cross) and [Long-Term].
    # -> Usually resolves to 'None' for Intraday/Swing due to limited row history.
    sma_200: Optional[float] = None
    
    # --- Momentum & Volatility Indicators ---
    # RSI 14: Overbought/Oversold tracking.
    # -> Crucial for [Intraday], [Swing], and [Positional]. Less relevant for Long-Term.
    rsi_14: Optional[float] = None
    
    # ATR 14: Average True Range (Absolute currency units).
    # -> Used for dynamic Stop-Loss calculations in [Intraday] and [Swing].
    atr_14: Optional[float] = None
    
    # VOL SMA 20: Baseline liquidity.
    # -> Used to filter out fake breakouts (Volume Spikes) in [Intraday] and [Swing].
    volume_avg_20: Optional[float] = None
    
    # --- Relative & Computed Metrics ---
    # Stock vs Sector RS: Outperformance Delta.
    # -> Mandatory for [Swing], [Positional], and [Long-Term]. Skipped in Intraday.
    stock_vs_sector_rs: Optional[float] = None
    
    # SMA Gap %: The percentage distance between SMA 50 and SMA 200.
    # -> Exclusively used by the [Positional] Gate to filter out Death Cross "Noise".
    sma_gap_pct: Optional[float] = None