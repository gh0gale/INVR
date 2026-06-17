import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(override=True)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
else:
    supabase = None

# Set your current algorithm version here. 
# Update this whenever you change gate thresholds!
PIPELINE_VERSION = "v1.0.0"

async def log_prediction_to_ledger(session_id: str, silver_metrics: dict, verdict_draft: dict):
    """
    Handles the Hybrid Ledger logic: 
    1. Checks if the exact prediction exists today.
    2. Writes it if it doesn't.
    3. Attaches the user interaction trace.
    """
    if not supabase:
        print("  [Ledger] Supabase not configured. Skipping log.")
        return

    ticker = verdict_draft.get("ticker")
    timeframe = verdict_draft.get("timeframe")
    today_date = datetime.utcnow().date().isoformat()

    print(f"  [Ledger] Syncing {timeframe.upper()} prediction for {ticker} (v{PIPELINE_VERSION})...")

    try:
        # 1. THE DE-DUPLICATION CHECK
        # Does this exact prediction already exist today?
        existing_log = supabase.table("algorithmic_ledger").select("log_id").eq("ticker", ticker).eq("timeframe", timeframe).eq("date", today_date).eq("pipeline_version", PIPELINE_VERSION).execute()

        if existing_log.data:
            # It exists! Just grab the ID.
            log_id = existing_log.data[0]["log_id"]
            print("  [Ledger] Prediction already exists today. Bypassing duplicate math log.")
        else:
            # It's new! Write the heavy JSON data.
            new_ledger_entry = {
                "ticker": ticker,
                "timeframe": timeframe,
                "date": today_date,
                "pipeline_version": PIPELINE_VERSION,
                "silver_state": silver_metrics,
                "gold_verdict": verdict_draft
            }
            insert_res = supabase.table("algorithmic_ledger").insert(new_ledger_entry).execute()
            log_id = insert_res.data[0]["log_id"]
            print("  [Ledger] New algorithmic prediction written.")

        # 2. THE INTERACTION TRACE
        # Now, track that this specific user session viewed this prediction.
        interaction_entry = {
            "log_id": log_id,
            "session_id": session_id,
            "action_taken": "viewed"
        }
        supabase.table("prediction_interactions").insert(interaction_entry).execute()
        print(f"  [Ledger] User interaction ('viewed') logged for session {session_id}.")

    except Exception as e:
        print(f"  [Ledger ERROR] Failed to sync ledger: {str(e)}")