import asyncio
import logging
from app.services.portfolio_normalizer import PortfolioNormalizer
from app.services.persona_engine import PersonaEngine
from app.db.supabase_client import supabase_client
from app.models.enums import IncomeBracket, RiskAppetite, PrimaryGoal, ProficiencyLevel, InvestmentHorizon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config provided by user
USER_ID = "809d95fd-019e-46db-ae53-e4ee1b83ff03"

async def seed_investor_profile():
    logger.info(f"Starting seed for User ID: {USER_ID}")
    
    normalizer = PortfolioNormalizer()
    engine = PersonaEngine()

    # 1. Mock Data (matching your request)
    raw_portfolio_text = "I have mostly IT and Banking stocks but I also have some Pharma."
    
    profile_data = {
        "age": 28,
        "income_bracket": IncomeBracket.FROM_10L_TO_25L,
        "monthly_investable": 50000,
        "risk_appetite": RiskAppetite.AGGRESSIVE,
        "investment_horizon_months": 60,
        "primary_goal": PrimaryGoal.WEALTH_CREATION,
        "portfolio_size": 500000,
        "proficiency_level": ProficiencyLevel.INTERMEDIATE,
        "investment_horizon": InvestmentHorizon.LONG_TERM,
        "investment_amount_target": 25000
    }

    # 2. Logic: Normalize & Score
    normalized_portfolio = normalizer.normalize(raw_portfolio_text)
    logger.info(f"Normalized Portfolio: {normalized_portfolio}")

    risk_score = engine.calculate_risk_score(profile_data)
    persona_label = engine.get_persona_label(risk_score)
    weights = engine.get_scoring_weights(risk_score)
    
    logger.info(f"Computed Persona: {persona_label} (Score: {risk_score})")

    # 3. Persistence
    try:
        # Layer 1: Profile
        profile_entry = profile_data.copy()
        profile_entry["id"] = USER_ID
        supabase_client.table("user_profiles").upsert(profile_entry).execute()
        
        # Layer 2: Persona
        persona_entry = {
            "id": USER_ID,
            "risk_score": risk_score,
            "persona_label": persona_label,
            "scoring_weight_profile": weights
        }
        supabase_client.table("user_personas").upsert(persona_entry).execute()
        
        # Layer 3: Portfolio
        portfolio_entry = {
            "user_id": USER_ID,
            "sector_weight_ranges": normalized_portfolio
        }
        supabase_client.table("portfolio_models").upsert(portfolio_entry).execute()
        
        logger.info("✅ Successfully seeded user evaluation data in Supabase.")
        
    except Exception as e:
        logger.error(f"❌ Failed to seed user: {e}")

if __name__ == "__main__":
    asyncio.run(seed_investor_profile())
