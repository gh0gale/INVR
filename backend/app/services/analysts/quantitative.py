def calculate_score(data: dict) -> dict:
    """
    Quantitative Analyst
    Calculates Beta vs Nifty 50, Sharpe Ratio, Sortino Ratio, Max Drawdown, VaR.
    Returns a score 0-100.
    """
    score = 50
    details = []

    def g(key, default=None):
        val = data.get(key)
        return float(val) if val is not None else default

    beta = g("beta_calc") or g("beta_1y")
    sharpe = g("sharpe_ratio")
    sortino = g("sortino_ratio")
    max_dd = g("max_drawdown")
    var_95 = g("var_95")

    if sharpe is not None:
        if sharpe > 1.0:
            score += 15
            details.append(f"Excellent Sharpe ratio ({sharpe:.2f}).")
        elif sharpe > 0.5:
            score += 5
        elif sharpe < 0:
            score -= 15
            details.append("Negative Sharpe ratio (trailing 3y).")

    if sortino is not None:
        if sortino > 1.5:
            score += 10
            details.append(f"Superior downside protection (Sortino {sortino:.2f}).")
        elif sortino < 0:
            score -= 5

    if beta is not None:
        if beta > 1.5:
            score -= 10
            details.append(f"High systematic risk (Beta {beta:.2f}).")
        elif 0.5 <= beta <= 1.2:
            score += 5
            details.append("Stable market correlation.")

    if max_dd is not None: 
        if max_dd < -0.40:
            score -= 15
            details.append(f"Severe historical max drawdown ({(max_dd*100):.1f}%).")
        elif max_dd > -0.15: 
            score += 10
            details.append("Low historical drawdown risk.")

    if var_95 is not None:
        if var_95 < -0.05:
            score -= 10
            details.append("High daily Value-at-Risk.")

    score = max(0, min(100, score))
    summary = " ".join(details) if details else "Quantitative risk profile is average or missing data."

    return {
        "score": int(score),
        "summary": summary
    }
