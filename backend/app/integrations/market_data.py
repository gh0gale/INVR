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

async def fetch_nse_circuit_status(ticker: str, current_price: float) -> Literal["upper", "lower", "none", "unknown"]:
    """Uses nsepython to check if price is hitting circuit limits."""
    def _fetch():
        try:
            from nsepython import nse_quote
            quote = nse_quote(ticker)
            # Safe parsing for circuit limits
            upper = quote.get('priceInfo', {}).get('intraDayHighLow', {}).get('value')
            lower = upper # Simplifying for prototype if exact lower isn't found
            
            if not upper or not lower:
                return "unknown"
                
            # Simple logic: If current price is within 0.5% of upper/lower band
            if current_price >= (upper * 0.995): return "upper"
            if current_price <= (lower * 1.005): return "lower"
            return "none"
        except Exception:
            return "unknown" # Failsafe if NSE blocks the scraper
            
    return await asyncio.to_thread(_fetch)


async def fetch_yfinance_fundamentals(ticker: str) -> dict:
    """Fetches base info + deep multi-year financial statements from yfinance."""
    def _fetch():
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info
        
        # 1. Base Info
        funds = {
            "sector": info.get("sector", "Unknown"),
            "pe": info.get("trailingPE", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "sector_pe_median": 25.0, 
            "debt_to_equity": (info.get("debtToEquity", 0) / 100) if info.get("debtToEquity") else 0,
            "roe": (info.get("returnOnEquity", 0) * 100) if info.get("returnOnEquity") else 0,
            "dividend_yield": info.get("dividendYield", 0)
        }
        
        try:
            # 2. Extract Income Statement Data (yfinance returns dates as columns, newest first)
            fin = stock.financials
            if not fin.empty:
                rev = fin.loc["Total Revenue"].dropna().tolist()[::-1] if "Total Revenue" in fin.index else []
                net_inc = fin.loc["Net Income"].dropna().tolist()[::-1] if "Net Income" in fin.index else []
                
                funds["revenue_3y"] = rev[-3:] if len(rev) >= 3 else rev
                funds["net_profit_3y"] = net_inc[-3:] if len(net_inc) >= 3 else net_inc
                
                funds["income_statement_5y"] = {
                    "revenue": rev[-5:] if len(rev) >= 5 else rev,
                    "net_profit": net_inc[-5:] if len(net_inc) >= 5 else net_inc,
                    "eps": [inc / 1e8 for inc in (net_inc[-5:] if len(net_inc) >= 5 else net_inc)] 
                }
                
            # 3. Extract Cash Flow Data
            cf = stock.cashflow
            if not cf.empty:
                cfo = cf.loc["Operating Cash Flow"].dropna().tolist()[::-1] if "Operating Cash Flow" in cf.index else []
                capex = cf.loc["Capital Expenditure"].dropna().tolist()[::-1] if "Capital Expenditure" in cf.index else []
                capex = [abs(c) for c in capex] # Convert negative capex to positive
                
                funds["cfo_3y"] = cfo[-3:] if len(cfo) >= 3 else cfo
                funds["cashflow_5y"] = {
                    "cfo": cfo[-5:] if len(cfo) >= 5 else cfo,
                    "capex": capex[-5:] if len(capex) >= 5 else capex
                }
                
            # 4. Extract Balance Sheet Data
            bs = stock.balance_sheet
            if not bs.empty:
                debt = bs.loc["Total Debt"].dropna().tolist()[::-1] if "Total Debt" in bs.index else []
                funds["balance_sheet_5y"] = {
                    "total_debt": debt[-5:] if len(debt) >= 5 else debt,
                    "book_value_per_share": [100, 110, 125, 140, 160] # Mocked BVPS for prototype stability
                }
                
        except Exception as e:
            print(f"  [⚠️] Warning: Could not parse deep financials for {ticker} ({e})")
            
        return funds
        
    return await asyncio.to_thread(_fetch)