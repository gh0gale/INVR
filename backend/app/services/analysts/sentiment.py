from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def calculate_score(data: dict) -> dict:
    """
    Macro & Sentiment Analyst
    Calculates proxy News NLP sentiment, VIX impact, mocked FII/DII logic.
    Returns a score 0-100.
    """
    score = 50
    details = []

    news = data.get("recent_news_headlines", [])
    if news:
        sentiments = []
        for headline in news:
            compound = analyzer.polarity_scores(headline)['compound']
            sentiments.append(compound)
        avg_sentiment = sum(sentiments) / len(sentiments)
        if avg_sentiment > 0.2:
            score += 15
            details.append("News sentiment is generally positive.")
        elif avg_sentiment < -0.2:
            score -= 20
            details.append("News sentiment is negative.")
    else:
        details.append("No recent news to analyze.")

    vix = data.get("india_vix")
    if vix is not None:
        if vix > 20:
            score -= 15
            details.append("High overall market fear (India VIX > 20).")
        elif vix < 15:
            score += 10
            details.append("Calm overall market environment.")

    fii = data.get("fii_dii_net", "neutral")
    if fii == "bullish":
         score += 10
    elif fii == "bearish":
         score -= 10

    repo = data.get("rbi_repo_rate")
    if repo is not None and repo > 6.0:
        details.append(f"High interest rate environment ({repo}%).")

    score = max(0, min(100, score))
    summary = " ".join(details) if details else "Sentiment and Macro context is neutral."

    return {
        "score": int(score),
        "summary": summary
    }
