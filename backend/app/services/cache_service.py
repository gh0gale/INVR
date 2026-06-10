import json
import os
import time
import asyncio
import pandas as pd
from typing import Optional

# TODO: [PRODUCTION] Migrate this entire file to use Redis. 
# Currently using local JSON file caching to save DB read/writes and avoid Docker during local testing.

CACHE_DIR = os.path.join(os.getcwd(), ".local_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _get_filepath(key: str) -> str:
    """Sanitize the cache key to create a valid Windows/Linux filename."""
    safe_key = key.replace(":", "_").replace("^", "")
    return os.path.join(CACHE_DIR, f"{safe_key}.json")

def _is_expired(filepath: str, ttl_seconds: int) -> bool:
    """Check if the file modification time is older than the TTL."""
    if not os.path.exists(filepath):
        return True
    file_age = time.time() - os.path.getmtime(filepath)
    return file_age > ttl_seconds

async def get_cached_dataframe(key: str, ttl_seconds: int) -> Optional[pd.DataFrame]:
    filepath = _get_filepath(key)
    
    if _is_expired(filepath, ttl_seconds):
        return None
        
    def _read():
        return pd.read_json(filepath, orient="index")
    
    try:
        return await asyncio.to_thread(_read)
    except Exception:
        return None

async def set_cached_dataframe(key: str, df: pd.DataFrame, ttl_seconds: int):
    # ttl_seconds is unused here because we check expiry on read via os.path.getmtime
    filepath = _get_filepath(key)
    def _write():
        df.to_json(filepath, orient="index")
    await asyncio.to_thread(_write)

async def get_cached_dict(key: str, ttl_seconds: int) -> Optional[dict]:
    filepath = _get_filepath(key)
    
    if _is_expired(filepath, ttl_seconds):
        return None
        
    def _read():
        with open(filepath, 'r') as f:
            return json.load(f)
            
    try:
        return await asyncio.to_thread(_read)
    except Exception:
        return None

async def set_cached_dict(key: str, data: dict, ttl_seconds: int):
    filepath = _get_filepath(key)
    def _write():
        with open(filepath, 'w') as f:
            json.dump(data, f)
    await asyncio.to_thread(_write)