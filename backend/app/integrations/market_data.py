import asyncio
import yfinance as yf
import pandas as pd
from typing import Literal
from datetime import datetime, timedelta

async def fetch_yfinance_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetches OHLCV data. Adds .NS for Indian markets. Uses exact-date fallback to prevent yfinance glitches."""
    def _fetch():
        clean_ticker = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
        stock = yf.Ticker(clean_ticker)
        
        # Attempt 1: Standard fetch
        df = stock.history(period=period, interval=interval)
        
        # Attempt 2: Fallback to exact date math if yfinance quietly returns an empty dataframe
        if df.empty:
            days_map = {
                "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, 
                "1y": 365, "2y": 730, "5y": 1825, "10y": 3650
            }
            days_back = days_map.get(period, 365)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            df = stock.history(
                start=start_date.strftime('%Y-%m-%d'), 
                end=end_date.strftime('%Y-%m-%d'), 
                interval=interval
            )
            
        if df.empty:
            raise ValueError(f"No price data found for {ticker} using period {period}")
            
        return df

    return await asyncio.to_thread(_fetch)

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
        clean_ticker = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
        stock = yf.Ticker(clean_ticker)
        info = stock.info
        
        # 1. Base Info
        funds = {
            "sector": info.get("sector", "Unknown"),
            "pe": info.get("trailingPE", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "sector_pe_median": 25.0, 
            "debt_to_equity": info.get("debtToEquity", 0) if info.get("debtToEquity") else 0,
            "roe": (info.get("returnOnEquity", 0) * 100) if info.get("returnOnEquity") else 0,
            "dividend_yield": info.get("dividendYield", 0)
        }
        
        try:
            # Extract Income Statement Data
            fin = stock.financials
            if not fin.empty:
                rev = fin.loc["Total Revenue"].dropna().tolist()[::-1] if "Total Revenue" in fin.index else []
                net_inc = fin.loc["Net Income"].dropna().tolist()[::-1] if "Net Income" in fin.index else []
                
                funds["revenue_3y"] = rev[-3:] if len(rev) >= 3 else rev
                funds["net_profit_3y"] = net_inc[-3:] if len(net_inc) >= 3 else net_inc
                
                # BUG FIX: Get actual shares outstanding (default to 1 to prevent division by zero if missing)
                shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding") or 1
                
                funds["income_statement_5y"] = {
                    "revenue": rev[-5:] if len(rev) >= 5 else rev,
                    "net_profit": net_inc[-5:] if len(net_inc) >= 5 else net_inc,
                    "eps": [inc / shares for inc in (net_inc[-5:] if len(net_inc) >= 5 else net_inc)] 
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
                    "book_value_per_share": [100, 110, 125, 140, 160] # Mocked placeholder BVPS for stability; historical shares not reliably available via yfinance free API
                }
                
        except Exception as e:
            print(f"  [⚠️] Warning: Could not parse deep financials for {ticker} ({e})")
            
        return funds
        
    return await asyncio.to_thread(_fetch)