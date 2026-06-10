from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel
import pandas as pd

class BronzePayload(BaseModel):
    ticker: str
    timeframe: str
    circuit_status: Literal["upper", "lower", "none", "unknown"] = "unknown"
    
    # In-memory Pandas DataFrames
    price_history: Optional[pd.DataFrame] = None
    sector_history: Optional[pd.DataFrame] = None
    
    # Dictionaries for fundamental/institutional data
    fundamentals: Optional[Dict[str, Any]] = None
    institutional_activity: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True