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
                if abs(silver.sma_gap_pct) > TH["death_cross_gap_pct"]:
                    gates["death_cross"] = "FAIL"
                    watch_list.append("Confirmed Death Cross. Avoid until 50-day SMA reclaims 200-day SMA.")
                else:
                    gates["death_cross"] = "WARN"
                    watch_list.append("Imminent Death Cross. Monitor SMA 50/200 closely.")
            else:
                gates["death_cross"] = "PASS"
                
        # Revenue Quality
        if silver.revenue_cagr_3y is not None:
            if silver.revenue_cagr_3y < (TH["revenue_cagr_min"] * 100):
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
                gates["secular_trend"] = "PASS"
                
        # Valuation Ceiling
        if silver.trailing_pe is not None:
            if silver.trailing_pe > TH.get("max_pe", 50.0):
                gates["valuation"] = "FAIL"
                watch_list.append(f"Valuation ceiling exceeded. PE ratio ({silver.trailing_pe}) is higher than the {TH['max_pe']} limit.")
            else:
                gates["valuation"] = "PASS"
                
        # FCF and EPS
        if silver.fcf_conversion is not None:
            gates["fcf_quality"] = "PASS" if silver.fcf_conversion > 0.6 else "WARN"
        if silver.eps_cagr_5y is not None:
            if silver.eps_cagr_5y < (TH["eps_cagr_min"] * 100):
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

    # 1. Translate backend keys to readable financial parameters
    GATE_NAMES = {
        "circuit": "Circuit Limits",
        "volume": "Institutional Volume",
        "micro_trend": "Intraday Trend (100-min)",
        "rsi": "Momentum (RSI)",
        "volume_spike": "Intraday Volume Surge",
        "trend": "Short-Term Trend (20 DMA)",
        "sector": "Sector Relative Strength",
        "death_cross": "Moving Average Alignment (50/200 DMA)",
        "revenue_growth": "Revenue Compounding",
        "secular_trend": "Long-Term Trend (200 DMA)",
        "fcf_quality": "Free Cash Flow Conversion",
        "eps_growth": "EPS Compounding",
        "valuation": "Valuation Comfort Ceiling"
    }

    # 2. Extract exactly what failed/warned and what passed
    flagged_issues = [GATE_NAMES.get(k, k) for k, v in gates.items() if v in ["FAIL", "WARN"]]
    strong_metrics = [GATE_NAMES.get(k, k) for k, v in gates.items() if v == "PASS"]

    # 3. Dynamic Parameter-Based Primary Reason
    if "BLOCK" in gates.values():
        verdict = "AVOID"
        reason = "Execution blocked due to Circuit Limits."
    elif failed_count >= 2:
        verdict = "CAUTION"  
        reason = f"Flagged due to weakness in: {', '.join(flagged_issues)}."
    elif failed_count == 1:
        verdict = "MONITOR"  
        reason = f"Held back by lagging {flagged_issues[0]}." if flagged_issues else "A primary technical gate is failing."
    elif passed_count == total_active and total_active > 0:
        verdict = "STRONG BUY"  
        reason = f"Cleared all gates, showing strong {', '.join(strong_metrics[:3])}."
        watch_list.append("Ready for entry within the calculated ATR zone.")
    else:
        verdict = "BUY ON DIP"  
        reason = "Mixed technical signals, but supported by overall structural floors."

    # --- STEP 1: INSTITUTIONAL VOLUME CONFIRMATION OVERRIDE ---
    # Retail moves price, institutions move volume. 
    # Validating breakouts require at least 1.5x the 20-period average volume.
    if verdict == "STRONG BUY" and silver.current_volume and silver.volume_avg_20:
        volume_ratio = silver.current_volume / silver.volume_avg_20
        if volume_ratio < 1.5:
            verdict = "MONITOR"
            reason = f"Price cleared breakout gates, but lacks institutional volume confirmation (Ratio: {volume_ratio:.2f} vs 1.5x required)."
            watch_list.append("Wait for an expansion bar with heavy volume to confirm institutional accumulation.")

    # --- STEP 2: DYNAMIC "BUY ZONE" (DIP SUPPORT) FILTER ---
    # A true dip is a pullback to structural support, not a freefall in mid-air.
    if verdict == "BUY ON DIP":
        price = silver.current_price
        sma_50 = silver.sma_50
        sma_200 = silver.sma_200
        
        is_near_support = False
        allowed_buffer = 0.03  # 3% tolerance window around moving averages
        
        # Check proximity to 50 SMA
        if sma_50:
            if (sma_50 * (1 - allowed_buffer)) <= price <= (sma_50 * (1 + allowed_buffer)):
                is_near_support = True
                
        # Check proximity to 200 SMA
        if sma_200:
            if (sma_200 * (1 - allowed_buffer)) <= price <= (sma_200 * (1 + allowed_buffer)):
                is_near_support = True
                
        # If it's not near support, it's a falling knife or drifting asset
        if not is_near_support:
            verdict = "CAUTION"
            reason = "Asset flagged as a 'BUY ON DIP' candidate but is currently floating outside structural support zones (50/200 DMA)."
            watch_list.append("Wait for price to stabilize and touch a structural moving average floor before allocating risk.")

    # --- STEP 3: TOP DOWN MACRO OVERRIDE (Final Authority) ---
    if silver.market_regime == "bearish" and verdict in ["STRONG BUY", "BUY ON DIP"]:
        verdict = "CAUTION"
        reason = "Market regime is strictly BEARISH. Bullish setups are suppressed to protect capital."
        watch_list.append("Avoid deploying new capital until the broader index reclaims its moving averages.")

    # Weighted Confidence Calculation
    GATE_WEIGHTS = {
        "circuit": 3.0, "death_cross": 3.0, "secular_trend": 2.0,
        "eps_growth": 2.0, "fcf_quality": 2.0, "volume": 1.5,
        "volume_spike": 1.5, "trend": 1.5, "sector": 1.5,
        "micro_trend": 1.0, "rsi": 1.0, "revenue_growth": 1.0,
        "valuation": 2.0
    }
    if not gates:
        confidence_score = 50.0
    else:
        total_weight = sum(GATE_WEIGHTS.get(k, 1.0) for k in gates.keys())
        passed_weight = sum(GATE_WEIGHTS.get(k, 1.0) for k, v in gates.items() if v == "PASS")
        confidence_score = 50.0 + ((passed_weight / total_weight) * 45.0)

    # =========================================================
    # TRADE SETUP (Arithmetic generation - Only if STRONG BUY)
    # =========================================================
    
    trade_setup = None
    # BUG FIX: Updated to check for "STRONG BUY" instead of the old "BUY_SETUP"
    if verdict == "STRONG BUY" and tf in ["intraday", "swing", "positional"] and silver.atr_14:
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