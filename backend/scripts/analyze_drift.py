import os
import sys
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Import YOUR real thresholds
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.gate_thresholds import GATE_THRESHOLDS as TH

load_dotenv(override=True)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

def analyze_system_drift():
    print("📊 INITIALIZING STATISTICAL DRIFT ENGINE...")
    
    logs = supabase.table("algorithmic_ledger").select("timeframe, actual_outcome, silver_state").neq("actual_outcome", "PENDING").neq("actual_outcome", "DRAW").execute().data
        
    if len(logs) < 30:
        print(f"⚠️ Only {len(logs)} graded rows found. Need more data for statistical significance.")
        return
        
    df = pd.DataFrame([{
        "timeframe": log["timeframe"],
        "outcome": log["actual_outcome"],
        "rsi": log["silver_state"].get("rsi_14", 50),
        "vol": log["silver_state"].get("current_volume", 1),
        "avg_vol": max(1, log["silver_state"].get("volume_avg_20", 1))
    } for log in logs])
    
    df["vol_ratio"] = df["vol"] / df["avg_vol"]
    
    wins = df[df["outcome"] == "WIN"]
    losses = df[df["outcome"] == "LOSS"]
    
    print(f" ⚙️ Auditing {len(wins)} Wins vs {len(losses)} Losses against config/gate_thresholds.py...")

    # --- DRIFT CHECK 1: RSI Overbought Ceiling ---
    current_rsi_gate = TH["rsi_overbought"]
    safe_rsi_p90 = float(wins["rsi"].quantile(0.90))
    
    if safe_rsi_p90 < (current_rsi_gate - 3.0): 
        reason = f"Reality Check: 90% of your successful trades happened when RSI was below {safe_rsi_p90:.1f}. Your current configuration allows trades up to {current_rsi_gate}. You are exposing the system to overbought setups."
        log_insight("rsi_overbought", "swing", current_rsi_gate, round(safe_rsi_p90, 1), reason)

    # --- DRIFT CHECK 2: Volume Minimum Ratio ---
    current_vol_gate = TH["volume_min_ratio"]
    avg_win_vol = float(wins["vol_ratio"].median())
    
    # If the median winning trade actually requires 1.2x volume, but our gate is only 0.5x
    if avg_win_vol > (current_vol_gate + 0.4):
        reason = f"Reality Check: The median winning trade has a volume ratio of {avg_win_vol:.2f}x. Your current gate of {current_vol_gate}x is letting extremely low-liquidity/low-conviction trades pass."
        log_insight("volume_min_ratio", "swing", current_vol_gate, round(avg_win_vol - 0.2, 2), reason)

    print("✅ DRIFT ANALYSIS COMPLETE. Admin dashboard updated.")

def log_insight(metric, timeframe, current, suggested, reason):
    """Upserts the suggestion into the threshold_insights table securely."""
    supabase.table("threshold_insights").insert({
        "metric": metric,
        "timeframe": timeframe,
        "current_threshold": current,
        "suggested_threshold": suggested,
        "confidence_score": 90.0,
        "reasoning": reason
    }).execute()
    print(f" 💡 ADMIN INSIGHT FIRED: {metric} should move from {current} -> {suggested}")

if __name__ == "__main__":
    analyze_system_drift()