from app.models.enums import RiskAppetite, ProficiencyLevel, InvestmentHorizon
from typing import Dict, Any

class PersonaEngine:
    """
    Computes risk scores, persona labels, and analysis weights for a user profile.
    """

    def calculate_risk_score(self, profile: Dict[str, Any]) -> float:
        # Weights from PS.md
        # Horizon: 30%
        # Appetite: 35%
        # Age: 20%
        # Income: 15%
        
        score = 0
        
        # 1. Horizon (30%)
        horizon_map = {
             InvestmentHorizon.INTRADAY: 100, # High risk activity
             InvestmentHorizon.SWING: 70,
             InvestmentHorizon.POSITIONAL: 50,
             InvestmentHorizon.LONG_TERM: 30 # Long term is safer
        }
        score += horizon_map.get(profile.get("investment_horizon"), 50) * 0.30
        
        # 2. Appetite (35%)
        appetite_map = {
            RiskAppetite.CONSERVATIVE: 20,
            RiskAppetite.MODERATE: 60,
            RiskAppetite.AGGRESSIVE: 100
        }
        score += appetite_map.get(profile.get("risk_appetite"), 50) * 0.35
        
        # 3. Age (20%) - Inverse relationship
        age = profile.get("age", 30)
        age_score = max(0, 100 - age) # Younger = higher risk capacity
        score += age_score * 0.20
        
        # 4. Income (15%) - Proxy via income bracket index
        score += 50 * 0.15 # Defaulting to middle for now
        
        return round(score, 2)

    def get_persona_label(self, risk_score: float) -> str:
        if risk_score <= 30: return "Conservative Income Seeker"
        if risk_score <= 55: return "Balanced Growth Investor"
        if risk_score <= 75: return "Growth-Oriented Investor"
        return "Aggressive Wealth Builder"

    def get_scoring_weights(self, risk_score: float) -> Dict[str, float]:
        """
        Adjusts analysis lens weights based on risk profile.
        Matching PS.md logic.
        """
        if risk_score <= 30: # Conservative
            return {"fundamental": 0.40, "valuation": 0.30, "technical": 0.10, "risk": 0.20}
        if risk_score <= 70: # Balanced/Growth
            return {"fundamental": 0.30, "valuation": 0.20, "technical": 0.30, "risk": 0.20}
        
        # Aggressive
        return {"fundamental": 0.20, "valuation": 0.10, "technical": 0.50, "risk": 0.20}
