import os
os.environ["SYNDICATE_WARNINGS"] = "0"
os.environ["PYDANTIC_WARNINGS"] = "0"

import time
import asyncio
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore")

# Import your pipeline services
from app.schemas.bronze import BronzePayload
from app.services.silver_service import compute_silver_metrics
from app.services.gold_service import evaluate_hard_gates

# Import LangChain for the LLM Layer (Optional execution based on flag)
from langchain_core.prompts import ChatPromptTemplate
# Adjust this import to whatever local LLM you are using (e.g., ChatOllama, ChatLlamaCpp)
from langchain_ollama import ChatOllama 

TICKERS = [
    "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "LT.NS", "MARUTI.NS",
    "TRENT.NS", "DIXON.NS", "CUMMINSIND.NS", "LUPIN.NS", "OBEROIRLTY.NS",
    "BSE.NS", "KPITTECH.NS", "RADICO.NS", "NEOGEN.NS", "ZENTEC.NS"
]

# Toggle this to True if you want to run the local LLM 45 times (Warning: Takes a long time!)
RUN_LLM_LAYER = True

def build_historical_bronze(ticker: str, timeframe: str, days_ago: int) -> BronzePayload:
    """Fetches historical price AND attempts to fetch basic fundamentals."""
    end_date = datetime.now() - timedelta(days=days_ago)
    start_date = end_date - timedelta(days=1000) 
    
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    
    # --- ADDED: Fetch the Nifty 50 Benchmark for the exact same dates ---
    index_ticker = yf.Ticker("^NSEI")
    index_df = index_ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    
    if df.empty:
        raise Exception("No price data available.")
        
    # Attempt to fetch basic fundamental context so the AI isn't blind
    fundamentals = {}
    try:
        info = stock.info
        fundamentals = {
            "trailingPE": info.get("trailingPE", 0),
            "revenueGrowth": info.get("revenueGrowth", 0),
            "earningsGrowth": info.get("earningsGrowth", 0),
            "debtToEquity": info.get("debtToEquity", 0),
            "returnOnEquity": info.get("returnOnEquity", 0)
        }
    except Exception:
        pass 
        
    return BronzePayload(
        ticker=ticker,
        timeframe=timeframe,
        price_history=df, 
        sector_history=index_df if not index_df.empty else None, # <-- ADDED: Feed the index data
        fundamentals=fundamentals,  
        circuit_status="none"
    )

def check_actual_future_price(ticker: str, days_ago: int) -> float:
    start_date = datetime.now() - timedelta(days=days_ago)
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date.strftime('%Y-%m-%d'))
    
    if df.empty or len(df) < 2: return 0.0
        
    entry_price = float(df['Close'].iloc[0])
    today_price = float(df['Close'].iloc[-1])
    return ((today_price - entry_price) / entry_price) * 100

def grade_verdict(verdict: str, return_pct: float) -> tuple[float, str]:
    """
    Advanced Scoring Logic:
    1.0 = Full Win
    0.5 = Partial Win (Stock chopped sideways, buffered accurately)
    0.0 = Loss
    """
    BUFFER = 3.0 # +/- 3% is considered "flat" or "choppy"
    
    if verdict == "STRONG BUY":
        if return_pct > 0: return 1.0, "✅ Correct (Profit)"
        else: return 0.0, "❌ Wrong (Loss)"
        
    elif verdict in ["BUY ON DIP", "MONITOR"]:
        # If the stock barely moved (inside the buffer), the neutral call was 50% correct
        if -BUFFER <= return_pct <= BUFFER:
            return 0.5, "⚖️ Buffer Hit (Choppy/Flat)"
            
        elif return_pct > BUFFER:
            if verdict == "BUY ON DIP": return 1.0, "✅ Correct (Profit)"
            else: return 0.0, "❌ Wrong (Missed Run)" # MONITOR missed the big run
            
        else: # return_pct < -BUFFER
            if verdict == "BUY ON DIP": return 0.0, "❌ Wrong (Loss)"
            else: return 1.0, "✅ Correct (Saved Money)" # MONITOR saved from the big crash
            
    elif verdict in ["CAUTION", "WAIT", "AVOID"]:
        if return_pct <= 0: return 1.0, "✅ Correct (Saved Money)"
        else: return 0.0, "❌ Wrong (Missed Run)"
        
    return 0.0, "❌ Unknown State"

def simulate_llm_layer(gold):
    """Simulates passing the gold payload to your local LangChain model."""
    if not RUN_LLM_LAYER:
        return "LLM Layer Skipped (Toggle RUN_LLM_LAYER=True to enable)"
        
    try:
        # Initialize your local model (Adjust model name if using Llama-3)
        llm = ChatOllama(model="llama3.1", temperature=0)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI financial analyst. Summarize this quant verdict in 1 sentence."),
            ("human", "Ticker: {ticker}\nVerdict: {verdict}\nReason: {reason}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({
            "ticker": gold.ticker, 
            "verdict": gold.verdict, 
            "reason": gold.primary_reason
        })
        return response.content
    except Exception as e:
        return f"LLM Error: {str(e)}"

async def run_full_pipeline():
    print("=" * 80)
    print("🤖 INITIATING FULL-STACK PIPELINE BACKTEST")
    print("=" * 80)
    
    configs = [
        {"type": "swing", "days_ago": 30},       
        {"type": "positional", "days_ago": 180},
        {"type": "long_term", "days_ago": 365}
    ]
    
    for config in configs:
        tf = config['type']
        days = config['days_ago']
        
        print(f"\n" + "═" * 80)
        print(f"📊 TIMEFRAME: {tf.upper()} (Testing signals from {days} days ago)")
        print("═" * 80)
        
        total_score = 0.0
        total_tested = 0
        
        for ticker in TICKERS:
            try:
                time.sleep(1.0) # Anti-bot delay
                
                # --- STAGE 1: BRONZE (Data Fetch) ---
                bronze = build_historical_bronze(ticker, tf, days)
                
                # --- STAGE 2: SILVER (Compute Metrics) ---
                silver = compute_silver_metrics(bronze)
                
                # --- STAGE 3: GOLD (Evaluate Gates) ---
                gold = evaluate_hard_gates(silver, bronze.circuit_status, available_capital=100000.0)
                
                # --- STAGE 4: LLM (Synthesize) ---
                llm_report = simulate_llm_layer(gold)
                
                # --- STAGE 5: GRADE REALITY ---
                actual_return = check_actual_future_price(ticker, days)
                score, reason = grade_verdict(gold.verdict, actual_return)
                
                total_score += score
                total_tested += 1
                
                # Output formatting
                ticker_display = f"[{ticker:<13}]"
                ai_display = f"AI: {gold.verdict:<12}"
                reality_display = f"Reality: {actual_return:>6.2f}%"
                
                print(f"{ticker_display} {ai_display} | {reality_display} | {reason}")
                
                if RUN_LLM_LAYER:
                    print(f"   └─ LLM: {llm_report}")
                
            except Exception as e:
                print(f"[{ticker:<13}] Skipped due to error: {e}")
                
        # Calculate accurate Win Rate accounting for 0.5 partial points
        win_rate = (total_score / total_tested) * 100 if total_tested > 0 else 0
        
        print("\n" + "-" * 40)
        print(f"📈 {tf.upper()} FINAL RESULTS:")
        print(f"Total Tested : {total_tested}")
        print(f"Total Score  : {total_score}/{total_tested} (Includes 0.5 Buffers)")
        print(f"🏆 WIN RATE  : {win_rate:.1f}%")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(run_full_pipeline())