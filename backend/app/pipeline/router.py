from typing import Dict, Any

PIPELINE_CONFIG = {
    "intraday": {
        "period": "5d",
        "interval": "5m",
        "needs_sector": False,
        "needs_fundamentals": False,
        "needs_circuits": True,
        "needs_institutional": False
    },
    "swing": {
        "period": "6mo",
        "interval": "1d",
        "needs_sector": True,
        "needs_fundamentals": True, # Lightweight
        "needs_circuits": True,
        "needs_institutional": True
    },
    "positional": {
        "period": "1y",
        "interval": "1d",
        "needs_sector": True,
        "needs_fundamentals": True,
        "needs_circuits": True,
        "needs_institutional": False
    },
    "long_term": {
        "period": "5y",
        "interval": "1wk",
        "needs_sector": True,
        "needs_fundamentals": True,
        "needs_circuits": False,    # Irrelevant for 5-year holds
        "needs_institutional": False
    }
}

def get_pipeline_manifest(timeframe: str) -> Dict[str, Any]:
    """Retrieves the strict data-fetching manifest based on timeframe."""
    if timeframe not in PIPELINE_CONFIG:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return PIPELINE_CONFIG[timeframe]