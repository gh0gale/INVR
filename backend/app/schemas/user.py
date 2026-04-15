from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from app.models.enums import IncomeBracket, RiskAppetite, PrimaryGoal, ProficiencyLevel, InvestmentHorizon

class PortfolioModelSchema(BaseModel):
    # E.g. {"IT": {"min": 0.40, "max": 0.55}}
    sector_weight_ranges: Dict[str, Dict[str, float]]

class UserProfileBase(BaseModel):
    age: int = Field(..., ge=18)
    income_bracket: Optional[IncomeBracket] = None
    monthly_investable: float = 0.0
    risk_appetite: RiskAppetite
    investment_horizon_months: int = Field(..., gt=0)
    primary_goal: Optional[PrimaryGoal] = None
    
    # New Fields requested by user
    portfolio_size: float = 0.0
    proficiency_level: ProficiencyLevel = ProficiencyLevel.BEGINNER
    investment_horizon: InvestmentHorizon = InvestmentHorizon.LONG_TERM
    investment_amount_target: float = 0.0

class UserProfileCreate(BaseModel):
    # This captures the raw "noisy" input for the normalizer
    profile: UserProfileBase
    raw_portfolio_data: Optional[str] = None # Text like "mostly IT and banking"
    existing_holdings: List[str] = [] # List of tickers

class UserPersonaResponse(BaseModel):
    risk_score: float
    persona_label: str
    preferred_sectors: List[str]
    sector_concentration_flags: List[str]
    diversification_score: float
    scoring_weight_profile: Dict[str, float]

class UserFullEvaluation(BaseModel):
    profile: UserProfileBase
    persona: UserPersonaResponse
    portfolio: PortfolioModelSchema
