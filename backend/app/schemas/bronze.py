from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
import pandas as pd

class BronzePayload(BaseModel):
    ticker: str
    timeframe: str  # "intraday", "swing", "positional", "long_term"
    # "none" / "upper" / "lower" as NSE reported it; "unknown" when NSE did not
    # answer; "not_checked" when the timeframe does not fetch it. Only the
    # first three are scored by the Gold layer.
    circuit_status: Optional[str] = "none"
    # Display name of the index relative strength was measured against, e.g.
    # "NIFTY IT", or "NIFTY 50" when no fresh sector index exists. None when
    # there was no usable benchmark at all.
    benchmark_index: Optional[str] = None
    
    # Dataframes held in memory or as structured objects during pipeline execution
    price_history: pd.DataFrame = Field(..., description="DataFrame with Open, High, Low, Close, Volume")
    sector_history: Optional[pd.DataFrame] = Field(None, description="Sector Index DataFrame or None")
    
    # Polymorphic structures to gracefully absorb multi-horizon variation
    fundamentals: Optional[Dict[str, Any]] = Field(None, description="Polymorphic dictionary for financial stats")
    institutional_activity: Optional[Dict[str, Any]] = Field(None, description="FII/DII and bulk deal arrays")

    model_config = ConfigDict(arbitrary_types_allowed=True)