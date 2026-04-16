import math

def calculate_score(data: dict) -> dict:
    """
    Valuation Analyst
    Calculates Forward P/E vs historical, EV/EBITDA, P/B, PEG, DCF Margin of Safety, Dividend Yield.
    Returns a score 0-100.
    """
    score = 50
    details = []

    def g(key, default=None):
        val = data.get(key)
        return float(val) if val is not None else default

    pe = g("current_pe")
    f_pe = g("forward_pe")
    peg = g("peg_ratio")
    pb = g("price_to_book")
    eveb = g("ev_to_ebitda")
    div_yield = g("dividend_yield")
    eps = g("trailing_eps")
    price = g("current_price")
    
    # Benchmarks from DB (fallbacks provided)
    median_pe = g("sector_median_pe", 20.0)
    median_pb = g("sector_median_pb", 3.0)

    # 1. P/E & Forward P/E (Sector Aware)
    if pe is not None:
        if pe < median_pe * 0.8:
            score += 15
            details.append(f"Currently trading at P/E ({pe:.1f}) below sector median ({median_pe:.1f}).")
        elif pe > median_pe * 1.5:
            score -= 15
            details.append(f"Trading at a significant premium to sector median P/E.")
        
        if f_pe is not None and f_pe < pe:
            score += 5
            details.append("Forward earnings growth improvement expected.")

    # 2. PEG Ratio
    if peg is not None:
        if peg < 1.0 and peg > 0:
            score += 15
            details.append(f"Attractive PEG ratio ({peg:.2f}).")
        elif peg > 2.0:
            score -= 10

    # 3. Price to Book (Sector Aware)
    if pb is not None:
        if pb < median_pb:
            score += 10
            details.append(f"P/B ratio ({pb:.1f}) is below sector median ({median_pb:.1f}).")
        elif pb > median_pb * 2:
            score -= 5

    # 4. EV / EBITDA
    if eveb is not None:
        if eveb < 10:
            score += 10
            details.append("Cheap EV/EBITDA multiple.")
        elif eveb > 20:
            score -= 5

    # 5. Dividend Yield
    if div_yield is not None:
        if div_yield > 0.03: # 3% yield
            score += 5
            details.append(f"Strong dividend yield ({div_yield*100:.1f}%).")

    # 6. Basic DCF Margin of Safety (Simplified Graham)
    if eps is not None and price is not None and eps > 0:
        growth_rate = 5.0 
        intrinsic_value = eps * (8.5 + 2 * growth_rate)
        margin_of_safety = (intrinsic_value - price) / intrinsic_value
        if margin_of_safety > 0.20:
            score += 15
            details.append(f"High margin of safety vs intrinsic value ({margin_of_safety*100:.1f}%).")
        elif margin_of_safety < -0.20:
            score -= 15
            details.append("Currently trading above intrinsic valuation.")

    score = max(0, min(100, score))
    summary = " ".join(details) if details else "Valuation metrics are neutral or lack sufficient data."

    return {
        "score": int(score),
        "summary": summary
    }
