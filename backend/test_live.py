import asyncio
import traceback
from app.services.bronze_service import build_bronze_payload
from app.services.silver_service import compute_silver_metrics
from app.services.gold_service import evaluate_hard_gates

async def test_live_network():
    ticker = "ETERNAL"
    timeframes = ["intraday", "swing", "positional", "long_term"]
    
    print("=" * 80)
    print(f"🥇 EXECUTING FULL MEDALLION PIPELINE FOR TICKER: {ticker.upper()}")
    print("=" * 80)

    for tf in timeframes:
        print("\n" + "═" * 80)
        print(f"📊 TIMEFRAME: {tf.upper()}")
        print("═" * 80)
        try:
            # 1. Bronze
            bronze = await build_bronze_payload(ticker, tf)
            # 2. Silver
            silver = compute_silver_metrics(bronze)
            # 3. Gold 
            gold = evaluate_hard_gates(silver=silver, circuit_status=bronze.circuit_status, available_capital=100000)
            
            print(f"🎯 VERDICT: {gold.verdict} ({gold.confidence_score}% Confidence)")
            print(f"📝 Reason:  {gold.primary_reason}")
            
            print("\n🛡️  GATE SCORECARD:")
            for gate_name, result in gold.gate_results.items():
                icon = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️"
                print(f"  {icon} {gate_name.upper():<15}: {result}")
            
            if gold.what_to_watch:
                print("\n👀 WHAT TO WATCH:")
                for item in gold.what_to_watch:
                    print(f"  -> {item}")

            if gold.trade_setup:
                print("\n💰 ARITHMETIC TRADE SETUP:")
                print(f"  - Entry Zone:  ₹{gold.trade_setup.entry_zone_low} to ₹{gold.trade_setup.entry_zone_high}")
                print(f"  - Target 1:    ₹{gold.trade_setup.target_1} (R:R {gold.trade_setup.risk_reward_ratio}x)")
                print(f"  - Stop Loss:   ₹{gold.trade_setup.stop_loss}")
                print(f"  - Sizing:      {gold.trade_setup.suggested_position_size} shares (Risking ₹{gold.trade_setup.risk_per_trade_inr})")
                
        except Exception as e:
            print(f"\n[💥] Pipeline Failed for {tf.upper()}: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_network())