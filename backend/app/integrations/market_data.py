import asyncio
import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Optional

logger = logging.getLogger(__name__)


def _num(value) -> Optional[float]:
    """A finite float, or None. yfinance mixes None, NaN, 'Infinity' and absent keys."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return v


def _row(df: Optional[pd.DataFrame], *names: str) -> Optional[pd.Series]:
    """The first statement row present, indexed by period end. None if none is."""
    if df is None or df.empty:
        return None
    for name in names:
        if name in df.index:
            return pd.to_numeric(df.loc[name], errors="coerce")
    return None


def _oldest_first(series: Optional[pd.Series]) -> List[float]:
    if series is None:
        return []
    return [float(v) for v in series.dropna().sort_index().tolist()]


def _ratio_pct(num: Optional[pd.Series], den: Optional[pd.Series]) -> List[float]:
    """num/den x100 per period, aligned on the period end, oldest first.

    Aligned by date rather than position: two statement rows can have different
    missing years, and dividing them positionally pairs one year's income with
    another year's equity.
    """
    if num is None or den is None:
        return []
    both = pd.concat([num, den], axis=1, join="inner").dropna()
    both = both[both.iloc[:, 1] > 0].sort_index()
    return [round(float(n / d * 100.0), 4) for n, d in both.itertuples(index=False)]

async def fetch_yfinance_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetches OHLCV data. Adds .NS for Indian markets. Uses exact-date fallback to prevent yfinance glitches."""
    def _fetch():
        # Index tickers (^CNXFIN, ^NSEBANK, etc.) must never get .NS appended
        if ticker.startswith("^"):
            clean_ticker = ticker
        else:
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

async def fetch_nse_circuit_status(ticker: str, current_price: float) -> str:
    """'upper' / 'lower' / 'none' from NSE's published price band, else 'unknown'.

    NSE takes the bare symbol. This used to pass 'RELIANCE.NS', which NSE never
    recognises, so the call failed on every run and returned 'unknown' - and
    the Gold layer scored 'unknown' as a PASS (audit DATA-01). It also invented
    a band when NSE sent none: the intraday high as the upper limit and 90% of
    it as the lower. Neither is a circuit limit. Now the band is NSE's or it is
    'unknown', and Gold skips the gate rather than passing it.
    """
    symbol = ticker.split(".")[0].upper()

    def _fetch():
        try:
            from nsepython import nse_quote
            quote = nse_quote(symbol) or {}
            price_info = quote.get("priceInfo") or {}
            upper = _num(price_info.get("upperCP"))
            lower = _num(price_info.get("lowerCP"))
            if not upper or not lower:
                return "unknown"

            # Within 0.5% of a band counts as at the band.
            if current_price >= (upper * 0.995): return "upper"
            if current_price <= (lower * 1.005): return "lower"
            return "none"
        except Exception as e:
            logger.info("NSE price band unavailable for %s: %s", symbol, e)
            return "unknown"

    return await asyncio.to_thread(_fetch)


async def fetch_yfinance_fundamentals(ticker: str) -> dict:
    """Base info plus multi-year statements from yfinance.

    Every field is the provider's value or None. Nothing is defaulted to a
    plausible number (audit DATA-02): a missing debt/equity used to arrive as
    0 and score a balance-sheet PASS, a missing ROE as 0 and score a WARN, a
    missing P/E as 0 and pass the valuation ceiling, and a sector P/E that no
    source provides as a hardcoded 25.0.
    """
    def _fetch():
        # Index tickers (^CNXFIN, ^NSEBANK, etc.) must never get .NS appended
        if ticker.startswith("^"):
            clean_ticker = ticker
        else:
            clean_ticker = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
        stock = yf.Ticker(clean_ticker)
        info = stock.info or {}

        pe = _num(info.get("trailingPE"))
        pe = pe if pe and pe > 0 else None   # undefined for a loss-maker
        shares = _num(info.get("sharesOutstanding")) or _num(info.get("impliedSharesOutstanding"))

        # Units are converted here, where they are known, not guessed later
        # (audit DATA-04). yfinance reports debt/equity as a percentage and ROE
        # as a fraction, always. Silver used to infer the unit from magnitude -
        # "above 10 must be a percentage" - so INFY's 9.5 (0.095x) was read as
        # 9.5x and every low-debt company between 1.5 and 10 was flagged as
        # dangerously leveraged.
        de_pct = _num(info.get("debtToEquity"))
        roe_frac = _num(info.get("returnOnEquity"))

        # 1. Base info, in the provider's own units. Silver normalises ROE
        # (a fraction) and debt/equity (a percentage) before any comparison.
        funds = {
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "trailingPE": pe,
            "trailingEps": _num(info.get("trailingEps")),
            "returnOnEquity": roe_frac,
            "debtToEquity": de_pct,
            "roe_pct": roe_frac * 100.0 if roe_frac is not None else None,
            "debt_to_equity_x": de_pct / 100.0 if de_pct is not None and de_pct >= 0 else None,
            "revenueGrowth": _num(info.get("revenueGrowth")),
            "earningsGrowth": _num(info.get("earningsGrowth")),
            "dividend_yield": _num(info.get("dividendYield")),
            # No `sector_pe_median`: no free source publishes one for Indian
            # sectors (NSE's quote API returns nothing to scripted clients as of
            # 2026-09). Absent is honest; a constant is not (audit P1-03).
            "ratios": {
                "pe": pe,
                "roe_5y": [],
                "debt_to_equity_trend": []
            }
        }

        try:
            # 2. Income statement
            fin = stock.financials
            rev_s = _row(fin, "Total Revenue")
            ni_s = _row(fin, "Net Income", "Net Income Common Stockholders")
            if fin is not None and not fin.empty:
                rev = _oldest_first(rev_s)
                net_inc = _oldest_first(ni_s)

                funds["revenue_3y"] = rev[-3:]
                funds["net_profit_3y"] = net_inc[-3:]

                # Reported EPS where the statement has it. Net income over
                # today's share count ignores dilution, and the old code divided
                # by 1 when the count was missing.
                eps = _oldest_first(_row(fin, "Diluted EPS", "Basic EPS"))
                if not eps and shares:
                    eps = [inc / shares for inc in net_inc]

                funds["income_statement_5y"] = {
                    "revenue": rev[-5:],
                    "net_profit": net_inc[-5:],
                    "eps": eps[-5:],
                }

                # Operating margin per year. Silver classifies the trend; it
                # was read from a key nothing populated, so every stock was
                # reported as having "stable" margins.
                funds["opm_trend"] = _ratio_pct(_row(fin, "Operating Income", "EBIT"), rev_s)[-5:]

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
            if bs is not None and not bs.empty:
                debt = _oldest_first(_row(bs, "Total Debt"))
                funds["balance_sheet_5y"] = {
                    "total_debt": debt[-5:],
                }

                equity_s = _row(bs, "Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity")
                equity = _oldest_first(equity_s)
                funds["balance_sheet_5y"]["book_value_per_share"] = (
                    [round(e / shares, 2) for e in equity[-5:]] if (equity and shares) else []
                )

                # ROE per year from the statements. yfinance's `returnOnEquity`
                # is empty for most NSE names (12 of 18 large caps checked on
                # 2026-09-13), which left the ROE gate deciding on a default.
                roe_hist = _ratio_pct(ni_s, equity_s)
                funds["ratios"]["roe_5y"] = roe_hist[-5:]
                if funds["returnOnEquity"] is None and roe_hist:
                    funds["returnOnEquity"] = roe_hist[-1] / 100.0
                    funds["roe_pct"] = roe_hist[-1]
                    funds["roe_source"] = "statements"

        except Exception as e:
            logger.warning("Could not parse deep financials for %s (%s)", ticker, e)
            
        return funds
        
    return await asyncio.to_thread(_fetch)