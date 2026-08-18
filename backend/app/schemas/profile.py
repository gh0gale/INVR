import hashlib
import json
from typing import Dict, Literal
from pydantic import BaseModel, Field, model_validator, PrivateAttr


class UserProfileRequest(BaseModel):
    experience: Literal["beginner", "intermediate", "advanced"]
    goal: Literal["wealth_growth", "dividend_income", "capital_preservation"]
    timeframe: Literal["intraday", "swing", "positional", "long_term"]
    risk: Literal["conservative", "moderate", "aggressive"]
    portfolio: Dict[str, float] = Field(..., description="Asset class allocations mapping")
    capital: float = Field(..., ge=0, description="Capital in INR")

    _contradictions_flagged: list[str] = PrivateAttr(default_factory=list)

    @model_validator(mode="after")
    def validate_portfolio_weights(self) -> "UserProfileRequest":
        # 1. Rejection Constraint: Sum of weights must equal 1.0 ± 0.01
        total_weight = sum(self.portfolio.values())
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(f"Portfolio allocation weights must sum up to 1.0 (Current sum: {total_weight})")
        return self

    @model_validator(mode="after")
    def check_profile_contradictions(self) -> "UserProfileRequest":
        # 2. Contradiction Check: Flag but don't break execution
        self._contradictions_flagged = []
        if self.goal == "capital_preservation" and self.risk == "aggressive":
            self._contradictions_flagged.append(
                "Contradiction: Aggressive risk profile paired with a Capital Preservation goal."
            )
        return self


class UserProfileResponse(UserProfileRequest):
    profile_version_hash: str
    contradictions_flagged: list[str] = Field(default_factory=list)

    @classmethod
    def create_with_hash(cls, request_data: UserProfileRequest, contradictions: list[str]) -> "UserProfileResponse":
        # Deterministic hash over sorted values, used purely to detect that a
        # profile changed. SHA-256 rather than MD5: the use is not adversarial,
        # but a weak digest in a financial codebase is a needless finding.
        serialized_profile = json.dumps(request_data.model_dump(), sort_keys=True)
        version_hash = hashlib.sha256(serialized_profile.encode("utf-8")).hexdigest()
        
        return cls(
            **request_data.model_dump(),
            profile_version_hash=version_hash,
            contradictions_flagged=contradictions
        )