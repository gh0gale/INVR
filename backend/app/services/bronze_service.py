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

# Hardcoded sector mapping for prototype 
# TODO: [PRODUCTION] Move this to a Supabase lookup table.
SECTOR_INDEX_MAP = {
    "Auto": "^CNXAUTO",
    "IT": "^CNXIT",
    "Bank": "^NSEBANK",
    "Financial Services": "^CNXFIN",
    "FMCG": "^CNXFMCG"
}

async def build_bronze_payload(ticker: str, timeframe: str) -> BronzePayload:
    manifest = get_pipeline_manifest(timeframe)
    price_df, sector_df, fundamentals, circuit = None, None, None, "none"
    
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
            cache_key = f"funds:{ticker}"
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

    # --- 3. Sector Data ---
    if manifest["needs_sector"] and fundamentals:
        sector_name = fundamentals.get("sector")
        index_ticker = SECTOR_INDEX_MAP.get(sector_name)
        
        if index_ticker:
            cache_key_sector = f"sector:{index_ticker}:{manifest['period']}:{manifest['interval']}"
            sector_df = await get_cached_dataframe(cache_key_sector, ttl)
            if sector_df is None:
                sector_df = await fetch_yfinance_history(index_ticker.replace('.NS', ''), manifest['period'], manifest['interval'])
                await set_cached_dataframe(cache_key_sector, sector_df, ttl)


    inst_activity = None
    if manifest["needs_institutional"]:
        inst_activity = {
            "fii_net_activity": 125.5,
            "dii_net_activity": -40.2
        }

    return BronzePayload(
        ticker=ticker,
        timeframe=timeframe,
        circuit_status=circuit,
        price_history=price_df,
        sector_history=sector_df,
        fundamentals=fundamentals,
        institutional_activity=inst_activity 
    )