import asyncio
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# We use the Service Role key for seeding since it bypasses RLS
url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))

print(f"Connecting to Supabase at: {url}")
supabase: Client = create_client(url, key)

# --- DUMMY USER ID ---
# Replace this with your actual User ID from Supabase Auth if you have one.
# For now, we use a placeholder, but note that FK constraints might require a real user in auth.users.
TEST_USER_ID = "809d95fd-019e-46db-ae53-e4ee1b83ff03" 

async def seed_sector_benchmarks():
    """Seeds Indian Sector Benchmarks"""
    benchmarks = [
        {"sector_name": "Information Technology", "median_pe": 28.5, "median_pb": 7.2, "avg_roe": 22.0, "concentration_threshold": 30.0},
        {"sector_name": "Banking & Finance", "median_pe": 15.2, "median_pb": 2.1, "avg_roe": 14.5, "concentration_threshold": 35.0},
        {"sector_name": "Pharmaceuticals", "median_pe": 32.0, "median_pb": 4.5, "avg_roe": 16.0, "concentration_threshold": 20.0},
        {"sector_name": "FMCG", "median_pe": 55.0, "median_pb": 12.0, "avg_roe": 25.0, "concentration_threshold": 20.0},
        {"sector_name": "Automobile", "median_pe": 24.0, "median_pb": 4.0, "avg_roe": 18.0, "concentration_threshold": 25.0},
        {"sector_name": "Infrastructure", "median_pe": 22.0, "median_pb": 3.0, "avg_roe": 12.0, "concentration_threshold": 20.0},
        {"sector_name": "Energy", "median_pe": 12.5, "median_pb": 1.8, "avg_roe": 15.0, "concentration_threshold": 15.0},
    ]
    try:
        supabase.table("sector_benchmarks").upsert(benchmarks).execute()
        print(f"Seeded {len(benchmarks)} Sector Benchmarks.")
    except Exception as e:
        print(f"Error seeding sector benchmarks: {e}")

async def seed_macro_context():
    """Seeds current Indian Macro Context"""
    macro = {
        "id": 1,
        "rbi_repo_rate": 6.50,
        "india_10y_bond_yield": 7.15,
        "nifty_50_pe": 22.4,
        "india_vix": 14.2,
        "cpi_inflation": 5.1,
        "fii_dii_net": "neutral"
    }
    try:
        supabase.table("macro_context").upsert(macro).execute()
        print("Seeded Macro Context.")
    except Exception as e:
        print(f"Error seeding macro context: {e}")

async def seed_test_user():
    """Seeds a Sample User Profile and Persona"""
    # 1. User Profile
    profile = {
        "id": TEST_USER_ID,
        "age": 30,
        "income_bracket": "10L-25L",
        "monthly_investable": 50000.0,
        "risk_appetite": "moderate",
        "investment_horizon_months": 60,
        "primary_goal": "wealth_creation",
        "proficiency_level": "intermediate"
    }

    # 2. User Persona (Computed logic)
    persona = {
        "id": TEST_USER_ID,
        "risk_score": 65.0,
        "persona_label": "Balanced Growth Seeker",
        "preferred_sectors": ["Information Technology", "Banking & Finance"],
        "scoring_weight_profile": {
            "fundamental": 0.40,
            "valuation": 0.30,
            "technical": 0.15,
            "quantitative": 0.10,
            "sentiment": 0.05
        }
    }

    try:
        # Note: If this fails, go to Supabase Dashboard and create a user in Auth 
        # then paste their ID into TEST_USER_ID above.
        supabase.table("user_profiles").upsert(profile).execute()
        supabase.table("user_personas").upsert(persona).execute()
        print("Seeded Test User Profile & Persona.")
    except Exception as e:
        print(f"Error seeding test user (check if UUID is valid in Auth): {e}")

async def main():
    print("Beginning Database Seed...")
    await seed_sector_benchmarks()
    await seed_macro_context()
    await seed_test_user()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
