import pandas as pd
from app.schemas.bronze import BronzePayload
from app.schemas.silver import SilverMetrics

def compute_silver_metrics(bronze: BronzePayload) -> SilverMetrics:
    """
    Transforms Bronze time-series data into Silver statistical metrics.
    Calculates technical indicators using native Pandas vectorization.
    """
    if bronze.price_history is None or bronze.price_history.empty:
        raise ValueError(f"Cannot compute Silver metrics: Price history missing for {bronze.ticker}")

    # Copy to avoid SettingWithCopy warnings and format index
    df = bronze.price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, unit='ms')

    # --- 1. Compute Simple Moving Averages ---
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['VOL_SMA_20'] = df['Volume'].rolling(window=20).mean()

    # --- 2. Compute Relative Strength Index (RSI 14) ---
    # Using Wilder's Smoothing Method (Industry Standard)
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))

    # --- 3. Compute Average True Range (ATR 14) ---
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift(1)).abs()
    low_close = (df['Low'] - df['Close'].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR_14'] = true_range.ewm(alpha=1/14, adjust=False).mean()
    
    # --- 4. Extract Latest Values ---
    latest = df.iloc[-1]
    
    def safe_get(col_name: str) -> float | None:
        val = latest.get(col_name)
        return float(val) if pd.notna(val) else None

    current_price = float(latest['Close'])
    sma_50 = safe_get('SMA_50')
    sma_200 = safe_get('SMA_200')
    
    # --- 5. Compute the SMA Gap Percentage (For Positional Death Cross) ---
    sma_gap_pct = None
    if sma_50 is not None and sma_200 is not None:
        sma_gap_pct = abs(sma_50 - sma_200) / sma_200 * 100

    # --- 6. Compute Sector Relative Strength (For Swing/Positional/Long-Term) ---
    stock_vs_sector_rs = None
    if bronze.sector_history is not None and not bronze.sector_history.empty:
        sector_df = bronze.sector_history.copy()
        if not isinstance(sector_df.index, pd.DatetimeIndex):
            sector_df.index = pd.to_datetime(sector_df.index, unit='ms')
            
        lookback = 20 # Compare momentum over the last 20 periods
        if len(df) >= lookback and len(sector_df) >= lookback:
            # Stock return over lookback
            stock_past = df['Close'].iloc[-lookback]
            stock_ret = (current_price - stock_past) / stock_past
            
            # Sector return over lookback
            sector_current = sector_df['Close'].iloc[-1]
            sector_past = sector_df['Close'].iloc[-lookback]
            sector_ret = (sector_current - sector_past) / sector_past
            
            # Outperformance Delta
            stock_vs_sector_rs = float(stock_ret - sector_ret)

    # Build and return the final Silver layer struct
    return SilverMetrics(
        ticker=bronze.ticker,
        current_price=current_price,
        sma_20=safe_get('SMA_20'),
        sma_50=sma_50,
        sma_200=sma_200,
        rsi_14=safe_get('RSI_14'),
        atr_14=safe_get('ATR_14'),
        volume_avg_20=safe_get('VOL_SMA_20'),
        current_volume=float(latest['Volume']),
        stock_vs_sector_rs=stock_vs_sector_rs,
        sma_gap_pct=sma_gap_pct
    )