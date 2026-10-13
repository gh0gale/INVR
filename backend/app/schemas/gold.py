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

# ---------------------------------------------------------------- v2 (shadow)
# Scored engine from docs/verdict_engine_plan.md, Phase 1. Recorded beside the
# v1 verdict until the cutover; nothing user-facing reads it yet.

class FactorResult(BaseModel):
    name: str
    score: Optional[float] = None      # [-1, 1]; None when the input is missing
    weight: float = 0.0
    reason: str = ""
    watch_item: Optional[str] = None


class PriceLevels(BaseModel):
    """ATR levels only. Position size is per user, so it is not stored here."""
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    target_1: float
    target_2: float
    risk_reward_ratio: float


class ScoredVerdict(BaseModel):
    ruleset: str
    ticker: str
    timeframe: str
    verdict: Literal["STRONG BUY", "BUY ON DIP", "MONITOR", "CAUTION", "AVOID"]
    composite: float                   # [-1, 1], missing factors count as 0
    coverage: float                    # share of horizon weight that had data
    confidence_score: float
    primary_reason: str
    caps_applied: List[str]
    factors: List[FactorResult]
    what_to_watch: List[str]
    price_levels: Optional[PriceLevels] = None
