from datetime import datetime
import logging
from app.database import supabase_admin as supabase

logger = logging.getLogger(__name__)

# Set your current algorithm version here. 
# Update this whenever you change gate thresholds!
PIPELINE_VERSION = "v1.0.0"

async def log_prediction_to_ledger(session_id: str, silver_metrics: dict, verdict_draft: dict, llm_output: dict = None):
    """
    Handles the Hybrid Ledger logic: 
    1. Checks if the exact prediction exists today.
    2. Writes it if it doesn't.
    3. Attaches the user interaction trace.
    """
    if not supabase:
        logger.warning("Supabase not configured. Skipping log.")
        return

    ticker = verdict_draft.get("ticker")
    timeframe = verdict_draft.get("timeframe")
    today_date = datetime.utcnow().date().isoformat()

    # Safely embed the LLM output into the gold_verdict payload so it persists
    if llm_output:
        verdict_draft["llm_analysis"] = llm_output

    logger.info("Syncing %s prediction for %s (v%s)...", timeframe.upper(), ticker, PIPELINE_VERSION)

    try:
        # 1. THE DE-DUPLICATION CHECK
        # Does this exact prediction already exist today?
        existing_log = supabase.table("algorithmic_ledger").select("log_id").eq("ticker", ticker).eq("timeframe", timeframe).eq("date", today_date).eq("pipeline_version", PIPELINE_VERSION).execute()

        if existing_log.data:
            # It exists! Just grab the ID.
            log_id = existing_log.data[0]["log_id"]
            logger.info("Prediction already exists today. Bypassing duplicate math log.")
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
            logger.info("New algorithmic prediction written.")

        # 2. THE INTERACTION TRACE
        # Now, track that this specific user session viewed this prediction.
        interaction_entry = {
            "log_id": log_id,
            "session_id": session_id,
            "action_taken": "viewed"
        }
        supabase.table("prediction_interactions").insert(interaction_entry).execute()
        logger.info("User interaction ('viewed') logged for session %s.", session_id)

    except Exception as e:
        logger.error("Failed to sync ledger: %s", str(e))