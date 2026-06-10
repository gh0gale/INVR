import asyncio
import json
import os
import sys
from app.services.bronze_service import build_bronze_payload

# Reconfigure stdout to support emojis on Windows terminals
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

async def test_pipeline():
    ticker = "IDEA"
    timeframes = ["intraday", "positional"]

    
    print("=" * 60)
    print(f"🚀 STARTING BRONZE LAYER VERIFICATION FOR: {ticker}")
    print("=" * 60)
    
    for tf in timeframes:
        print(f"\n[🔄] Triggering Pipeline Router & Fetcher for Timeframe: '{tf.upper()}'")
        try:
            # 1. Execute the orchestrator service
            payload = await build_bronze_payload(ticker=ticker, timeframe=tf)
            
            # 2. Print high-level structural verification
            print(f"  [✅] Payload successfully assembled in memory!")
            print(f"  [•] Ticker: {payload.ticker}")
            print(f"  [•] Timeframe: {payload.timeframe}")
            print(f"  [•] Circuit Status: {payload.circuit_status}")
            
            if payload.price_history is not None:
                print(f"  [•] Price History Shapes: {payload.price_history.shape} (Rows, Columns)")
                print(f"      Latest Close Price: INR {payload.price_history['Close'].iloc[-1]:.2f}")
            else:
                print(f"  [❌] Price History is missing!")
                
            print(f"  [•] Fundamentals Extracted: {payload.fundamentals}")
            
            if payload.sector_history is not None:
                print(f"  [•] Sector Index History Shape: {payload.sector_history.shape}")
            else:
                print(f"  [•] Sector Index History: None (Skipped per manifest or missing mapping)")
                
        except Exception as e:
            print(f"  [💥] Error executing {tf}: {str(e)}")
            
    # 3. Verify physical file creation on disk
    print("\n" + "=" * 60)
    print("📁 INSPECTING LOCAL JSON CACHE STORAGE")
    print("=" * 60)
    cache_dir = os.path.join(os.getcwd(), ".local_cache")
    if os.path.exists(cache_dir):
        files = os.listdir(cache_dir)
        print(f"Found {len(files)} file(s) in .local_cache/:")
        for f in files:
            size_kb = os.path.getsize(os.path.join(cache_dir, f)) / 1024
            print(f"  - {f} ({size_kb:.2f} KB)")
    else:
        print("  [❌] .local_cache directory does not exist on disk!")

if __name__ == "__main__":
    import time
    start_time = time.time()
    # Run the async test suite
    asyncio.run(test_pipeline())
    end_time = time.time()
    print("\n" + "=" * 60)
    print(f"⏱️ TOTAL TIME ELAPSED: {end_time - start_time:.2f} seconds")
    print("=" * 60)