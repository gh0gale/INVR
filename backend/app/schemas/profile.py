import hashlib
import json
from typing import Dict, Literal
from pydantic import BaseModel, Field, model_validator, PrivateAttr

# Width of the `user_profiles.profile_version_hash` column. Raise this only
# together with an ALTER TABLE; see backend/migrations/002_widen_profile_hash.sql.
HASH_LENGTH = 32


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
        """Weights must sum to 1.0 - unless there is no portfolio at all.

        Audit finding E2E-01. An empty dict used to fail this check with
        "must sum up to 1.0 (Current sum: 0)", so a user holding only cash
        could not create a profile. That is not an edge case for this product:
        a beginner with capital and no holdings is precisely the person the
        onboarding flow is written for, and the old rule forced them to invent
        an allocation. Fabricated holdings then flow into `semantic_profile`
        and the tutor's portfolio routing mode, so the cost was not cosmetic.

        An empty portfolio means "no holdings yet". A non-empty one is still
        required to be a complete allocation, because a partial one is
        ambiguous: it cannot be distinguished from a mistake.
        """
        if not self.portfolio:
            return self

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
        #
        # Truncated to HASH_LENGTH because the live `user_profiles`
        # .profile_version_hash column is varchar(32), sized when this was an
        # MD5 digest. A full 64-char SHA-256 overflows it and Postgres rejects
        # the upsert with 22001 "value too long". 32 hex chars is 128 bits,
        # which is far beyond what change detection needs.
        serialized_profile = json.dumps(request_data.model_dump(), sort_keys=True)
        version_hash = hashlib.sha256(
            serialized_profile.encode("utf-8")
        ).hexdigest()[:HASH_LENGTH]
        
        return cls(
            **request_data.model_dump(),
            profile_version_hash=version_hash,
            contradictions_flagged=contradictions
        )