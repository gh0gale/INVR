import asyncio
import json
import os
import sys
import httpx
from dotenv import load_dotenv

# Ensure the backend directory is in python search path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load environment variables (.env contains Supabase credentials)
load_dotenv()

from app.database import supabase_admin
from app.schemas.profile import UserProfileRequest
from app.services.profile_service import create_and_store_profile

async def run_e2e_test(query: str, ticker: str, timeframe: str):
    # We will use the test user ID linked to 'testuser@example.com' in the auth.users table
    test_user_id = "51928e80-ce4e-4846-9a40-f1fad08cb431"
    
    print("\n" + "=" * 80)
    print(f"STEP 1: PREPARING USER PROFILE IN DATABASE FOR USER: {test_user_id}")
    print("=" * 80)
    
    # 1. Define a profile that matches the UserProfileRequest schema.
    # Note that portfolio weights must sum to 1.0 (e.g. 0.5 + 0.3 + 0.2 = 1.0)
    profile_data = {
        "experience": "intermediate",
        "goal": "wealth_growth",
        "timeframe": timeframe,
        "risk": "moderate",
        "portfolio": {
            "large_cap": 0.5,
            "mid_cap": 0.3,
            "fixed_income": 0.2
        },
        "capital": 250000.0
    }
    
    try:
        # Validate data with Pydantic schema
        profile_payload = UserProfileRequest(**profile_data)
        
        # Persist the profile directly to the database via the profile service layer
        print(f"Persisting profile to database...")
        profile_res = create_and_store_profile(user_id=test_user_id, payload=profile_payload)
        print(f"Successfully stored profile. Version Hash: {profile_res.profile_version_hash}")
    except Exception as e:
        print(f"Failed to prepare profile in DB: {e}")
        return

    # 2. Retrieve the user profile back from the DB (demonstrates DB read)
    print("\n" + "=" * 80)
    print("STEP 2: READING RETRIEVED USER PROFILE FROM DATABASE")
    print("=" * 80)
    try:
        db_res = supabase_admin.table("user_profiles").select("*").eq("id", test_user_id).execute()
        if not db_res.data:
            print("Error: User profile not found in database.")
            return
        db_profile = db_res.data[0]
        print("Successfully read user profile from database:")
        print(json.dumps(db_profile, indent=2))
    except Exception as e:
        print(f"Failed to read from DB: {e}")
        return

    # 3. Call the Analytics Pipeline endpoint to get the Tear Sheet (Bronze -> Silver -> Gold -> Platinum LLM)
    print("\n" + "=" * 80)
    print(f"STEP 3: RUNNING QUANT MEDALLION PIPELINE FOR {ticker} ({timeframe})")
    print("=" * 80)
    
    # Map database profile to the format expected by the /analytics/process endpoint
    analytics_profile = {
        "risk_tolerance": db_profile["risk"],
        "experience_level": db_profile["experience"],
        "goal": db_profile["goal"],
        "available_capital": db_profile["capital"]
    }
    
    analytics_url = "http://127.0.0.1:8000/api/v1/analytics/process"
    analytics_payload = {
        "ticker": ticker,
        "timeframe": timeframe,
        "user_profile": analytics_profile
    }
    
    print(f"Sending POST request to: {analytics_url}")
    # 60s timeout to allow local LLM generation & data scraping
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(analytics_url, json=analytics_payload)
            if response.status_code != 200:
                print(f"Analytics endpoint error (Status {response.status_code}): {response.text}")
                return
                
            analytics_res = response.json()
            if not analytics_res.get("success"):
                print(f"Analytics pipeline execution failed: {analytics_res.get('errors')}")
                return
                
            print("Analytics pipeline completed successfully!")
            print(f"Verdict: {analytics_res.get('verdict')}")
            print(f"Synthesizer output keys: {list(analytics_res.get('llm_analysis', {}).keys())}")
        except Exception as e:
            print(f"Analytics API request failed: {e}")
            return

    # 4. Request a stream response from the Tutor using the real DB profile and pipeline output
    print("\n" + "=" * 80)
    print("STEP 4: STREAMING RESPONSE FROM THE TUTOR")
    print("=" * 80)
    
    # Structure the analysis context matching the tutor input schemas
    analysis_context = {
        "ticker": analytics_res["ticker"],
        "timeframe": analytics_res["timeframe"],
        "verdict": analytics_res["verdict"],
        "llm_analysis": analytics_res["llm_analysis"]
    }
    
    # Map the DB profile to the schema expected by the tutor graph
    tutor_user_profile = {
        "experience_level": db_profile["experience"],
        "goal": db_profile["goal"],
        "risk_tolerance": db_profile["risk"],
        "portfolio": db_profile["portfolio"],
        "capital": db_profile["capital"]
    }
    
    tutor_url = "http://127.0.0.1:8000/api/v1/tutor/chat/stream"
    tutor_payload = {
        "message": query,
        "session_id": f"e2e_session_{ticker}_{timeframe}",
        "analysis_context": analysis_context,
        "user_profile": tutor_user_profile
    }
    
    print(f"\n[User]: {query}")
    print("[Tutor]: ", end="", flush=True)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream("POST", tutor_url, json=tutor_payload) as stream_response:
                if stream_response.status_code != 200:
                    print(f"\nError: Tutor stream returned status code {stream_response.status_code}")
                    return
                    
                async for line in stream_response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        
                        if data_str == "[DONE]":
                            print("\n\n--- Stream Completed ---")
                            break
                            
                        try:
                            data_json = json.loads(data_str)
                            if "token" in data_json:
                                print(data_json["token"], end="", flush=True)
                            elif "error" in data_json:
                                print(f"\n[Backend Error]: {data_json['error']}")
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"\nHTTP error during stream response: {e}")

if __name__ == "__main__":
    # Test cases representing actual live operations:
    # 1. We test Mode 4 / News Trigger on Reliance (requires fetching fresh data and compiling it)
    asyncio.run(run_e2e_test(
        query="Is there any recent news on Reliance that impacts this layout?",
        ticker="RELIANCE.NS",
        timeframe="long_term"
    ))
