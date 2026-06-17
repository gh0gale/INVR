import os
import time
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# --- CONFIGURATION ---
# Adjust this URL if your router has a prefix (e.g., http://127.0.0.1:8000/api/v1/analytics/process)
API_URL = "http://127.0.0.1:8000/api/v1/analytics/process" 

# Load the exact same .env your backend uses
load_dotenv(override=True)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def run_end_to_end_test():
    print("\n🚀 Starting End-to-End Pipeline & Ledger Test...\n")

    # --- 1. PREPARE THE PAYLOAD ---
    session_id = "550e8400-e29b-41d4-a716-446655440000"
    payload = {
        "ticker": "RELIANCE.NS",
        "timeframe": "swing",
        "session_id": session_id,
        "user_profile": {
            "experience_level": "intermediate",
            "goal": "wealth_growth",
            "risk_tolerance": "moderate"
        }
    }

    # --- 2. FIRE API REQUEST ---
    print(f"📡 1. Sending POST request to {API_URL} for {payload['ticker']} ({payload['timeframe']})...")
    start_time = time.time()

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Could not connect to the server. Is Uvicorn running?")
        return
    except Exception as e:
        print(f"❌ API Call Failed: {response.text}")
        return

    elapsed_time = time.time() - start_time
    print(f"✅ API Response Received in {elapsed_time:.2f} seconds.")
    print(f"   - Success Flag: {data.get('success')}")
    print(f"   - Verdict: {data.get('verdict')}")
    print(f"   - LLM Output Snippet: {str(data.get('llm_analysis'))[:100]}...\n")

    # --- 3. WAIT FOR BACKGROUND TASKS ---
    print("⏳ Waiting 2.5 seconds for FastAPI background tasks to sync to Supabase...")
    time.sleep(2.5)

    # --- 4. VERIFY SUPABASE DATABASE ---
    print("\n🔍 2. Verifying Supabase Hybrid Ledger...")
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("⚠️ Supabase credentials not found in .env. Skipping database verification.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Step A: Check algorithmic_ledger (De-duplicated Math)
    print("   -> Checking 'algorithmic_ledger' table...")
    ledger_res = supabase.table("algorithmic_ledger") \
        .select("*") \
        .eq("ticker", "RELIANCE.NS") \
        .eq("timeframe", "swing") \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not ledger_res.data:
        print("   ❌ FAILED: No record found in algorithmic_ledger. Background task failed or RLS blocked it.")
        return

    latest_log = ledger_res.data[0]
    log_id = latest_log["log_id"]
    print(f"   ✅ SUCCESS: Found prediction log (ID: {log_id})")
    print(f"      - Pipeline Version: {latest_log['pipeline_version']}")
    
    # Verify JSONB storage worked
    silver_state = latest_log.get('silver_state', {})
    if 'current_price' in silver_state:
        print(f"      - Silver State Verified (Price logged: ₹{silver_state['current_price']})")
    else:
        print("      ⚠️ Silver State JSONB appears empty or malformed.")

    # Step B: Check prediction_interactions (User Behavior)
    print("\n   -> Checking 'prediction_interactions' table...")
    interaction_res = supabase.table("prediction_interactions") \
        .select("*") \
        .eq("log_id", log_id) \
        .eq("session_id", session_id) \
        .execute()

    if not interaction_res.data:
        print("   ❌ FAILED: No interaction trace found.")
        return

    print(f"   ✅ SUCCESS: Found interaction trace for session '{session_id}'. Action recorded as: '{interaction_res.data[0]['action_taken']}'")

    print("\n🎉 ALL TESTS PASSED! The Medallion Pipeline, LangGraph Router, and Hybrid Ledger are fully operational in a production configuration.")

if __name__ == "__main__":
    run_end_to_end_test()