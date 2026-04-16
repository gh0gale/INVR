import yfinance as yf
import pandas as pd
import numpy as np
import logging
from app.db.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class MarketFetcher:
    """
    Enriched wrapper for yfinance to compute missing technical and fundamental metrics.
    Prepared for 6 phase AI intelligence analysts.
    """
    
    def __init__(self, ticker_symbol: str):
        if not ticker_symbol.endswith(".NS") and not ticker_symbol.endswith(".BO") and not ticker_symbol.startswith("^"):
            self.symbol = f"{ticker_symbol}.NS"
        else:
            self.symbol = ticker_symbol
        
        self.ticker = yf.Ticker(self.symbol)
        self.info = {}
        self.history = pd.DataFrame()
        self.financials = pd.DataFrame()
        self.balance_sheet = pd.DataFrame()
        self.cashflow = pd.DataFrame()
        self.options = []
        
        self.nifty_history = pd.DataFrame()
        self.vix_info = {}
        self.macro_context = {}
        self.sector_benchmark = {}

    async def fetch_all(self):
        """Fetches info, 3 years of history, Nifty50 history, Options and News."""
        try:
            self.info = self.ticker.info
            self.history = self.ticker.history(period="3y")
            self.financials = self.ticker.financials
            self.balance_sheet = self.ticker.balance_sheet
            self.cashflow = self.ticker.cashflow
            
            # Additional API calls
            try:
                self.options = self.ticker.options
            except Exception:
                self.options = []

            # Fetch benchmarks from DB
            try:
                # 1. Macro Context
                macro_res = supabase_client.table("macro_context").select("*").eq("id", 1).execute()
                if macro_res.data:
                    self.macro_context = macro_res.data[0]
                
                # 2. Sector Benchmarks
                sector = self.info.get("sector")
                if sector:
                    benchmark_res = supabase_client.table("sector_benchmarks").select("*").eq("sector_name", sector).execute()
                    if benchmark_res.data:
                        self.sector_benchmark = benchmark_res.data[0]
            except Exception as e:
                logger.warning(f"Database context fetch error: {e}")

            # Fetch benchmark and VIX from YF (as fallback)
            try:
                nifty = yf.Ticker("^NSEI")
                self.nifty_history = nifty.history(period="3y")
                vix = yf.Ticker("^INDIAVIX")
                vix_hist = vix.history(period="5d")
                # Prefer DB VIX if exists, otherwise YF
                self.vix_info = {"current_vix": self.macro_context.get("india_vix") or (vix_hist['Close'].iloc[-1] if not vix_hist.empty else 15.0)}
            except Exception as e:
                logger.warning(f"Failed to fetch market benchmarks: {e}")
            
            # Save the snapshot to DB
            if not self.history.empty:
                await self.save_to_db()

            return not self.history.empty
        except Exception as e:
            logger.error(f"Error fetching data for {self.symbol}: {e}")
            return False

    async def save_to_db(self):
        """Persists the final payload to Supabase market_data table."""
        try:
            payload = self.get_market_data_payload()
            if payload:
                # Remove non-serializable or complex fields not in schema
                # Match schema keys
                supabase_client.table("market_data").upsert(payload).execute()
                logger.info(f"✅ Saved snapshot for {self.symbol} to database.")
        except Exception as e:
            logger.error(f"❌ Failed to save snapshot to DB: {e}")

    def get_market_data_payload(self) -> dict:
        if not self.info or self.history.empty:
            return {}

        payload = {
            "ticker": self.symbol,
            "sector": self.info.get("sector"),
            "industry": self.info.get("industry")
        }

        # --- FUNDAMENTAL & VALUATION ---
        payload["current_price"] = self.info.get("currentPrice") or self.info.get("regularMarketPrice")
        payload["market_cap"] = self.info.get("marketCap")
        payload["trailing_eps"] = self.info.get("trailingEps")
        payload["forward_eps"] = self.info.get("forwardEps")
        payload["current_pe"] = self.info.get("trailingPE")
        payload["forward_pe"] = self.info.get("forwardPE")
        payload["peg_ratio"] = self.info.get("pegRatio")
        payload["price_to_book"] = self.info.get("priceToBook")
        payload["ev_to_ebitda"] = self.info.get("enterpriseToEbitda")
        payload["dividend_yield"] = self.info.get("dividendYield")
        
        payload["roe"] = self.info.get("returnOnEquity")
        payload["roce"] = self.info.get("returnOnAssets")
        payload["debt_to_equity"] = self.info.get("debtToEquity")
        payload["current_ratio"] = self.info.get("currentRatio")
        payload["free_cash_flow"] = self.info.get("freeCashflow")
        
        # Safe extraction from statements for DuPont & Z-Score
        try:
            if not self.financials.empty and not self.balance_sheet.empty:
                payload["net_income"] = self.financials.loc['Net Income'].iloc[0] if 'Net Income' in self.financials.index else None
                payload["total_revenue"] = self.financials.loc['Total Revenue'].iloc[0] if 'Total Revenue' in self.financials.index else None
                payload["ebit"] = self.financials.loc['EBIT'].iloc[0] if 'EBIT' in self.financials.index else None
                
                payload["total_assets"] = self.balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in self.balance_sheet.index else None
                payload["total_equity"] = self.balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in self.balance_sheet.index else None
                payload["total_liabilities"] = self.balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0] if 'Total Liabilities Net Minority Interest' in self.balance_sheet.index else None
                
                payload["current_assets"] = self.balance_sheet.loc['Current Assets'].iloc[0] if 'Current Assets' in self.balance_sheet.index else None
                payload["current_liabilities"] = self.balance_sheet.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in self.balance_sheet.index else None
                payload["retained_earnings"] = self.balance_sheet.loc['Retained Earnings'].iloc[0] if 'Retained Earnings' in self.balance_sheet.index else None
        except Exception as e:
            logger.debug(f"Statement parsing error: {e}")

        # --- FALLBACK CALCULATORS ---
        # 1. ROE (Net Income / Stockholders Equity)
        if not payload.get("roe") and payload.get("net_income") and payload.get("total_equity"):
            payload["roe"] = payload["net_income"] / payload["total_equity"]
            
        # 2. Current Ratio (Current Assets / Current Liabilities)
        if not payload.get("current_ratio") and payload.get("current_assets") and payload.get("current_liabilities"):
            payload["current_ratio"] = payload["current_assets"] / payload["current_liabilities"]
            
        # 3. Free Cash Flow (Operating Cash Flow - Capital Expenditure)
        if not payload.get("free_cash_flow") and not self.cashflow.empty:
            try:
                ocf = self.cashflow.loc['Operating Cash Flow'].iloc[0] if 'Operating Cash Flow' in self.cashflow.index else 0
                capex = abs(self.cashflow.loc['Capital Expenditure'].iloc[0]) if 'Capital Expenditure' in self.cashflow.index else 0
                payload["free_cash_flow"] = float(ocf - capex)
            except: pass

        # 4. ROCE (EBIT / (Total Assets - Current Liabilities))
        if not payload.get("roce") and payload.get("ebit") and payload.get("total_assets") and payload.get("current_liabilities"):
            capital_employed = payload["total_assets"] - payload["current_liabilities"]
            if capital_employed > 0:
                payload["roce"] = payload["ebit"] / capital_employed

        # 5. PEG Ratio (PE / (Revenue Growth * 100))
        if not payload.get("peg_ratio") and payload.get("current_pe") and self.info.get("revenueGrowth"):
            rev_growth_pct = self.info.get("revenueGrowth") * 100
            if rev_growth_pct > 0:
                payload["peg_ratio"] = payload["current_pe"] / rev_growth_pct

        # --- TECHNICAL ---
        close = self.history['Close']
        high = self.history['High']
        low = self.history['Low']
        volume = self.history['Volume']
        
        if len(close) >= 200:
            payload["sma_50"] = float(close.tail(50).mean())
            payload["sma_200"] = float(close.tail(200).mean())
            payload["ema_50"] = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
            payload["ema_200"] = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            payload["rsi_14"] = float(100 - (100 / (1 + rs.iloc[-1])))

            # MACD
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            payload["macd_line"] = float(macd.iloc[-1])
            payload["macd_signal"] = float(signal.iloc[-1])
            
            # Bollinger Bands (20-day, 2 std dev)
            std_20 = close.rolling(window=20).std()
            sma_20 = close.rolling(window=20).mean()
            payload["bb_upper"] = float((sma_20 + 2 * std_20).iloc[-1])
            payload["bb_lower"] = float((sma_20 - 2 * std_20).iloc[-1])
            payload["bb_mid"] = float(sma_20.iloc[-1])
            
            # VWAP (recent 20 days)
            recent_v = volume.tail(20)
            recent_typical = ((high.tail(20) + low.tail(20) + close.tail(20)) / 3)
            payload["vwap_20d"] = float((recent_typical * recent_v).sum() / recent_v.sum()) if recent_v.sum() > 0 else float(close.iloc[-1])
            
            # ADX proxy (True Range base)
            tr1 = high.tail(14) - low.tail(14)
            tr2 = abs(high.tail(14) - close.shift(1).tail(14))
            tr3 = abs(low.tail(14) - close.shift(1).tail(14))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            payload["atr_14"] = float(tr.mean())

            # Historical volatility
            payload["volatility_30d"] = float(close.tail(30).pct_change().std() * np.sqrt(252))

        # --- QUANTITATIVE ---
        if not self.nifty_history.empty and len(close) > 252:
            try:
                # Align dates
                stock_ret = close.pct_change().dropna()
                nifty_ret = self.nifty_history['Close'].pct_change().dropna()
                aligned_returns = pd.concat([stock_ret, nifty_ret], axis=1, join='inner').tail(252*3) # Up to 3 years
                if not aligned_returns.empty:
                    s_ret = aligned_returns.iloc[:,0]
                    n_ret = aligned_returns.iloc[:,1]
                    
                    cov = np.cov(s_ret, n_ret)[0][1]
                    var = np.var(n_ret)
                    payload["beta_calc"] = float(cov / var) if var > 0 else float(self.info.get("beta", 1.0))
                    
                    # Sharpe & Sortino (Assuming 7% risk free rate for India)
                    rf_daily = 0.07 / 252
                    excess_ret = s_ret - rf_daily
                    payload["sharpe_ratio"] = float((excess_ret.mean() / s_ret.std()) * np.sqrt(252)) if s_ret.std() > 0 else 0
                    
                    downside_std = excess_ret[excess_ret < 0].std()
                    payload["sortino_ratio"] = float((excess_ret.mean() / downside_std) * np.sqrt(252)) if downside_std > 0 else 0
                    
                    # Max Drawdown
                    roll_max = close.cummax()
                    drawdown = close / roll_max - 1.0
                    payload["max_drawdown"] = float(drawdown.min())
                    
                    # VaR 95%
                    payload["var_95"] = float(np.percentile(s_ret, 5))
            except Exception as e:
                logger.debug(f"Quant calc error: {e}")

        # --- DERIVATIVE ---
        payload["has_options"] = len(self.options) > 0
        if payload["has_options"]:
            try:
                earliest_exp = self.options[0]
                chain = self.ticker.option_chain(earliest_exp)
                calls = chain.calls
                puts = chain.puts
                
                total_call_oi = calls['openInterest'].sum()
                total_put_oi = puts['openInterest'].sum()
                payload["put_call_ratio"] = float(total_put_oi / total_call_oi) if total_call_oi > 0 else 1.0
                
                # Approximate max pain
                strikes = sorted(set(calls['strike']).union(set(puts['strike'])))
                max_pain_strike = 0
                min_loss = float('inf')
                for strike in strikes:
                    call_loss = calls[calls['strike'] < strike]['openInterest'] * (strike - calls[calls['strike'] < strike]['strike'])
                    put_loss = puts[puts['strike'] > strike]['openInterest'] * (puts[puts['strike'] > strike]['strike'] - strike)
                    total_loss = call_loss.sum() + put_loss.sum()
                    if total_loss < min_loss:
                        min_loss = total_loss
                        max_pain_strike = strike
                        
                payload["max_pain"] = float(max_pain_strike)
                
                # We can't perfectly calculate IV percentile without historical options, but provide current avg
                payload["avg_implied_volatility"] = float((calls['impliedVolatility'].mean() + puts['impliedVolatility'].mean()) / 2)
            except Exception as e:
                logger.debug(f"Options calc error: {e}")

        # --- SENTIMENT & MACRO ---
        # 1. Macro
        payload["india_vix"] = self.vix_info.get("current_vix", 15.0)
        payload["rbi_repo_rate"] = self.macro_context.get("rbi_repo_rate", 6.5) 
        payload["fii_dii_net"] = self.macro_context.get("fii_dii_net", "neutral")
        
        # 2. Add Benchmarks for Analysts
        if self.sector_benchmark:
            payload["sector_median_pe"] = self.sector_benchmark.get("median_pe")
            payload["sector_median_pb"] = self.sector_benchmark.get("median_pb")
            payload["sector_avg_roe"] = self.sector_benchmark.get("avg_roe")

        # 3. News Sentences Proxy
        news_list = self.ticker.news
        headlines = [n.get("title", "") for n in news_list] if news_list else []
        payload["recent_news_headlines"] = headlines
        
        # Return cleaned dict (no NaN, match SQL schema keys)
        sql_cols = {
            "ticker", "sector", "industry", "current_price", "trailing_eps", "forward_eps",
            "revenue_growth_yoy", "net_profit_margin", "roe", "roce", "debt_to_equity",
            "current_ratio", "free_cash_flow", "retained_earnings", "sma_50", "sma_200",
            "ema_50", "ema_200", "rsi_14", "macd_line", "macd_signal", "bb_upper",
            "bb_lower", "bb_mid", "vwap_20d", "atr_14", "current_pe", "forward_pe",
            "peg_ratio", "price_to_book", "ev_to_ebitda", "dividend_yield", "beta_calc",
            "sharpe_ratio", "sortino_ratio", "volatility_30d", "max_drawdown", "var_95",
            "has_options", "put_call_ratio", "max_pain", "avg_implied_volatility"
        }
        
        cleaned = {}
        for k, v in payload.items():
            if v is not None:
                if isinstance(v, float) and np.isnan(v):
                    continue
                # Only include keys that are analysts' inputs or SQL columns
                if k in sql_cols or k.startswith("sector_") or k == "recent_news_headlines" or k == "india_vix" or k == "rbi_repo_rate" or k == "fii_dii_net":
                    cleaned[k] = v
        return cleaned
