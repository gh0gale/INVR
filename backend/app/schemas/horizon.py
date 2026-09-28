from typing import Literal, Optional

from pydantic import BaseModel

# The horizons are the engine's own timeframes, the keys of PIPELINE_CONFIG in
# app/pipeline/router.py. Mirrored in frontend/src/lib/horizons.ts.
Timeframe = Literal["intraday", "swing", "positional", "long_term"]


class StockHorizonIn(BaseModel):
    timeframe: Timeframe


class StockHorizon(BaseModel):
    ticker: str
    timeframe: Optional[Timeframe]   # None: no saved choice, use the profile's
