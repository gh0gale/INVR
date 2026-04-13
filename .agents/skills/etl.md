---
name: etl-pipeline
description: >
  ETL and data pipeline patterns for the AI Investment Intelligence platform.
  Use when building: market data fetcher (yfinance), metric computation (PE, PEG, RSI,
  MACD, SMA, EMA, Beta, Volatility), daily pipeline orchestration, DB seeding, data
  quality verification, or vector DB population.
  Triggers on: "process data", "fetch market data", "seed database", "compute metrics",
  "data pipeline", "update prices", "generate embeddings", "populate vector DB",
  "daily pipeline", "cron job", "idempotent update".
---

# ETL Pipeline Patterns — Investment Intelligence Platform

## Rule 1 — Every Script Must Be Idempotent

Safe to run multiple times with the same result. Check before inserting:

```python
def upsert_market_data(db, ticker: str, metric: str, value: float, fetched_at: datetime):
    """Insert or update — never duplicate rows."""
    existing = db.query(MarketDataCache).filter_by(ticker=ticker, metric_name=metric).first()
    if existing:
        if existing.fetched_at >= fetched_at:
            logger.info("skip_fresh", ticker=ticker, metric=metric)
            return False  # already have newer data
        existing.value = value
        existing.fetched_at = fetched_at
    else:
        db.add(MarketDataCache(ticker=ticker, metric_name=metric, value=value, fetched_at=fetched_at))
    return True
```

## Market Data Fetcher

```python
# backend/etl/market_fetcher.py
import yfinance as yf
import structlog

logger = structlog.get_logger()

class MarketFetcher:
    """Wraps yfinance for mockability. Never call yf.Ticker directly outside this class."""

    def __init__(self, ticker_cls=None):
        self._ticker_cls = ticker_cls or yf.Ticker

    def fetch_info(self, symbol: str) -> dict:
        try:
            t = self._ticker_cls(symbol)
            return t.info or {}
        except Exception as e:
            logger.error("fetch_info_failed", symbol=symbol, error=str(e))
            return {}

    def fetch_history(self, symbol: str, period: str = "1y", interval: str = "1d"):
        try:
            t = self._ticker_cls(symbol)
            return t.history(period=period, interval=interval)
        except Exception as e:
            logger.error("fetch_history_failed", symbol=symbol, error=str(e))
            return None

# In tests: MarketFetcher(ticker_cls=MockTicker)
```

## Metric Computation

```python
# backend/etl/metrics.py
import pandas as pd
import numpy as np

def compute_rsi(prices: pd.Series, window: int = 14) -> float | None:
    """Relative Strength Index (0–100). >70 = overbought, <30 = oversold."""
    if len(prices) < window + 1:
        return None
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else None

def compute_sma(prices: pd.Series, window: int) -> float | None:
    if len(prices) < window:
        return None
    return round(float(prices.rolling(window).mean().iloc[-1]), 2)

def compute_ema(prices: pd.Series, span: int) -> float | None:
    if len(prices) < span:
        return None
    return round(float(prices.ewm(span=span, adjust=False).mean().iloc[-1]), 2)

def compute_macd(prices: pd.Series) -> dict | None:
    if len(prices) < 26:
        return None
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return {
        "macd": round(float(macd_line.iloc[-1]), 4),
        "signal": round(float(signal.iloc[-1]), 4),
        "histogram": round(float((macd_line - signal).iloc[-1]), 4),
    }

def compute_volatility(prices: pd.Series, window: int = 30) -> float | None:
    if len(prices) < window:
        return None
    returns = prices.pct_change().dropna()
    return round(float(returns.tail(window).std() * np.sqrt(252)), 4)  # annualised

def compute_beta(stock_prices: pd.Series, market_prices: pd.Series, window: int = 252) -> float | None:
    if len(stock_prices) < window or len(market_prices) < window:
        return None
    sr = stock_prices.pct_change().dropna().tail(window)
    mr = market_prices.pct_change().dropna().tail(window)
    if len(sr) != len(mr):
        return None
    cov = np.cov(sr, mr)
    return round(float(cov[0, 1] / cov[1, 1]), 2) if cov[1, 1] != 0 else None
```

## Daily Pipeline

```python
# backend/etl/pipeline.py
import structlog
from datetime import datetime

logger = structlog.get_logger()

TICKERS = [
    "HDFCBANK.NS", "TCS.NS", "INFY.NS", "RELIANCE.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS",
    # extend via config or DB table
]

async def run_daily_pipeline(db, fetcher=None, tickers=None):
    """Idempotent daily pipeline: fetch → compute → upsert."""
    fetcher = fetcher or MarketFetcher()
    tickers = tickers or TICKERS
    now = datetime.utcnow()

    done, skipped, failed = 0, 0, 0

    for ticker in tickers:
        try:
            info = fetcher.fetch_info(ticker)
            history = fetcher.fetch_history(ticker)

            # --- 30+ Computed Metrics as per PS.md ---
            # Fundamental: EPS YoY, Rev CAGR (3Y), Profit Margin, ROE, ROCE, D/E, Interest Cov, FCF, Promoter/FII holdings.
            # Technical: SMA (20/50/200), EMA (20/50), RSI (14), MACD, Bollinger Bands, Volume Ratio, 52w High/Low, Support/Resistance.
            # Valuation: PE, PEG, Sector Median PE, Price-to-book, EV/EBITDA, Graham number.
            # Risk/Derivatives: Beta (1y), Volatility (30d), Max Drawdown, News Sentiment, FII open interest, PCR, IV.
            
            # (Example of legacy metrics mapped to new schema conventions):
            if history is not None and not history.empty:
                close = history["Close"]
                metrics["rsi_14"] = compute_rsi(close, 14)
                metrics["sma_50"] = compute_sma(close, 50)
                metrics["sma_200"] = compute_sma(close, 200)
                metrics["volatility_30d"] = compute_volatility(close, 30)

            # Upsert each metric
            for name, value in metrics.items():
                if value is not None:
                    created = upsert_market_data(db, ticker, name, float(value), now)
                    if created:
                        done += 1
                    else:
                        skipped += 1

        except Exception as e:
            logger.error("pipeline_ticker_failed", ticker=ticker, error=str(e))
            failed += 1

    logger.info("pipeline_complete", done=done, skipped=skipped, failed=failed)

    if failed > 0:
        logger.warning("pipeline_had_failures", count=failed)
    return {"done": done, "skipped": skipped, "failed": failed}
```

## Vector DB Seed (RAG Content)

```python
# backend/etl/seed_rag.py
FINANCIAL_CONCEPTS = [
    {
        "concept": "PE Ratio",
        "text": "Price-to-Earnings ratio compares a stock's price to its earnings per share. "
                "A high PE may indicate overvaluation or high growth expectations. "
                "Compare PE to industry average and historical PE for context."
    },
    {
        "concept": "PEG Ratio",
        "text": "PEG = PE / Earnings Growth Rate. Adjusts PE for growth. "
                "PEG < 1 = potentially undervalued. PEG > 1 = potentially overvalued. "
                "More useful than PE alone for growth stocks."
    },
    {
        "concept": "RSI",
        "text": "Relative Strength Index (0-100). RSI > 70 = overbought, may see pullback. "
                "RSI < 30 = oversold, may bounce. Use with other indicators, not alone."
    },
    # ... extend with 50+ concepts
]

def seed_vector_db(rag_service):
    texts = [c["text"] for c in FINANCIAL_CONCEPTS]
    rag_service.build_index(texts)
    logger.info("rag_seeded", count=len(texts))
```

## Data Quality Verification

Always verify after any ETL run:

```python
async def verify_pipeline_output(db, tickers: list[str]):
    """Run after pipeline to assert data quality."""
    from sqlalchemy import func, select

    total = await db.scalar(select(func.count()).select_from(MarketDataCache))
    logger.info("total_cached_metrics", count=total)
    assert total > 0, "Pipeline produced no data"

    for ticker in tickers[:5]:  # spot-check first 5
        count = await db.scalar(
            select(func.count())
            .select_from(MarketDataCache)
            .where(MarketDataCache.ticker == ticker)
        )
        assert count >= 3, f"Ticker {ticker} has only {count} metrics — expected ≥3"

    # Check freshness & Staleness Flags
    oldest = await db.scalar(select(func.min(MarketDataCache.fetched_at)))
    age_hours = (datetime.utcnow() - oldest).total_seconds() / 3600
    if age_hours > 24:
        logger.warning("stale_data_detected", oldest_hours=round(age_hours, 1))
        # Add staleness flags to out-of-date metrics here, actively excluding them from analysis recommendations.
```

## Cron Trigger (APScheduler)

```python
# backend/main.py — add to startup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        run_daily_pipeline,
        trigger="cron",
        hour=6, minute=0,  # 6:00 AM IST daily (before market open)
        args=[get_db_session()],
        id="daily_market_pipeline",
        replace_existing=True,
    )
    scheduler.start()
```

## Anti-Patterns — Never

- Run destructive operations without checking if output already exists (idempotency!)
- Leave a script that crashes halfway with no progress report
- Silently swallow exceptions — always `logger.error(...)` and count failures
- Hardcode ticker lists — load from config or DB
- Skip the final count/verification step
- Call `yf.Ticker()` directly outside of `MarketFetcher` wrapper
- Let a single ticker failure crash the entire pipeline
