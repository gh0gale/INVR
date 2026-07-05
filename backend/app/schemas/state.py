from typing import TypedDict, Dict, Any, List, Optional
from app.schemas.bronze import BronzePayload
from app.schemas.silver import SilverMetrics
from app.schemas.gold import VerdictDraft

class UserProfile(TypedDict):
    risk_tolerance: str       # "conservative", "moderate", "aggressive"
    experience_level: str     # "beginner", "intermediate", "expert"
    goal: str                 # e.g., "Capital preservation", "Aggressive growth"
    available_capital: float

class AnalysisState(TypedDict):
    # Inputs
    ticker: str
    timeframe: str
    user_profile: UserProfile
    
    # Pipeline Payloads
    bronze: Optional[BronzePayload]
    silver: Optional[SilverMetrics]
    gold: Optional[VerdictDraft]
    
    # Final Output
    llm_output: Optional[Dict[str, Any]]
    errors: List[str]

    retry_count: int
    correction_note: Optional[str]