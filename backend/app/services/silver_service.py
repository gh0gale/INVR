import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from app.schemas.bronze import BronzePayload
from app.schemas.silver import SilverMetrics
from config.gate_thresholds import GATE_THRESHOLDS as TH

def _normalize_roe_pct(raw) -> Optional[float]:
    """Return on equity as a percentage, whichever unit the source used.

    yfinance reports `returnOnEquity` as a fraction (0.1845 = 18.45%), but some
    fallback keys and cached rows carry it already in percent. `roe_min` in
    gate_thresholds.py is expressed in percent, so everything is normalised to
    that before any comparison.

    The ambiguity is resolved by magnitude: a fraction above 1.0 would be a
    100%+ return on equity, which is rare enough that treating values <= 1.0 as
    fractions is the safer reading. Returns None for missing data rather than
    0.0, so "no data" is never scored as "bad ROE".
    """
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:  # NaN
        return None
    return value * 100.0 if -1.0 <= value <= 1.0 else value


def _normalize_debt_to_equity(raw) -> Optional[float]:
    """Debt/equity as a multiple, whichever unit the source used.

    yfinance reports this as a percentage (150.0 = 1.5x equity), while
    `debt_equity_max` is a multiple (1.5). Values above 10 are read as
    percentages; a genuine 10x-equity debt load is far rarer than the
    percentage encoding. Returns None for missing data.
    """
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value or value < 0:
        return None
    return value / 100.0 if value > 10 else value


def calculate_cagr(history_list: list) -> Optional[float]:
    """Helper method to mathematically calculate CAGR from list profiles safely."""
    if not history_list or len(history_list) < 2 or history_list[0] <= 0:
        return None
    start_val = history_list[0]
    end_val = history_list[-1]
    periods = len(history_list) - 1
    if end_val <= 0:
        return None
    try:
        return float((end_val / start_val) ** (1 / periods) - 1)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None

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


    # MACRO REGIME & RELATIVE STRENGTH (Top-Down Filter)
    
    if tf in ["swing", "positional", "long_term"] and bronze.sector_history is not None:
        sdf = bronze.sector_history
        lookback = 20 if tf == "swing" else (50 if tf == "positional" else 12)
        
        # 1. Sector/Index Relative Strength
        if len(df) >= lookback and len(sdf) >= lookback:
            stock_ret = (current_price - df['Close'].iloc[-lookback]) / df['Close'].iloc[-lookback]
            sector_ret = (sdf['Close'].iloc[-1] - sdf['Close'].iloc[-lookback]) / sdf['Close'].iloc[-lookback]
            m["stock_vs_sector_rs"] = float(stock_ret - sector_ret)
            
        # 2. Market Regime Evaluation (Is the broader index crashing?)
        if len(sdf) >= 200:
            index_close = float(sdf['Close'].iloc[-1])
            index_sma_50 = float(sdf['Close'].rolling(50).mean().iloc[-1])
            index_sma_200 = float(sdf['Close'].rolling(200).mean().iloc[-1])
            
            if index_close < index_sma_50 and index_close < index_sma_200:
                m["market_regime"] = "bearish"
            elif index_close > index_sma_50 and index_close > index_sma_200:
                m["market_regime"] = "bullish"
            else:
                m["market_regime"] = "neutral"

    # =========================================================================
    # 2. HORIZON SPECIFIC FUNDAMENTALS EXTRACTION & ANALYSIS
    # =========================================================================
    f = bronze.fundamentals or {}
    inst = bronze.institutional_activity or {}

    if tf == "swing":
        # Relative valuation is only computed when a real sector median exists.
        # It used to fall back to a hardcoded 25.0, which produced a confident
        # number out of no data (audit FIX-03). None is the honest answer, and
        # matches how institutional_bias and the P1-01 stub already behave.
        pe = f.get("trailingPE", f.get("pe_ratio", 0.0))
        sector_pe = f.get("sector_pe_median")
        if pe > 0 and sector_pe:
            m["pe_vs_sector_avg"] = float(pe - float(sector_pe))
        else:
            m["pe_vs_sector_avg"] = None

        de = _normalize_debt_to_equity(f.get("debtToEquity", f.get("debt_to_equity")))
        m["debt_to_equity"] = de
        m["debt_flag"] = bool(de > TH["debt_equity_max"]) if de is not None else None

        # Institutional bias needs institutional data. The source is not wired
        # up (P1-01), and an empty dict used to arrive here as fii=0, dii=0 and
        # leave as a confident "neutral" - a reading manufactured from nothing.
        fii_net = inst.get("fii_net_activity")
        dii_net = inst.get("dii_net_activity")
        if fii_net is None and dii_net is None:
            m["institutional_bias"] = None
        else:
            net = (fii_net or 0.0) + (dii_net or 0.0)
            m["institutional_bias"] = "buyer" if net > 50 else ("seller" if net < -50 else "neutral")

    elif tf == "positional":
        # Fallback Chain: Try 3Y CAGR list -> Fallback to standard YoY Revenue Growth
        rev_3y = calculate_cagr(f.get("revenue_3y", []))
        m["revenue_cagr_3y"] = (rev_3y * 100) if rev_3y is not None else float(f.get("revenueGrowth", 0.0) * 100)
        
        profit_3y = calculate_cagr(f.get("net_profit_3y", []))
        m["profit_cagr_3y"] = (profit_3y * 100) if profit_3y is not None else float(f.get("earningsGrowth", 0.0) * 100)
        
        opm = f.get("opm_trend", [])
        if len(opm) >= 2:
            is_monotonic = all(opm[i] <= opm[i+1] for i in range(len(opm)-1))
            is_v_shape = len(opm) >= 3 and opm[0] > opm[1] and opm[-1] > opm[0]
            m["opm_trend"] = "expanding" if (is_monotonic or is_v_shape) else ("contracting" if opm[-1] < opm[0] else "stable")
        else:
            m["opm_trend"] = "stable"
            
        # Capital Return Metrics.
        # yfinance returns returnOnEquity as a fraction (0.18 = 18%) while
        # `roe_min` is expressed in percent (15.0). Comparing them directly made
        # the test `0.18 > 15.0` and this flag was therefore False for every
        # stock ever analysed (audit FIX-02). Normalised to percent first.
        roe = _normalize_roe_pct(f.get("returnOnEquity", f.get("roe")))
        m["roe_pct"] = roe
        m["roe_vs_cost_of_capital"] = bool(roe > TH["roe_min"]) if roe is not None else None

        pe = float(f.get("trailingPE", f.get("pe", 0.0)))
        m["trailing_pe"] = pe
        sector_pe = f.get("sector_pe_median")
        if pe and sector_pe:
            m["valuation_comfort"] = float((pe - float(sector_pe)) / float(sector_pe) * 100)
        else:
            m["valuation_comfort"] = None

    elif tf == "long_term":
        inc = f.get("income_statement_5y", {})
        bal = f.get("balance_sheet_5y", {})
        ratios = f.get("ratios", {})
        cf_5y = f.get("cashflow_5y", {})

        # Fallback Chain: Try 5Y CAGR list -> Fallback to YoY Growth
        rev_5y = calculate_cagr(inc.get("revenue", []))
        m["revenue_cagr_5y"] = (rev_5y * 100) if rev_5y is not None else float(f.get("revenueGrowth", 0.0) * 100)
        
        eps_5y = calculate_cagr(inc.get("eps", []))
        m["eps_cagr_5y"] = (eps_5y * 100) if eps_5y is not None else float(f.get("earningsGrowth", 0.0) * 100)

        # FCF Conversion Calculation
        cfo_list = cf_5y.get("cfo", [])
        capex_list = cf_5y.get("capex", [])
        net_profit_list = inc.get("net_profit", [])
        if cfo_list and capex_list and net_profit_list:
            min_len = min(len(cfo_list), len(capex_list), len(net_profit_list))
            if min_len > 0:
                total_fcf = sum(cfo_list[i] - capex_list[i] for i in range(min_len))
                total_np = sum(net_profit_list[:min_len])
                if total_np > 0:
                    m["fcf_conversion"] = float(total_fcf / total_np)
            
            
        # ROE Trend Resilience Analysis
        roe_5y = ratios.get("roe_5y", [])
        roe_val = _normalize_roe_pct(f.get("returnOnEquity"))
        
        if roe_5y:
            m["roe_consistency_5y"] = "consistent_moat" if min(roe_5y) > 18.0 else "average"
        elif (roe_val or 0.0) > 18.0:
            m["roe_consistency_5y"] = "consistent_moat"
        else:
            m["roe_consistency_5y"] = "volatile"

        # Structural Credit Health Directory Tracking
        debt_5y = bal.get("total_debt", [])
        if len(debt_5y) >= 2:
            m["debt_trajectory"] = "deleveraging" if debt_5y[-1] < debt_5y[0] else "leveraging"
        else:
            m["debt_trajectory"] = "stable"
            
        pe = float(f.get("trailingPE", ratios.get("pe", 0.0)))
        m["trailing_pe"] = pe
        growth = m.get("eps_cagr_5y", 0.0)
        m["pe_band_vs_growth"] = float(pe / growth) if (pe > 0 and growth > 0) else pe

    return SilverMetrics(**m)