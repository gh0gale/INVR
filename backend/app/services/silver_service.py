import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from app.schemas.bronze import BronzePayload
from app.schemas.silver import SilverMetrics

def calculate_cagr(history_list: list) -> Optional[float]:
    """Helper method to mathematically calculate CAGR from list profiles safely."""
    if not history_list or len(history_list) < 2 or history_list[0] <= 0:
        return None
    start_val = history_list[0]
    end_val = history_list[-1]
    periods = len(history_list) - 1
    if end_val <= 0:
        return None
    return float((end_val / start_val) ** (1 / periods) - 1)

def compute_silver_metrics(bronze: BronzePayload) -> SilverMetrics:
    df = bronze.price_history.copy()
    if df.empty:
        raise ValueError(f"Price series empty for {bronze.ticker}")

    latest_row = df.iloc[-1]
    current_price = float(latest_row['Close'])
    current_volume = float(latest_row['Volume'])
    tf = bronze.timeframe.lower()

    # Initialize return parameters dictionary
    m: Dict[str, Any] = {
        "ticker": bronze.ticker,
        "timeframe": tf,
        "current_price": current_price,
        "current_volume": current_volume
    }

    # =========================================================================
    # 1. TECHNICAL TRANSFORMATION CORE BLOCK (Vectorized Pandas Operations)
    # =========================================================================
    # Moving Averages (Calculated only if data sequence length criteria met)
    if len(df) >= 20:
        m["sma_20"] = float(df['Close'].rolling(20).mean().iloc[-1])
        m["volume_avg_20"] = float(df['Volume'].rolling(20).mean().iloc[-1])
    if len(df) >= 50:
        m["sma_50"] = float(df['Close'].rolling(50).mean().iloc[-1])
    if len(df) >= 200 and tf in ["positional", "long_term"]:
        m["sma_200"] = float(df['Close'].rolling(200).mean().iloc[-1])
        if m["sma_50"] and m["sma_200"]:
            m["sma_gap_pct"] = float((m["sma_50"] - m["sma_200"]) / m["sma_200"] * 100)

    # Wilder's Relative Strength Index (RSI 14)
    if len(df) >= 15:
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
        loss = -delta.clip(upper=0).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / (loss + 1e-9)
        m["rsi_14"] = float((100 - (100 / (1 + rs))).iloc[-1])

    # Average True Range (ATR 14)
    if len(df) >= 15:
        hl = df['High'] - df['Low']
        hc = (df['High'] - df['Close'].shift(1)).abs()
        lc = (df['Low'] - df['Close'].shift(1)).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        m["atr_14"] = float(tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1])

    # Sector Relative Strength Matrix Evaluation
    if tf in ["swing", "positional", "long_term"] and bronze.sector_history is not None:
        sdf = bronze.sector_history
        lookback = 20 if tf == "swing" else (50 if tf == "positional" else 12) # ~20 periods baseline
        if len(df) >= lookback and len(sdf) >= lookback:
            stock_ret = (current_price - df['Close'].iloc[-lookback]) / df['Close'].iloc[-lookback]
            sector_ret = (sdf['Close'].iloc[-1] - sdf['Close'].iloc[-lookback]) / sdf['Close'].iloc[-lookback]
            m["stock_vs_sector_rs"] = float(stock_ret - sector_ret)

    # =========================================================================
    # 2. HORIZON SPECIFIC FUNDAMENTALS EXTRACTION & ANALYSIS
    # =========================================================================
    f = bronze.fundamentals or {}
    inst = bronze.institutional_activity or {}

    if tf == "swing":
        # Valuation & Debt Flags
        if "pe_ratio" in f:
            m["pe_vs_sector_avg"] = float(f["pe_ratio"] - f.get("sector_pe_median", 25.0))
        if "debt_to_equity" in f:
            m["debt_flag"] = bool(f["debt_to_equity"] > 1.5)
        
        # Institutional Bias Processing Engine
        fii_net = inst.get("fii_net_activity", 0.0)
        dii_net = inst.get("dii_net_activity", 0.0)
        if fii_net + dii_net > 50: # Net buying over 50 Cr
            m["institutional_bias"] = "buyer"
        elif fii_net + dii_net < -50:
            m["institutional_bias"] = "seller"
        else:
            m["institutional_bias"] = "neutral"

    elif tf == "positional":
        # Multi-Year Aggregations
        m["revenue_cagr_3y"] = calculate_cagr(f.get("revenue_3y", []))
        m["profit_cagr_3y"] = calculate_cagr(f.get("net_profit_3y", []))
        
        # Operating Margin Trend Analysis
        opm = f.get("opm_trend", [])
        if len(opm) >= 2:
            m["opm_trend"] = "expanding" if opm[-1] > opm[0] else "contracting"
        else:
            m["opm_trend"] = "stable"
            
        # Capital Return Metrics
        m["roe_vs_cost_of_capital"] = bool(f.get("roe", 0) > 15.0)
        
        # Cash Flow Verification
        cfo_list = f.get("cfo_3y", [])
        profit_list = f.get("net_profit_3y", [])
        if cfo_list and profit_list and sum(profit_list) > 0:
            m["cfo_vs_net_profit"] = float(sum(cfo_list) / sum(profit_list))
            
        # Corporate Controller Track
        promoters = f.get("promoter_holding_trend", [])
        if len(promoters) >= 2:
            m["promoter_holding_trend"] = "accumulating" if promoters[-1] > promoters[0] else "decreasing"
        
        m["valuation_comfort"] = float(f.get("pe", 0.0))

    elif tf == "long_term":
        # Deep Business Moat Audit Parsing Block
        inc = f.get("income_statement_5y", {})
        bal = f.get("balance_sheet_5y", {})
        cf = f.get("cashflow_5y", {})
        ratios = f.get("ratios", {})
        holdings = f.get("holding_pattern_8q", {})

        m["revenue_cagr_5y"] = calculate_cagr(inc.get("revenue", []))
        m["eps_cagr_5y"] = calculate_cagr(inc.get("eps", []))
        
        # Free Cash Flow Performance Calculation
        cfo_5y = cf.get("cfo", [])
        capex_5y = cf.get("capex", [])
        net_profit_5y = inc.get("net_profit", [])
        if cfo_5y and capex_5y and net_profit_5y and sum(net_profit_5y) > 0:
            fcf_total = sum(cfo_5y) - sum(capex_5y)
            m["fcf_conversion"] = float(fcf_total / sum(net_profit_5y))
            
        # ROE Trend Resilience Analysis
        roe_5y = ratios.get("roe_5y", [])
        if roe_5y:
            m["roe_consistency_5y"] = "consistent_moat" if min(roe_5y) > 18.0 else "average"
        else:
            m["roe_consistency_5y"] = "volatile"

        # Structural Credit Health Directory Tracking
        debt_5y = bal.get("total_debt", [])
        if len(debt_5y) >= 2:
            m["debt_trajectory"] = "deleveraging" if debt_5y[-1] < debt_5y[0] else "leveraging"
            
        m["book_value_growth"] = calculate_cagr(bal.get("book_value_per_share", []))
        
        # Shareholder Base Dynamics
        p_hold = holdings.get("promoter", [])
        if p_hold:
            m["promoter_conviction_trend"] = float(p_hold[-1] - p_hold[0])
            
        m["pe_band_vs_growth"] = float(ratios.get("pe", 0.0))
        m["dividend_consistency"] = bool(ratios.get("dividend_yield", 0.0) > 0.0)

    return SilverMetrics(**m)