import asyncio
from app.db.supabase_client import supabase_client
from app.models.enums import ProficiencyLevel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_ID = "809d95fd-019e-46db-ae53-e4ee1b83ff03"

async def verify_system():
    logger.info("--- 🛡️ AI STOCK SYSTEM VERIFICATION ---")
    
    # 1. Check Market Data & Enrichment
    market_resp = supabase_client.table("market_data").select("ticker, macd_line, support_level, revenue_cagr_3y, graham_number").limit(5).execute()
    stocks = market_resp.data
    if stocks:
        enriched_count = sum(1 for s in stocks if s.get('macd_line') is not None)
        logger.info(f"✅ Market Data: Found {len(stocks)}+ stocks. Enrichment: {enriched_count}/5 checked stocks have MACD/Support.")
    else:
        logger.error("❌ Market Data: No stocks found. Run app.etl.pipeline first.")

    # 2. Check User Intelligence
    profile_resp = supabase_client.table("user_profiles").select("id, proficiency_level").eq("id", USER_ID).execute()
    if profile_resp.data:
        p = profile_resp.data[0]
        logger.info(f"✅ User Profile: Found ID {USER_ID[:8]}... (Level: {p['proficiency_level']})")
    else:
        logger.error(f"❌ User Profile: ID {USER_ID} not found. Run app.scripts.seed_user first.")

    # 3. Check Persona Calculation
    persona_resp = supabase_client.table("user_personas").select("persona_label, risk_score").eq("id", USER_ID).execute()
    if persona_resp.data:
        per = persona_resp.data[0]
        logger.info(f"✅ User Persona: Computed as '{per['persona_label']}' (Risk: {per['risk_score']})")
    else:
        logger.error("❌ User Persona: Not found.")

    # 4. Check Portfolio Normalization
    port_resp = supabase_client.table("portfolio_models").select("sector_weight_ranges").eq("user_id", USER_ID).execute()
    if port_resp.data:
        sectors = list(port_resp.data[0]['sector_weight_ranges'].keys())
        logger.info(f"✅ Portfolio Normalization: Mapped to {len(sectors)} sectors ({', '.join(sectors)})")
    else:
        logger.error("❌ Portfolio Model: Not found.")

    logger.info("---------------------------------------")

if __name__ == "__main__":
    asyncio.run(verify_system())
