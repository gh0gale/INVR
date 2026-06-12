from pydantic import BaseModel, Field
from typing import List, Literal

class AnalysisOutput(BaseModel):
    # Update this in both VerdictDraft and AnalysisOutput
    verdict: Literal["STRONG BUY", "BUY ON DIP", "MONITOR", "CAUTION", "AVOID"] = Field(
        ..., description="MUST perfectly match the quantitative verdict."
    )
    confidence_score: float = Field(
        ..., description="The exact confidence score computed by the system."
    )
    personalized_reasoning: List[str] = Field(
        ..., description="3-4 brief sentences explaining the verdict based on the user's profile."
    )
    what_to_watch: List[str] = Field(
        ..., description="The actionable monitoring conditions."
    )
    risk_warning: str = Field(
        ..., description="A mandatory 1-sentence risk warning tailored to the stock's debt or circuit status."
    )
    tutor_triggers: List[str] = Field(
        ..., description="Financial jargon used in this report that a beginner might want explained."
    )