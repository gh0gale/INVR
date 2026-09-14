import asyncio
from app.pipeline.router import get_pipeline_manifest
from app.schemas.bronze import BronzePayload
from app.integrations.market_data import (
    fetch_yfinance_history, 
    fetch_yfinance_fundamentals, 
    fetch_nse_circuit_status
)
from app.services.cache_service import (
    get_cached_dataframe, set_cached_dataframe, 
    get_cached_dict, set_cached_dict
)
from app.config import settings

# Hardcoded sector mapping for prototype 
# TODO: [PRODUCTION] Move this to a Supabase lookup table.
# The sector index is only used for relative strength and the market-regime
# read, and regime needs 200 bars of history. A swing run fetches 6mo of daily
# bars (~126), which meant `market_regime` was never computed and the bearish
# override in the Gold layer was dead code on the default horizon
# (audit finding NEW-BE-08). Both series are indexed from the right, so a longer
# sector window leaves relative strength unchanged.
SECTOR_PERIOD = {
    "intraday": "5d",
    "swing": "2y",
    "positional": "2y",
    "long_term": "5y",
}

# Benchmarks for relative strength and the market-regime override (audit
# DATA-03). The old map was keyed "IT", "Auto", "Bank", "FMCG" - names yfinance
# never returns - so only "Financial Services" ever matched, and its index
# (^CNXFIN) has a single row on Yahoo. Relative strength and the bearish
# override therefore ran for no stock at all.
#
# A mapping alone is not enough either: as of 2026-09 Yahoo carries current
# history for only a few NSE sector indices, and several others stopped
# updating in July 2026 while still returning rows. So each candidate is used
# only if it is fresh and long enough (`_usable`), and the NIFTY 50 is the
# fallback - a stock measured against the broad market rather than a stale
# sector series or nothing. Keys are yfinance's own `industry` / `sector` names.
BROAD_MARKET_INDEX = "^NSEI"

INDUSTRY_BENCHMARKS = {
    "Banks - Regional": "^NSEBANK",
    "Banks - Diversified": "^NSEBANK",
    "Auto Manufacturers": "^CNXAUTO",
    "Auto Parts": "^CNXAUTO",
}

SECTOR_BENCHMARKS = {
    "Technology": "^CNXIT",
    "Healthcare": "^CNXPHARMA",
    "Financial Services": "^CNXFIN",
    "Consumer Defensive": "^CNXFMCG",
    "Consumer Cyclical": "^CNXCONSUM",
    "Basic Materials": "^CNXMETAL",
    "Energy": "^CNXENERGY",
    "Utilities": "^CNXENERGY",
    "Real Estate": "^CNXREALTY",
    "Industrials": "^CNXINFRA",
}

BENCHMARK_NAMES = {
    "^NSEI": "NIFTY 50", "^NSEBANK": "NIFTY BANK", "^CNXIT": "NIFTY IT",
    "^CNXPHARMA": "NIFTY PHARMA", "^CNXFIN": "NIFTY FINANCIAL SERVICES",
    "^CNXAUTO": "NIFTY AUTO", "^CNXFMCG": "NIFTY FMCG", "^CNXCONSUM": "NIFTY INDIA CONSUMPTION",
    "^CNXMETAL": "NIFTY METAL", "^CNXENERGY": "NIFTY ENERGY", "^CNXREALTY": "NIFTY REALTY",
    "^CNXINFRA": "NIFTY INFRASTRUCTURE",
}

# Bars the relative-strength lookback needs in Silver, per timeframe.
BENCHMARK_MIN_ROWS = {"swing": 20, "positional": 50, "long_term": 12}
# How far a benchmark's last bar may trail the stock's before it is stale.
MAX_BENCHMARK_LAG_DAYS = 7


def benchmark_candidates(fundamentals: dict | None) -> list[str]:
    f = fundamentals or {}
    first = INDUSTRY_BENCHMARKS.get(f.get("industry")) or SECTOR_BENCHMARKS.get(f.get("sector"))
    return [c for c in (first, BROAD_MARKET_INDEX) if c] if first != BROAD_MARKET_INDEX else [BROAD_MARKET_INDEX]


def _usable(benchmark_df, price_df, min_rows: int) -> bool:
    if benchmark_df is None or len(benchmark_df) < min_rows:
        return False
    lag = (price_df.index[-1].date() - benchmark_df.index[-1].date()).days
    return abs(lag) <= MAX_BENCHMARK_LAG_DAYS


async def build_bronze_payload(ticker: str, timeframe: str) -> BronzePayload:
    ticker = ticker if ticker.endswith(settings.MARKET_SUFFIX) else f"{ticker}{settings.MARKET_SUFFIX}"
    manifest = get_pipeline_manifest(timeframe)
    # "not_checked" when this horizon does not look at circuits, "unknown" when
    # it does and NSE did not answer. Gold scores neither (audit DATA-01).
    price_df, sector_df, fundamentals = None, None, None
    circuit = "unknown" if manifest["needs_circuits"] else "not_checked"
    benchmark_name = None
    
    # Define TTLs: 5 mins for intraday, 12 hours (43200s) for daily/longer
    ttl = 300 if timeframe == "intraday" else 43200 
    
    # --- 1. Fetch Price Data ---
    cache_key_price = f"price:{ticker}:{manifest['period']}:{manifest['interval']}"
    
    # Notice we pass `ttl` to the read function now
    price_df = await get_cached_dataframe(cache_key_price, ttl)
    
    if price_df is None:
        price_df = await fetch_yfinance_history(ticker, manifest['period'], manifest['interval'])
        await set_cached_dataframe(cache_key_price, price_df, ttl)
        
    current_price = price_df['Close'].iloc[-1]

    # --- 2. Fetch Optional Data Concurrently ---
    tasks = []
    
    if manifest["needs_fundamentals"]:
        async def get_funds():
            # Versioned whenever the dict's shape or units change, or the old
            # key serves a pre-fix dict for up to 24 hours. v2: no defaulted
            # values (DATA-02). v3: explicit-unit D/E and ROE (DATA-04).
            cache_key = f"funds:v3:{ticker}"
            # Fundamentals change slowly, cache for 24 hours (86400s)
            data = await get_cached_dict(cache_key, 86400)
            if not data:
                data = await fetch_yfinance_fundamentals(ticker)
                await set_cached_dict(cache_key, data, 86400)
            return data
        tasks.append(("fundamentals", get_funds()))

    if manifest["needs_circuits"]:
        tasks.append(("circuit", fetch_nse_circuit_status(ticker, current_price)))

    if tasks:
        results = await asyncio.gather(*(t[1] for t in tasks), return_exceptions=True)
        for i, (task_name, _) in enumerate(tasks):
            res = results[i]
            if not isinstance(res, Exception):
                if task_name == "fundamentals": fundamentals = res
                if task_name == "circuit": circuit = res

    # --- 3. Benchmark (sector index, else the broad market) ---
    if manifest["needs_sector"]:
        sector_period = SECTOR_PERIOD.get(timeframe, manifest['period'])
        min_rows = BENCHMARK_MIN_ROWS.get(timeframe, 20)
        for index_ticker in benchmark_candidates(fundamentals):
            cache_key_sector = f"sector:{index_ticker}:{sector_period}:{manifest['interval']}"
            candidate = await get_cached_dataframe(cache_key_sector, ttl)
            if candidate is None:
                try:
                    candidate = await fetch_yfinance_history(index_ticker, sector_period, manifest['interval'])
                except Exception:
                    continue
                await set_cached_dataframe(cache_key_sector, candidate, ttl)
            if _usable(candidate, price_df, min_rows):
                sector_df = candidate
                benchmark_name = BENCHMARK_NAMES.get(index_ticker, index_ticker)
                break


    inst_activity = None
    if manifest["needs_institutional"]:
        # TODO: [PRODUCTION] Integrate real FII/DII data from NSE bulk deals API or NSDL/CDSL.
        # Until then, return None to avoid fake bias signals.
        inst_activity = None

    return BronzePayload(
        ticker=ticker,
        timeframe=timeframe,
        circuit_status=circuit,
        price_history=price_df,
        sector_history=sector_df,
        fundamentals=fundamentals,
        institutional_activity=inst_activity,
        benchmark_index=benchmark_name,
    )