import os
import sys
import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Run either as `python -m scripts.grade_ledger` or `python backend/scripts/grade_ledger.py`.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts._grading import resolve_outcome

load_dotenv(override=True)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Grade swing trades after 15 days, positional after 90, long-term after 365
TIMEFRAMES = {"swing": 15, "positional": 90, "long_term": 365}

def grade_trades():
    print("🔍 ORACLE: Grading Matured Predictions against Market Reality...")
    
    for timeframe, days_to_wait in TIMEFRAMES.items():
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_wait)).date().isoformat()
        
        pending_rows = supabase.table("algorithmic_ledger").select("*").eq("actual_outcome", "PENDING").eq("timeframe", timeframe).lte("date", cutoff_date).execute().data
            
        if not pending_rows:
            print("✅ No matured pending rows to grade today.")
            continue
            
        print(f" ⚙️ Found {len(pending_rows)} matured {timeframe} predictions. Fetching reality...")
        
        for row in pending_rows:
            ticker = row["ticker"]
            start_date = row["date"]
            verdict = row["gold_verdict"].get("verdict", "MONITOR")
            entry_price = row["silver_state"].get("current_price")
            
            # Fetch Future Reality
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = start_dt + timedelta(days=days_to_wait + 10)
            
            try:
                time.sleep(0.5)
                df = yf.download(ticker, start=start_dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d"), progress=False)
                if df.empty: continue
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                future_df = df.head(days_to_wait)
                
                max_high = float(future_df['High'].max())
                min_low = float(future_df['Low'].min())
                
                # Intent evaluation, shared with the historical simulator so
                # backtest and live outcomes are directly comparable.
                outcome = resolve_outcome(
                    verdict=verdict,
                    entry_price=entry_price,
                    setup=row["gold_verdict"].get("trade_setup"),
                    max_high=max_high,
                    min_low=min_low,
                )
                
                # Update DB
                supabase.table("algorithmic_ledger").update({"actual_outcome": outcome, "max_favorable_excursion": max_high, "max_adverse_excursion": min_low}).eq("log_id", row["log_id"]).execute()
            except Exception as e:
                print(f"Failed to grade {ticker}: {e}")
                
    print("✅ GRADING COMPLETE.")

if __name__ == "__main__":
    grade_trades()