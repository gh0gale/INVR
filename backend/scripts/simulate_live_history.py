import os
import sys
import time
import pandas as pd
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Ensure Python can find your app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.bronze import BronzePayload
from app.services.silver_service import compute_silver_metrics 
from app.services.gold_service import evaluate_hard_gates
from config.gate_thresholds import GATE_THRESHOLDS as TH

load_dotenv(override=True)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

TICKERS = ["RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS", "ICICIBANK.NS"]
LOOKAHEAD_DAYS = 15 # Standard swing trade horizon

def run_simulation():
    print("🚀 RUNNING TIME MACHINE: Simulating 2 years of live production using your Silver Layer...")
    batch_payloads = []
    
    for ticker in TICKERS:
        print(f"📡 Processing historical feed for {ticker}...")
        df = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df.empty: continue
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.dropna(inplace=True)
        
        # Walk forward through time (start at day 200 to allow SMAs to warm up)
        for i in range(200, len(df) - LOOKAHEAD_DAYS):
            historical_slice = df.iloc[:i+1].copy()
            simulated_date = df.index[i].date().isoformat()
            
            # 1. Build the Bronze Payload
            bronze = BronzePayload(
                ticker=ticker, 
                timeframe="swing", 
                circuit_status="none",
                price_history=historical_slice,
                sector_history=None, fundamentals=None, institutional_activity=None
            )
            
            # 2. Run YOUR exact Silver Layer math
            try:
                silver = compute_silver_metrics(bronze)
            except Exception as e:
                continue
                
            # 3. Evaluate against YOUR exact Hard Gates
            try:
                gold = evaluate_hard_gates(silver, "none", 100000.0)
            except Exception:
                continue
                
            # Only proceed if the trade survives your production gates
            if gold.verdict in ["STRONG BUY", "BUY ON DIP"]:
                
                # 4. The Oracle: What happened in reality 15 days later?
                future_slice = df.iloc[i+1 : i+1+LOOKAHEAD_DAYS]
                current_price = getattr(silver, "current_price")
                max_high = float(future_slice['High'].max())
                min_low = float(future_slice['Low'].min())
                
                # Grade Intent (+5% target, -5% stop)
                outcome = "DRAW"
                if max_high >= current_price * 1.05: outcome = "WIN"
                elif min_low <= current_price * 0.95: outcome = "LOSS"
                
                if outcome in ["WIN", "LOSS"]:
                    batch_payloads.append({
                        "ticker": ticker,
                        "timeframe": "swing",
                        "date": simulated_date,
                        "pipeline_version": "v1.0.0",
                        "silver_state": silver.model_dump() if hasattr(silver, 'model_dump') else silver.__dict__,
                        "gold_verdict": gold.model_dump() if hasattr(gold, 'model_dump') else gold.__dict__,
                        "actual_outcome": outcome,
                        "max_favorable_excursion": max_high,
                        "max_adverse_excursion": min_low
                    })

    if batch_payloads:
        supabase.table("algorithmic_ledger").upsert(batch_payloads).execute()
        print(f"✅ Injected {len(batch_payloads)} fully graded production logs based purely on your existing code.")
    else:
        print("⚠️ No trades passed your gates.")

if __name__ == "__main__":
    start = time.time()
    run_simulation()
    print(f"⏱️ Done in {round(time.time() - start, 2)}s")