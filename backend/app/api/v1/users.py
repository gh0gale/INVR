from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserProfileCreate, UserFullEvaluation, UserPersonaResponse, PortfolioModelSchema
from app.services.portfolio_normalizer import PortfolioNormalizer
from app.services.persona_engine import PersonaEngine
from app.db.supabase_client import supabase_client
import uuid

router = APIRouter()
normalizer = PortfolioNormalizer()
engine = PersonaEngine()

@router.post("/profile", response_model=UserFullEvaluation)
async def create_user_profile(data: UserProfileCreate):
    """
    Creates or updates a user profile, computes the persona, 
    and normalizes the portfolio model.
    """
    user_id = "809d95fd-019e-46db-ae53-e4ee1b83ff03" # Provided by user for testing
    
    # 1. Normalize Portfolio
    normalized_portfolio = normalizer.normalize(data.raw_portfolio_data)
    
    # 2. Compute Persona
    profile_dict = data.profile.dict()
    risk_score = engine.calculate_risk_score(profile_dict)
    persona_label = engine.get_persona_label(risk_score)
    weights = engine.get_scoring_weights(risk_score)
    
    # 3. Save to Supabase (Layer 1: Profile)
    try:
        profile_entry = profile_dict.copy()
        profile_entry["id"] = user_id
        supabase_client.table("user_profiles").upsert(profile_entry).execute()
        
        # Save Layer 2: Persona
        persona_entry = {
            "id": user_id,
            "risk_score": risk_score,
            "persona_label": persona_label,
            "scoring_weight_profile": weights
        }
        supabase_client.table("user_personas").upsert(persona_entry).execute()
        
        # Save Layer 3: Portfolio
        portfolio_entry = {
            "user_id": user_id,
            "sector_weight_ranges": normalized_portfolio
        }
        supabase_client.table("portfolio_models").upsert(portfolio_entry).execute()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return UserFullEvaluation(
        profile=data.profile,
        persona=UserPersonaResponse(
            risk_score=risk_score,
            persona_label=persona_label,
            preferred_sectors=[], 
            sector_concentration_flags=[],
            diversification_score=0.0,
            scoring_weight_profile=weights
        ),
        portfolio=PortfolioModelSchema(sector_weight_ranges=normalized_portfolio)
    )
