from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import pandas as pd

class BronzePayload(BaseModel):
    ticker: str
    timeframe: str  # "intraday", "swing", "positional", "long_term"
    circuit_status: Optional[str] = "none"  # "none", "upper", "lower", or "unknown"
    
    # Dataframes held in memory or as structured objects during pipeline execution
    price_history: pd.DataFrame = Field(..., description="DataFrame with Open, High, Low, Close, Volume")
    sector_history: Optional[pd.DataFrame] = Field(None, description="Sector Index DataFrame or None")
    
    # Polymorphic structures to gracefully absorb multi-horizon variation
    fundamentals: Optional[Dict[str, Any]] = Field(None, description="Polymorphic dictionary for financial stats")
    institutional_activity: Optional[Dict[str, Any]] = Field(None, description="FII/DII and bulk deal arrays")

    class Config:
        arbitrary_types_allowed = True