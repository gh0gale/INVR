import asyncio
import yfinance as yf
import pandas as pd
from typing import Literal

async def fetch_yfinance_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetches OHLCV data. Adds .NS for Indian markets."""
    def _fetch():
        stock = yf.Ticker(f"{ticker}.NS")
        return stock.history(period=period, interval=interval)
    
    df = await asyncio.to_thread(_fetch)
    if df.empty:
        raise ValueError(f"No price data found for {ticker}")
    return df

async def fetch_yfinance_fundamentals(ticker: str) -> dict:
    def _fetch():
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info
        return {
            "trailingPE": info.get("trailingPE"),
            "debtToEquity": info.get("debtToEquity"),
            "returnOnEquity": info.get("returnOnEquity"),
            "sector": info.get("sector")
        }
    return await asyncio.to_thread(_fetch)

async def fetch_nse_circuit_status(ticker: str, current_price: float) -> Literal["upper", "lower", "none", "unknown"]:
    """Uses nsepython to check if price is hitting circuit limits."""
    def _fetch():
        try:
            from nsepython import nse_quote
            quote = nse_quote(ticker)
            upper = quote['priceInfo']['intraDayHighLow']['value'] # Approximation mapping
            lower = quote['priceInfo']['intraDayHighLow']['value']
            
            # Simple logic: If current price is within 0.5% of upper/lower band
            if current_price >= (upper * 0.995): return "upper"
            if current_price <= (lower * 1.005): return "lower"
            return "none"
        except Exception:
            return "unknown" # Failsafe if NSE blocks the scraper
            
    return await asyncio.to_thread(_fetch)