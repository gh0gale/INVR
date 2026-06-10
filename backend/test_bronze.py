import asyncio
import json
import os
from app.services.bronze_service import build_bronze_payload
from app.services.silver_service import compute_silver_metrics # <-- NEW IMPORT

async def test_pipeline():
    ticker = "ASHOKLEY"
    timeframes = ["intraday", "positional"]
    
    print("=" * 60)
    print(f"🚀 STARTING BRONZE & SILVER VERIFICATION FOR: {ticker}")
    print("=" * 60)
    
    for tf in timeframes:
        print(f"\n[🔄] Processing Timeframe: '{tf.upper()}'")
        try:
            # Bronze Phase
            payload = await build_bronze_payload(ticker=ticker, timeframe=tf)
            print(f"  [✅] Bronze Payload built. Price rows: {len(payload.price_history) if payload.price_history is not None else 0}")
            
            # Silver Phase
            if payload.price_history is not None:
                print(f"  [⚙️] Computing Silver Metrics...")
                silver = compute_silver_metrics(payload)
                
                print(f"  [✅] Silver Metrics Computed:")
                print(f"      - Price: INR {silver.current_price:.2f}")
                print(f"      - RSI (14): {silver.rsi_14:.2f}" if silver.rsi_14 else "      - RSI (14): None")
                print(f"      - SMA 50: {silver.sma_50:.2f}" if silver.sma_50 else "      - SMA 50: None (Insufficient Data)")
                print(f"      - SMA 200: {silver.sma_200:.2f}" if silver.sma_200 else "      - SMA 200: None (Insufficient Data)")
                print(f"      - ATR (14): {silver.atr_14:.2f}" if silver.atr_14 else "      - ATR (14): None")
                print(f"      - Sector RS Delta: {silver.stock_vs_sector_rs:.4f}" if silver.stock_vs_sector_rs else "      - Sector RS Delta: None")
                
        except Exception as e:
            print(f"  [💥] Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())