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

async def seed_sector_benchmarks():
    """
    Seeds Indian Sector Benchmarks (Approximations for dev)
    """
    benchmarks = [
        {"sector_name": "Information Technology", "median_pe": 28.5, "median_pb": 7.2, "avg_roe": 22.0, "concentration_threshold": 30.0},
        {"sector_name": "Banking & Finance", "median_pe": 15.2, "median_pb": 2.1, "avg_roe": 14.5, "concentration_threshold": 35.0},
        {"sector_name": "Pharmaceuticals", "median_pe": 32.0, "median_pb": 4.5, "avg_roe": 16.0, "concentration_threshold": 20.0},
        {"sector_name": "FMCG", "median_pe": 55.0, "median_pb": 12.0, "avg_roe": 25.0, "concentration_threshold": 20.0},
        {"sector_name": "Automobile", "median_pe": 24.0, "median_pb": 4.0, "avg_roe": 18.0, "concentration_threshold": 25.0},
        {"sector_name": "Infrastructure", "median_pe": 22.0, "median_pb": 3.0, "avg_roe": 12.0, "concentration_threshold": 20.0},
    ]

    try:
        response = supabase.table("sector_benchmarks").upsert(benchmarks).execute()
        print(f"✅ Seeded {len(response.data)} Sector Benchmarks.")
    except Exception as e:
        print(f"❌ Error seeding sector benchmarks: {e}")

async def seed_macro_context():
    """
    Seeds current Indian Macro Context (Static baseline for dev)
    """
    macro = {
        "id": 1,
        "rbi_repo_rate": 6.50,
        "india_10y_bond_yield": 7.15,
        "nifty_50_pe": 22.4,
        "india_vix": 14.2,
        "cpi_inflation": 5.1
    }

    try:
        response = supabase.table("macro_context").upsert(macro).execute()
        print("✅ Seeded Macro Context.")
    except Exception as e:
        print(f"❌ Error seeding macro context: {e}")

async def main():
    print("Beginning Database Seed...")
    await seed_sector_benchmarks()
    await seed_macro_context()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
