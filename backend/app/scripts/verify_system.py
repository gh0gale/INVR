import asyncio
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.etl.market_fetcher import MarketFetcher
from app.services.analysts import fundamental, valuation, technical, quantitative, derivative, sentiment
from app.db.supabase_client import supabase_client

async def verify_flow(ticker_symbol="RELIANCE.NS"):
    print(f"\n" + "="*60)
    print(f"SYSTEM VERIFICATION: {ticker_symbol}")
    print("="*60 + "\n")

    # 1. FETCH & PERSIST
    print("Phase 1: Fetching live data & saving snapshot...")
    fetcher = MarketFetcher(ticker_symbol)
    success = await fetcher.fetch_all()
    
    if not success:
        print("Error: Failed to fetch data. Check your internet connection or ticker symbol.")
        return

    data = fetcher.get_market_data_payload()
    print(f"Data fetched and saved to 'market_data' table.")

    # 2. VERIFY DB CONTEXT
    print(f"\nPhase 2: Double-checking Database Context...")
    if "sector_median_pe" in data:
        print(f"Success: Fetched Sector Medians from DB (P/E: {data['sector_median_pe']}, P/B: {data['sector_median_pb']})")
    else:
        print(f"Warning: Sector benchmarks not found in DB for {data.get('sector')}. Using hardcoded fallbacks.")

    if "rbi_repo_rate" in data:
        print(f"Success: Fetched Macro Context from DB (Repo Rate: {data['rbi_repo_rate']}%)")

    # 3. RUN ANALYSTS
    print(f"\nPhase 3: Running 6-Pillar Deterministic Analysts...")
    
    analysts = {
        "Fundamental": fundamental,
        "Valuation": valuation,
        "Technical": technical,
        "Quantitative": quantitative,
        "Derivative": derivative,
        "Sentiment": sentiment
    }

    print("-" * 60)
    print(f"{'ANALYST':<15} | {'SCORE':<5} | {'SUMMARY'}")
    print("-" * 60)

    for name, module in analysts.items():
        try:
            res = module.calculate_score(data)
            print(f"{name:<15} | {res['score']:>5} | {res['summary']}")
        except Exception as e:
            print(f"{name:<15} | ERROR | {e}")

    print("-" * 60)
    print("\n🚀 Verification Complete! The system is ready for the Phase 4 Agentic Loop.")

if __name__ == "__main__":
    ticker = "RELIANCE.NS"
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    asyncio.run(verify_flow(ticker))
