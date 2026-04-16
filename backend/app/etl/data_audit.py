import asyncio
import json
from market_fetcher import MarketFetcher
import sys
import os

# Put app root in path so we can import services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

async def audit_data(ticker="RELIANCE.NS"):
    print(f"\n" + "="*80)
    print(f"DATA AUDIT & REPORT: {ticker}")
    print("="*80 + "\n")

    fetcher = MarketFetcher(ticker)
    success = await fetcher.fetch_all()
    if not success:
        print(f"Error: Failed to fetch data for {ticker}")
        return
        
    payload = fetcher.get_market_data_payload()
    
    # Mapping of Analyst Files to the keys they actually use
    audit_map = {
        "FUNDAMENTAL (fundamental.py)": [
            "roe", "roce", "debt_to_equity", "current_ratio", "free_cash_flow", 
            "market_cap", "total_assets", "current_assets", "current_liabilities", 
            "retained_earnings", "ebit", "total_liabilities"
        ],
        "VALUATION (valuation.py)": [
            "current_pe", "forward_pe", "peg_ratio", "price_to_book", 
            "ev_to_ebitda", "dividend_yield", "trailing_eps", "current_price"
        ],
        "TECHNICAL (technical.py)": [
            "current_price", "rsi_14", "macd_line", "macd_signal", "ema_50", 
            "ema_200", "vwap_20d", "bb_upper", "bb_lower"
        ],
        "QUANTITATIVE (quantitative.py)": [
            "beta_calc", "sharpe_ratio", "sortino_ratio", "max_drawdown", "var_95"
        ],
        "DERIVATIVE (derivative.py)": [
            "has_options", "put_call_ratio", "max_pain", "current_price", "avg_implied_volatility"
        ],
        "SENTIMENT (sentiment.py)": [
            "recent_news_headlines", "india_vix", "fii_dii_net", "rbi_repo_rate"
        ]
    }
    
    print(f"{'ANALYST GROUP / KEY':<40} | {'STATUS':<10} | {'VALUE'}")
    print("-" * 80)
    
    for group, keys in audit_map.items():
        print(f"\n{group}")
        print("-" * len(group))
        for key in keys:
            fetched = key in payload
            status = "[x]" if fetched else "[ ] MISSING"
            
            if fetched:
                raw_val = payload.get(key)
                if key == "recent_news_headlines":
                    val_str = f"Found {len(raw_val)} headlines"
                elif isinstance(raw_val, float):
                    val_str = f"{raw_val:.4f}"
                else:
                    val_str = str(raw_val)
                # Truncate if too long
                if len(val_str) > 40:
                    val_str = val_str[:37] + "..."
            else:
                val_str = "N/A"
            
            print(f"  {key:<37} | {status:<10} | {val_str}")

if __name__ == "__main__":
    ticker_to_audit = "RELIANCE.NS"
    if len(sys.argv) > 1:
        ticker_to_audit = sys.argv[1]
    asyncio.run(audit_data(ticker_to_audit))
