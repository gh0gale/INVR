from pydantic import BaseModel
from typing import Literal, Dict, List, Optional

class TradeSetup(BaseModel):
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    target_1: float
    target_2: float
    suggested_position_size: float
    risk_per_trade_inr: float
    risk_reward_ratio: float

class VerdictDraft(BaseModel):
    ticker: str
    timeframe: str
    verdict: Literal["STRONG BUY", "BUY ON DIP", "MONITOR", "CAUTION", "AVOID"]
    confidence_score: float
    gate_results: Dict[str, str]       # e.g., {"trend": "PASS", "rsi": "WARN"}
    what_to_watch: List[str]           # Actionable conditions for the user
    trade_setup: Optional[TradeSetup] = None
    primary_reason: str