import math

def calculate_score(data: dict) -> dict:
    """
    Fundamental Analyst
    Calculates ROE, ROCE, DuPont, Debt-to-Equity, Current Ratio, Altman Z-Score, FCF Yield.
    Returns a score 0-100.
    """
    score = 50
    details = []

    # Safe get helper
    def g(key, default=0.0):
        val = data.get(key)
        return float(val) if val is not None else default

    roe = g("roe")
    roce = g("roce")
    debt_eq = g("debt_to_equity")
    curr_rat = g("current_ratio")
    fcf = g("free_cash_flow")
    market_cap = g("market_cap")
    
    # 1. Profitability (ROE / ROCE)
    if roe > 0.15:
        score += 10
        details.append("Strong ROE (>15%).")
    elif roe > 0:
        score += 5
    elif roe < 0:
        score -= 10
        details.append("Negative ROE.")
        
    if roce > 0.15:
        score += 10
    
    # 2. Solvency (Debt to Equity)
    if debt_eq > 0:
        # yfinance often gives this as percentage (e.g., 50 for 0.5) so check scale
        d_val = debt_eq if debt_eq < 100 else debt_eq / 100.0
        if d_val > 2.0:
            score -= 15
            details.append("High debt-to-equity risk.")
        elif d_val < 0.5:
            score += 10
            details.append("Low debt leverage.")
            
    # 3. Liquidity (Current Ratio)
    if curr_rat > 1.5:
        score += 5
    elif curr_rat > 0 and curr_rat < 1.0:
        score -= 10
        details.append("Current ratio < 1 (Liquidity risk).")

    # 4. FCF Yield
    if fcf > 0 and market_cap > 0:
        fcf_yield = fcf / market_cap
        if fcf_yield > 0.05:
            score += 10
            details.append(f"Healthy FCF Yield ({fcf_yield*100:.1f}%).")
        elif fcf_yield < 0:
            score -= 10

    # 5. Partial Altman-Z Score (if sufficient data)
    ta = g("total_assets")
    ca = g("current_assets")
    cl = g("current_liabilities")
    re = g("retained_earnings")
    ebit = g("ebit")
    if ta > 0 and ca > 0 and cl > 0 and re != 0 and ebit != 0 and g("total_liabilities") > 0:
        wc = ca - cl
        A = wc / ta
        B = re / ta
        C = ebit / ta
        D = market_cap / g("total_liabilities")
        z_score = 6.56 * A + 3.26 * B + 6.72 * C + 1.05 * D
        if z_score < 1.1:
            score -= 20
            details.append(f"Altman Z-Score {z_score:.2f} indicates distress risk.")
        elif z_score > 2.6:
            score += 10
            details.append(f"Strong Altman Z-Score ({z_score:.2f}).")

    score = max(0, min(100, score))
    summary = " ".join(details) if details else "Fundamental metrics are neutral or lack sufficient data."

    return {
        "score": int(score),
        "summary": summary
    }
