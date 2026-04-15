import asyncio
import logging
from typing import List
from app.etl.market_fetcher import MarketFetcher
from app.db.supabase_client import supabase_client
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initial set of Nifty 50 tokens for the platform
TARGET_TICKERS = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "LICI",
    "ASIANPAINT", "TITAN", "MARUTI", "SUNPHARMA", "BAJFINANCE"
]

async def process_ticker(ticker_symbol: str):
    """
    Fetches data for a single ticker and upserts it to Supabase.
    """
    logger.info(f"Processing {ticker_symbol}...")
    fetcher = MarketFetcher(ticker_symbol)
    
    success = await fetcher.fetch_all()
    if not success:
        logger.error(f"Failed to fetch data for {ticker_symbol}")
        return

    payload = fetcher.get_market_data_payload()
    if not payload:
        logger.warning(f"No data payload generated for {ticker_symbol}")
        return

    try:
        # Upsert into market_data table
        response = supabase_client.table("market_data").upsert(payload).execute()
        logger.info(f"✅ Successfully updated {ticker_symbol} in database.")
    except Exception as e:
        logger.error(f"Error upserting {ticker_symbol}: {e}")

async def run_pipeline(tickers: List[str] = TARGET_TICKERS):
    """
    Orchestrates the full market data update pipeline.
    """
    logger.info(f"Starting Market Data Pipeline for {len(tickers)} tickers...")
    
    # Process sequentially to avoid rate limiting issues with yfinance/Supabase for now
    for ticker in tickers:
        await process_ticker(ticker)
        # Small sleep to be polite to APIs
        await asyncio.sleep(1)
    
    logger.info("Market Data Pipeline execution complete.")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
