import asyncio
import json
import os
import sys
import pandas as pd

# Add the backend directory to sys.path to ensure absolute imports work
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.bronze_service import build_bronze_payload
from app.services.silver_service import compute_silver_metrics
from app.services.gold_service import evaluate_hard_gates
from config.gate_thresholds import GATE_THRESHOLDS as TH

async def main():
    payload = {
        "ticker": "RELIANCE.NS",
        "timeframe": "swing",
        "user_profile": {
            "risk_tolerance": "moderate",
            "experience_level": "intermediate",
            "goal": "wealth_growth",
            "available_capital": 250000.00
        }
    }
    
    ticker = payload["ticker"]
    timeframe = payload["timeframe"]
    user_profile = payload["user_profile"]
    
    print("=" * 70)
    print(f"1. FETCHING DATA FOR {ticker} (BRONZE LAYER)")
    print("=" * 70)
    
    try:
        bronze = await build_bronze_payload(ticker, timeframe)
        print("Bronze Layer Fetching: SUCCESS")
        print(f"  Ticker: {bronze.ticker}")
        print(f"  Timeframe: {bronze.timeframe}")
        print(f"  Circuit Status: {bronze.circuit_status}")
        print(f"  Price History Data points: {len(bronze.price_history) if bronze.price_history is not None else 0}")
        print(f"  Sector History Data points: {len(bronze.sector_history) if bronze.sector_history is not None else 0}")
        if bronze.fundamentals:
            print("  Fundamentals keys fetched:")
            for k, v in bronze.fundamentals.items():
                val_summary = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
                print(f"    - {k}: {val_summary}")
        else:
            print("  Fundamentals: None")
    except Exception as e:
        print(f"Error fetching bronze payload: {e}")
        return

    print("\n" + "=" * 70)
    print(f"2. COMPUTING METRICS FOR {ticker} (SILVER LAYER)")
    print("=" * 70)
    
    try:
        silver = compute_silver_metrics(bronze)
        print("Silver Layer Computation: SUCCESS")
        print(f"  Current Price: INR {silver.current_price:.2f}")
        print(f"  Current Volume: {silver.current_volume:,.0f}")
        print(f"  SMA 20: {f'INR {silver.sma_20:.2f}' if silver.sma_20 else 'N/A'}")
        print(f"  SMA 50: {f'INR {silver.sma_50:.2f}' if silver.sma_50 else 'N/A'}")
        print(f"  SMA 200: {f'INR {silver.sma_200:.2f}' if silver.sma_200 else 'N/A'}")
        print(f"  RSI (14): {f'{silver.rsi_14:.2f}' if silver.rsi_14 else 'N/A'}")
        print(f"  ATR (14): {f'{silver.atr_14:.2f}' if silver.atr_14 else 'N/A'}")
        print(f"  Volume Avg (20): {f'{silver.volume_avg_20:,.0f}' if silver.volume_avg_20 else 'N/A'}")
        print(f"  Stock vs Sector Relative Strength: {f'{silver.stock_vs_sector_rs:.4f}' if silver.stock_vs_sector_rs is not None else 'N/A'}")
        print(f"  Market Regime: {silver.market_regime}")
        print(f"  Revenue CAGR (5Y): {f'{silver.revenue_cagr_5y*100:.2f}%' if silver.revenue_cagr_5y is not None else 'N/A'}")
        print(f"  EPS CAGR (5Y): {f'{silver.eps_cagr_5y*100:.2f}%' if silver.eps_cagr_5y is not None else 'N/A'}")
        print(f"  FCF Conversion: {f'{silver.fcf_conversion:.2f}' if silver.fcf_conversion is not None else 'N/A'}")
        print(f"  ROE Consistency (5Y): {silver.roe_consistency_5y}")
        print(f"  Debt Trajectory: {silver.debt_trajectory}")
        print(f"  PE Band vs Growth: {silver.pe_band_vs_growth}")
    except Exception as e:
        print(f"Error computing silver metrics: {e}")
        return

    print("\n" + "=" * 70)
    print(f"3. EVALUATING HARD GATES (GOLD LAYER)")
    print("=" * 70)
    
    try:
        gold = evaluate_hard_gates(
            silver=silver,
            circuit_status=bronze.circuit_status,
            available_capital=user_profile["available_capital"]
        )
        print("Gold Layer Gate Evaluation: SUCCESS")
    except Exception as e:
        print(f"Error running gold service: {e}")
        return

    print("\n" + "-" * 70)
    print("CALCULATIONS, METRICS COMPARISONS & GATE DETAILS")
    print("-" * 70)
    
    # Check Universal Gates
    print("[Universal Gates]")
    # Circuit Gate
    print(f"  * Circuit Status check:")
    print(f"    - Input Status: '{bronze.circuit_status}'")
    if bronze.circuit_status == "lower":
        print(f"    - Logic: status == 'lower' -> BLOCK ('Circuit limits must normalize before any entry.')")
    elif bronze.circuit_status == "upper":
        print(f"    - Logic: status == 'upper' -> WARN ('Wait for the stock to exit upper circuit to ensure liquidity.')")
    else:
        print(f"    - Logic: status is normal -> PASS")
    print(f"    - Result: gate_results['circuit'] = '{gold.gate_results.get('circuit')}'")
    
    # Volume Gate
    print(f"  * Volume Validation check:")
    if silver.current_volume and silver.volume_avg_20:
        vol_min = silver.volume_avg_20 * TH["volume_min_ratio"]
        print(f"    - Current Volume: {silver.current_volume:,.0f}")
        print(f"    - 20-Period Avg Volume: {silver.volume_avg_20:,.0f}")
        print(f"    - Threshold Ratio: {TH['volume_min_ratio']}")
        print(f"    - Min Required Volume (Avg * {TH['volume_min_ratio']}): {vol_min:,.0f}")
        print(f"    - Comparison: current_volume ({silver.current_volume:,.0f}) < min_required ({vol_min:,.0f}) ?")
        print(f"    - Result: gate_results['volume'] = '{gold.gate_results.get('volume')}'")
    else:
        print("    - Skipped: Missing current_volume or volume_avg_20 metrics")

    # Check Timeframe long_term Gates
    print("\n[Long-Term Timeframe Specific Gates]")
    # Secular Anchor Gate
    print(f"  * Secular Anchor (200-Week SMA) check:")
    if silver.sma_200:
        print(f"    - Current Price: INR {silver.current_price:.2f}")
        print(f"    - 200-Week SMA: INR {silver.sma_200:.2f}")
        print(f"    - Comparison: current_price ({silver.current_price:.2f}) < 200 SMA ({silver.sma_200:.2f}) ?")
        print(f"    - Result: gate_results['secular_trend'] = '{gold.gate_results.get('secular_trend')}'")
    else:
        print("    - Skipped: Missing 200-week SMA")

    # FCF Quality Gate
    print(f"  * FCF Quality check:")
    if silver.fcf_conversion is not None:
        print(f"    - FCF Conversion: {silver.fcf_conversion:.2f}")
        print(f"    - Comparison: fcf_conversion ({silver.fcf_conversion:.2f}) > 0.6 ?")
        print(f"    - Result: gate_results['fcf_quality'] = '{gold.gate_results.get('fcf_quality')}'")
    else:
        print("    - Skipped: Missing FCF conversion")

    # EPS CAGR Gate
    print(f"  * EPS Growth check:")
    if silver.eps_cagr_5y is not None:
        print(f"    - 5Y EPS CAGR: {silver.eps_cagr_5y*100:.2f}%")
        print(f"    - Threshold CAGR: {TH['eps_cagr_min']*100:.2f}%")
        print(f"    - Comparison: eps_cagr_5y ({silver.eps_cagr_5y:.4f}) < threshold ({TH['eps_cagr_min']:.4f}) ?")
        print(f"    - Result: gate_results['eps_growth'] = '{gold.gate_results.get('eps_growth')}'")
    else:
        print("    - Skipped: Missing 5Y EPS CAGR")

    # Verdict Overrides
    print("\n[Verdict Overrides & Resolutions]")
    passed_count = sum(1 for v in gold.gate_results.values() if v == "PASS")
    failed_count = sum(1 for v in gold.gate_results.values() if v == "FAIL")
    total_active = len(gold.gate_results)
    print(f"  * Gate Counts: Total Active = {total_active}, Passed = {passed_count}, Failed = {failed_count}")
    
    # Macro Regime Override
    print(f"  * Market Regime Override check:")
    print(f"    - Market Regime: {silver.market_regime}")
    if silver.market_regime == "bearish":
        print("    - Comparison: market_regime is 'bearish' -> Suppress any BUY/STRONG BUY to CAUTION")
    else:
        print("    - Comparison: market_regime is not 'bearish' -> No regime override")

    # Dynamic Buy Zone Override (only for BUY ON DIP)
    print(f"  * Dynamic Buy Zone Proximity check:")
    print(f"    - Pre-override Verdict: {gold.verdict} (checks below are run based on verdict logic)")
    
    print("\n" + "=" * 70)
    print("FINAL GOLD VERDICT EVALUATION")
    print("=" * 70)
    print(f"Ticker: {gold.ticker}")
    print(f"Timeframe: {gold.timeframe}")
    print(f"Verdict: {gold.verdict}")
    print(f"Confidence Score: {gold.confidence_score}%")
    print(f"Primary Reason: {gold.primary_reason.replace('₹', 'INR')}")
    print(f"Gate Results: {gold.gate_results}")
    # Clean the Rupee symbol from messages in what_to_watch list
    what_to_watch_clean = [msg.replace('₹', 'INR') for msg in gold.what_to_watch]
    print(f"What to Watch: {what_to_watch_clean}")
    print(f"Trade Setup: {gold.trade_setup}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
