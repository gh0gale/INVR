import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MarketFetcher:
    """
    Enriched wrapper for yfinance to compute missing technical and fundamental metrics.
    """
    
    def __init__(self, ticker_symbol: str):
        if not ticker_symbol.endswith(".NS") and not ticker_symbol.endswith(".BO"):
            self.symbol = f"{ticker_symbol}.NS"
        else:
            self.symbol = ticker_symbol
        
        self.ticker = yf.Ticker(self.symbol)
        self.info = {}
        self.history = pd.DataFrame()
        self.financials = pd.DataFrame()

    async def fetch_all(self):
        """Fetches info and 2 years of history to permit CAGR calculation."""
        try:
            self.info = self.ticker.info
            self.history = self.ticker.history(period="2y")
            # Only fetch financials for deep-dive metrics (CAGR)
            self.financials = self.ticker.financials
            return not self.history.empty
        except Exception as e:
            logger.error(f"Error fetching data for {self.symbol}: {e}")
            return False

    def get_market_data_payload(self) -> dict:
        if not self.info or self.history.empty:
            return {}

        # 1. Base Payload (Direct from info)
        payload = {
            "ticker": self.symbol,
            "sector": self.info.get("sector"),
            "industry": self.info.get("industry"),
            "current_price": self.info.get("currentPrice") or self.info.get("regularMarketPrice"),
            "trailing_eps": self.info.get("trailingEps"),
            "revenue_growth_yoy": self.info.get("revenueGrowth"),
            "net_profit_margin": self.info.get("profitMargins"),
            "roe": self.info.get("returnOnEquity"),
            "roce": self.info.get("returnOnAssets"),
            "debt_to_equity": self.info.get("debtToEquity"),
            "free_cash_flow": self.info.get("freeCashflow"),
            "promoter_holding": self.info.get("heldPercentInsiders"),
            "current_pe": self.info.get("trailingPE"),
            "peg_ratio": self.info.get("pegRatio"),
            "price_to_book": self.info.get("priceToBook"),
            "ev_to_ebitda": self.info.get("enterpriseToEbitda"),
            "beta_1y": self.info.get("beta"),
        }

        # 2. Technical Analysis
        close = self.history['Close']
        if len(close) >= 200:
            payload["sma_20"] = float(close.tail(20).mean())
            payload["sma_50"] = float(close.tail(50).mean())
            payload["sma_200"] = float(close.tail(200).mean())
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            payload["rsi_14"] = float(100 - (100 / (1 + rs.iloc[-1])))

            # MACD (12, 26, 9)
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            payload["macd_line"] = float(macd.iloc[-1])
            payload["macd_signal"] = float(signal.iloc[-1])

        # 3. Support & Resistance (Pivot Points - Standard)
        # Using 5-day window for recent support
        recent_window = self.history.tail(5)
        high = recent_window['High'].max()
        low = recent_window['Low'].min()
        last_close = close.iloc[-1]
        
        pivot = (high + low + last_close) / 3
        payload["support_level"] = float(2 * pivot - high) # S1
        payload["resistance_level"] = float(2 * pivot - low) # R1

        # 4. Fundamental Backfills (CAGR & ROE)
        # Calculate ROE fallback if missing
        if not payload.get("roe") and not self.financials.empty:
            try:
                # Net Income / Total Shareholder Equity (last year)
                net_income = self.financials.loc['Net Income'].iloc[0]
                equity = self.ticker.balance_sheet.loc['Stockholders Equity'].iloc[0]
                payload["roe"] = float(net_income / equity)
            except:
                pass

        # Calculate Revenue CAGR (3yr)
        if not self.financials.empty and 'Total Revenue' in self.financials.index:
            try:
                revs = self.financials.loc['Total Revenue']
                if len(revs) >= 3:
                    latest = revs.iloc[0]
                    oldest = revs.iloc[2] # 3 years ago
                    if oldest > 0:
                        payload["revenue_cagr_3y"] = float((latest / oldest)**(1/3) - 1)
            except:
                pass

        # 5. Valuation formulas (Graham Number)
        eps = payload.get("trailing_eps")
        pb = payload.get("price_to_book")
        curr_price = payload.get("current_price")
        if eps and pb and curr_price:
            bvps = curr_price / pb
            payload["graham_number"] = float(np.sqrt(max(0, 22.5 * eps * bvps)))

        # Volatility
        payload["volatility_30d"] = float(close.tail(30).pct_change().std() * np.sqrt(252))

        # 5. Clean and Return
        return {k: v for k, v in payload.items() if v is not None and not (isinstance(v, float) and np.isnan(v))}
