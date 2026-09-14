import asyncio
from datetime import datetime
from typing import Optional
import hashlib
import json
import logging
from opentelemetry import trace
from app.database import supabase_admin as supabase
from config.gate_thresholds import GATE_THRESHOLDS

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

"""
Ledger version.

This string is part of the de-duplication key (ticker, timeframe, date,
version), and the Engine Room groups wins and losses by it. Bumping it by hand
was the plan; in practice it sat at v1.0.0 across a threshold change and two
prompt rewrites, so predictions made under different rules were graded as one
cohort (audit finding NEW-BE-06).

The ruleset half is therefore derived, not remembered: any edit to
GATE_THRESHOLDS produces a new fingerprint automatically. Bump RULESET_VERSION
by hand only for logic changes that thresholds cannot express, such as adding a
gate or changing an override.
"""
# v1.2.0 (2026-09-13): gates no longer score absent data. The circuit gate is
# skipped when NSE gives no band, relative strength and the regime override
# run against a fresh benchmark, and missing fundamentals are None instead of
# 0 / 25.0 (audit DATA-01..03). Verdicts before and after are not comparable.
# v1.2.1 (2026-09-13): debt/equity is converted from yfinance's percentage at
# the source. Under v1.2.0 low-debt companies (D/E 1.5-10%) were flagged as
# 1.5-10x leveraged (audit DATA-04), so those rows are a separate cohort.
RULESET_VERSION = "v1.2.1"

_THRESHOLD_FINGERPRINT = hashlib.sha256(
    json.dumps(GATE_THRESHOLDS, sort_keys=True).encode("utf-8")
).hexdigest()[:8]

PIPELINE_VERSION = f"{RULESET_VERSION}-{_THRESHOLD_FINGERPRINT}"

async def log_prediction_to_ledger(session_id: str, silver_metrics: dict, verdict_draft: dict, llm_output: dict = None, user_id: str = None) -> Optional[str]:
    """
    Handles the Hybrid Ledger logic:
    1. Checks if the exact prediction exists today.
    2. Writes it if it doesn't.
    3. Attaches the user interaction trace.

    Returns the ledger row's log_id, or None if it could not be written. The
    analytics route awaits this before responding (audit MU-04), so the
    Supabase client's blocking calls run in a worker thread rather than
    stalling every other request on the event loop. `asyncio.to_thread` copies
    the context, so the request's trace id still lands on the row.

    `user_id` is what makes the interaction row attributable. The ledger row
    itself stays shared and user-agnostic on purpose: it is deduplicated on
    (ticker, timeframe, date, pipeline_version) so one deterministic verdict is
    stored once and graded once. Ownership lives on the interaction, which is
    how the workspace scopes a user's history (audit finding ISO-01).
    """
    return await asyncio.to_thread(
        _write_prediction, session_id, silver_metrics, verdict_draft, llm_output, user_id
    )


def _write_prediction(session_id: str, silver_metrics: dict, verdict_draft: dict, llm_output: dict = None, user_id: str = None) -> Optional[str]:
    ticker = verdict_draft.get("ticker", "UNKNOWN")
    timeframe = verdict_draft.get("timeframe", "UNKNOWN")

    # Wrap the entire task in a manual telemetry span
    with tracer.start_as_current_span("log_prediction_to_ledger", attributes={"ticker": ticker, "timeframe": timeframe}) as span:
        
        if not supabase:
            msg = "Supabase not configured. Skipping log."
            logger.warning(msg)
            span.add_event(msg)
            return None

        log_id = None
        today_date = datetime.utcnow().date().isoformat()

        # Safely embed the LLM output into the gold_verdict payload so it persists
        if llm_output:
            verdict_draft["llm_analysis"] = llm_output

        logger.info("Syncing %s prediction for %s (v%s)...", timeframe.upper(), ticker, PIPELINE_VERSION)

        try:
            # 1. THE DE-DUPLICATION CHECK
            existing_log = supabase.table("algorithmic_ledger").select("log_id").eq("ticker", ticker).eq("timeframe", timeframe).eq("date", today_date).eq("pipeline_version", PIPELINE_VERSION).execute()

            if existing_log.data:
                log_id = existing_log.data[0]["log_id"]
                logger.info("Prediction already exists today. Bypassing duplicate math log.")
                span.add_event("Duplicate found. Bypassing insert.")
            
            else:
                span_context = trace.get_current_span().get_span_context()
                trace_id = format(span_context.trace_id, '032x') if span_context.is_valid else None

                new_ledger_entry = {
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "date": today_date,
                    "pipeline_version": PIPELINE_VERSION,
                    "silver_state": silver_metrics,
                    "gold_verdict": verdict_draft,
                    "trace_id": trace_id
                }
                # 1. Standard Relational Insert
                insert_res = supabase.table("algorithmic_ledger").insert(new_ledger_entry).execute()
                log_id = insert_res.data[0]["log_id"]
                logger.info("New algorithmic prediction written.")
                span.add_event("New ledger entry written.")
                


            # 2. THE INTERACTION TRACE
            interaction_entry = {
                "log_id": log_id,
                "session_id": session_id,
                "action_taken": "viewed",
                "user_id": user_id,
            }
            supabase.table("prediction_interactions").insert(interaction_entry).execute()
            logger.info("User interaction ('viewed') logged for session %s.", session_id)
            span.add_event("Interaction logged.")

        except Exception as e:
            # Inject errors directly into the Trace UI
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            logger.error("Failed to sync ledger: %s", str(e))

        # Set as soon as the ledger row exists, so a failure on the interaction
        # insert still hands back the row the verdict was recorded under.
        return log_id