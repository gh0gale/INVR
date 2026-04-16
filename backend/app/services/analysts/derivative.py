def calculate_score(data: dict) -> dict:
    """
    Derivative Analyst
    Calculates Put-Call Ratio (PCR), IV approximation, Option Max Pain.
    Returns a score 0-100. (Gracefully returns 50 if no F&O).
    """
    if not data.get("has_options", False):
        return {
            "score": 50,
            "summary": "Stock is not in F&O list or options data unavailable."
        }

    score = 50
    details = []

    def g(key, default=None):
        val = data.get(key)
        return float(val) if val is not None else default

    pcr = g("put_call_ratio")
    max_pain = g("max_pain")
    price = g("current_price")
    iv = g("avg_implied_volatility")

    if pcr is not None:
        if pcr > 1.2:
            score += 15
            details.append(f"High PCR ({pcr:.2f}) indicates extreme retail fear (contrarian bullish).")
        elif pcr < 0.6:
            score -= 10
            details.append(f"Low PCR ({pcr:.2f}) indicates high greed (contrarian bearish).")

    if max_pain is not None and price is not None and max_pain > 0:
        proximity_pct = abs(price - max_pain) / price
        if proximity_pct > 0.05:
            if price > max_pain:
                score -= 10
                details.append(f"Price is >5% above max pain point (₹{max_pain:.1f}), gravitation risk downwards.")
            else:
                score += 10
                details.append(f"Price is >5% below max pain point (₹{max_pain:.1f}), gravitation potential upwards.")

    if iv is not None:
        if iv > 0.5:
            score -= 5
            details.append("High option premiums (uncertainty/event risk).")

    score = max(0, min(100, score))
    summary = " ".join(details) if details else "Derivative metrics are neutral."

    return {
        "score": int(score),
        "summary": summary
    }
