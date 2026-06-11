from app.schemas.silver import SilverMetrics
from app.schemas.gold import VerdictDraft, TradeSetup
from config.gate_thresholds import GATE_THRESHOLDS as TH

def evaluate_hard_gates(silver: SilverMetrics, circuit_status: str, available_capital: float = 100000.0) -> VerdictDraft:
    gates = {}
    watch_list = []
    tf = silver.timeframe

    # =========================================================
    # UNIVERSAL GATES
    # =========================================================
    if circuit_status == "lower":
        gates["circuit"] = "BLOCK"
        watch_list.append("Circuit limits must normalize before any entry.")
    elif circuit_status == "upper":
        gates["circuit"] = "WARN"
        watch_list.append("Wait for the stock to exit upper circuit to ensure liquidity.")
    else:
        gates["circuit"] = "PASS"

    # Volume Validation
    if silver.current_volume and silver.volume_avg_20:
        if silver.current_volume < (silver.volume_avg_20 * TH["volume_min_ratio"]):
            gates["volume"] = "WARN"
            watch_list.append(f"Wait for volume to cross {int(silver.volume_avg_20 * TH['volume_min_ratio']):,} to confirm institutional participation.")
        else:
            gates["volume"] = "PASS"

    # =========================================================
    # TIMEFRAME SPECIFIC LOGIC
    # =========================================================

    
    if tf == "intraday":
        # Micro-Trend (100-minute average)
        if silver.sma_20:
            if silver.current_price > silver.sma_20:
                gates["micro_trend"] = "PASS"
            else:
                gates["micro_trend"] = "FAIL"
                watch_list.append(f"Wait for price to reclaim the 100-minute SMA (₹{silver.sma_20:.2f}).")
        
        # Micro-Momentum
        if silver.rsi_14:
            if silver.rsi_14 > TH["rsi_overbought"]:
                gates["rsi"] = "FAIL"
                watch_list.append("Micro-momentum is overbought. Wait for an intraday pullback.")
            elif silver.rsi_14 < TH["rsi_oversold"]:
                gates["rsi"] = "WARN"
                watch_list.append("Micro-momentum is oversold. Watch for a bounce.")
            else:
                gates["rsi"] = "PASS"
                
        # Intraday Volume Spike
        if silver.current_volume and silver.volume_avg_20:
            if silver.current_volume < (silver.volume_avg_20 * 1.5):
                gates["volume_spike"] = "WARN"
                watch_list.append("Awaiting a volume spike (>1.5x average) to confirm intraday conviction.")
            else:
                gates["volume_spike"] = "PASS"

    

    elif tf == "swing":
        # Trend
        if silver.sma_20:
            if silver.current_price > silver.sma_20:
                gates["trend"] = "PASS"
            else:
                gates["trend"] = "FAIL"
                watch_list.append(f"Wait for a daily close above the 20-day SMA (₹{silver.sma_20:.2f}).")
        
        # Sector Momentum
        if silver.stock_vs_sector_rs is not None:
            if silver.stock_vs_sector_rs < TH["sector_rs_min"]:
                gates["sector"] = "FAIL"
                watch_list.append("Wait for the stock to stop heavily underperforming its sector index.")
            else:
                gates["sector"] = "PASS"
                
        # RSI 
        if silver.rsi_14:
            if silver.rsi_14 > TH["rsi_overbought"]:
                gates["rsi"] = "FAIL"
                watch_list.append("RSI is overbought. Wait for a pullback to cool momentum.")
            elif silver.rsi_14 < TH["rsi_oversold"]:
                gates["rsi"] = "WARN"
                watch_list.append("RSI is oversold. Wait for a confirmed reversal candle.")
            else:
                gates["rsi"] = "PASS"


    elif tf == "positional":
        # Death Cross Gate
        if silver.sma_50 and silver.sma_200 and silver.sma_gap_pct is not None:
            if silver.sma_50 < silver.sma_200:
                if silver.sma_gap_pct > TH["death_cross_gap_pct"]:
                    gates["death_cross"] = "FAIL"
                    watch_list.append("Confirmed Death Cross. Avoid until 50-day SMA reclaims 200-day SMA.")
                else:
                    gates["death_cross"] = "WARN"
                    watch_list.append("Imminent Death Cross. Monitor SMA 50/200 closely.")
            else:
                gates["death_cross"] = "PASS"
                
        # Revenue Quality
        if silver.revenue_cagr_3y is not None:
            if silver.revenue_cagr_3y < TH["revenue_cagr_min"]:
                gates["revenue_growth"] = "WARN"
                watch_list.append(f"Revenue CAGR is lagging the {TH['revenue_cagr_min']*100}% target.")
            else:
                gates["revenue_growth"] = "PASS"


    elif tf == "long_term":
        # Secular Anchor
        if silver.sma_200:
            if silver.current_price < silver.sma_200:
                gates["secular_trend"] = "WARN"
                watch_list.append(f"Wait for structural recovery above the 200-week SMA (₹{silver.sma_200:.2f}).")
            else:
                gates["secular_trend"] = "PASS"
                
        # FCF and EPS
        if silver.fcf_conversion is not None:
            gates["fcf_quality"] = "PASS" if silver.fcf_conversion > 0.6 else "WARN"
        if silver.eps_cagr_5y is not None:
            if silver.eps_cagr_5y < TH["eps_cagr_min"]:
                gates["eps_growth"] = "FAIL"
                watch_list.append("EPS compounding is too slow for a long-term hold.")
            else:
                gates["eps_growth"] = "PASS"

    # =========================================================
    # VERDICT RESOLUTION
    # =========================================================
    passed_count = sum(1 for v in gates.values() if v == "PASS")
    failed_count = sum(1 for v in gates.values() if v == "FAIL")
    total_active = len(gates)

    if "BLOCK" in gates.values():
        verdict = "AVOID"
        reason = "Execution blocked. Stock is locked in a circuit limit."
    elif failed_count >= 2:
        verdict = "WAIT"
        reason = f"Failed {failed_count} critical structural gates."
    elif failed_count == 1:
        verdict = "CAUTION"
        reason = "A primary technical or fundamental gate is failing."
    elif passed_count == total_active and total_active > 0:
        verdict = "BUY_SETUP"
        reason = "All technical and fundamental gates cleared successfully."
        watch_list.append("Ready for entry within the calculated ATR zone.")
    else:
        verdict = "MONITOR"
        reason = "Mixed signals with no hard failures."

    # Base Confidence Calculation
    confidence_score = 50.0 + ((passed_count / total_active) * 45.0) if total_active > 0 else 50.0

    # =========================================================
    # TRADE SETUP (Arithmetic generation - Only if BUY_SETUP)
    # =========================================================
    
    trade_setup = None
    if verdict == "BUY_SETUP" and tf in ["intraday", "swing", "positional"] and silver.atr_14:
        p = silver.current_price
        atr = silver.atr_14
        
        # Intraday requires tighter risk multipliers than Swing/Positional
        stop_mult = 1.5 if tf == "intraday" else 2.0
        t1_mult = 2.5 if tf == "intraday" else 3.0
        t2_mult = 4.0 if tf == "intraday" else 5.0
        
        entry_low = p - (0.5 * atr)
        entry_high = p + (0.5 * atr)
        stop_loss = p - (stop_mult * atr)
        t1 = p + (t1_mult * atr)
        t2 = p + (t2_mult * atr)
        
        # Risk Sizing: (Capital * 2% risk) / (Entry - Stop Loss)
        risk_per_trade = available_capital * 0.02
        risk_distance = max(p - stop_loss, 0.01) # Avoid div by zero
        position_size = int(risk_per_trade / risk_distance)
        
        rr_ratio = (t1 - p) / risk_distance
        
        trade_setup = TradeSetup(
            entry_zone_low=round(entry_low, 2),
            entry_zone_high=round(entry_high, 2),
            stop_loss=round(stop_loss, 2),
            target_1=round(t1, 2),
            target_2=round(t2, 2),
            suggested_position_size=position_size,
            risk_per_trade_inr=risk_per_trade,
            risk_reward_ratio=round(rr_ratio, 2)
        )

    return VerdictDraft(
        ticker=silver.ticker,
        timeframe=tf,
        verdict=verdict,
        primary_reason=reason,
        confidence_score=round(confidence_score, 1),
        gate_results=gates,
        what_to_watch=watch_list,
        trade_setup=trade_setup
    )