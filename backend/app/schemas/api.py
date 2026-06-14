from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class APIUserProfile(BaseModel):
    risk_tolerance: str = Field(default="moderate")
    experience_level: str = Field(default="intermediate")
    goal: str = Field(default="Capital preservation and steady growth")
    available_capital: float = Field(default=100000.0)

class PipelineRequest(BaseModel):
    ticker: str = Field(..., description="NSE Stock ticker symbol (e.g., RELIANCE.NS)")
    timeframe: str = Field(..., description="swing | positional | long_term")
    user_profile: Optional[APIUserProfile] = Field(default_factory=APIUserProfile)

class PipelineResponse(BaseModel):
    success: bool
    ticker: str
    timeframe: str
    verdict: Optional[str]
    llm_analysis: Optional[Dict[str, Any]]
    errors: Optional[list[str]]