def calculate_score(data: dict) -> dict:
    """
    Technical Analyst
    Calculates RSI, MACD, 50/200 EMA crossovers, ADX proxy (ATR), VWAP, Bollinger Bands.
    Returns a score 0-100.
    """
    score = 50
    details = []

    def g(key, default=None):
        val = data.get(key)
        return float(val) if val is not None else default

    price = g("current_price")
    rsi = g("rsi_14")
    macd_line = g("macd_line")
    macd_signal = g("macd_signal")
    ema_50 = g("ema_50")
    ema_200 = g("ema_200")
    vwap = g("vwap_20d")
    bb_upper = g("bb_upper")
    bb_lower = g("bb_lower")
    
    if rsi is not None:
        if rsi < 30:
            score += 15
            details.append(f"RSI Oversold ({rsi:.1f}).")
        elif rsi > 70:
            score -= 15
            details.append(f"RSI Overbought ({rsi:.1f}).")
        elif 40 <= rsi <= 60:
            score += 5
            details.append("RSI is neutral/bullish.")

    if macd_line is not None and macd_signal is not None:
        if macd_line > macd_signal:
            score += 10
            details.append("MACD is bullish (Line > Signal).")
        else:
            score -= 10
            details.append("MACD is bearish.")

    if price is not None and ema_50 is not None and ema_200 is not None:
        if ema_50 > ema_200:
            score += 10
            details.append("Golden Cross regime (50 EMA > 200 EMA).")
        else:
            score -= 10
            details.append("Death Cross regime (50 EMA < 200 EMA).")
        if price > ema_50:
            score += 5

    if price is not None and vwap is not None:
        if price > vwap:
            score += 5
            details.append("Price is above 20-day VWAP.")
        else:
            score -= 5

    if price is not None and bb_upper is not None and bb_lower is not None:
        band_diff = bb_upper - bb_lower
        if band_diff > 0:
            pct_b = (price - bb_lower) / band_diff
            if pct_b < 0.1:
                score += 10
                details.append("Price near lower Bollinger Band (potential bounce).")
            elif pct_b > 0.9:
                score -= 10
                details.append("Price near upper Bollinger Band (potential pullback).")

    score = max(0, min(100, score))
    summary = " ".join(details) if details else "Technical indicators are neutral."

    return {
        "score": int(score),
        "summary": summary
    }
