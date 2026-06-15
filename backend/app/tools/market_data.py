import yfinance as yf
import asyncio

async def fetch_stock_news(ticker: str) -> str:
    """Fetches the latest 3 news headlines for a ticker to inject into the LLM context."""
    def _fetch():
        clean_ticker = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
        stock = yf.Ticker(clean_ticker)
        news = stock.news
        if not news:
            return "No recent news found for this asset."
        
        headlines = [f"- {item['title']} ({item['publisher']})" for item in news[:3]]
        return "\n".join(headlines)
        
    try:
        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return f"News tool failed: {str(e)}"