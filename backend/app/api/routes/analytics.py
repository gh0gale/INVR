import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends 
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.schemas.api import PipelineRequest, PipelineResponse
from app.orchestrator import build_pipeline_graph
from app.services.ledger_service import log_prediction_to_ledger
from app.api.deps import get_current_user_id
from app.telemetry import wrap_background_task
from app.services.guardrail_service import check_input_safety

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
pipeline_graph = build_pipeline_graph()

@router.post("/process", response_model=PipelineResponse)
@limiter.limit("10/minute")
async def process_pipeline(request: Request, payload: PipelineRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user_id)):
    """
    Triggers the Medallion Data Pipeline and LangGraph orchestrator for a specific ticker.
    """
    # Guardrail Check - precise textual field checking to avoid false positives on numeric fields
    profile = payload.user_profile
    profile_text = f"Risk: {profile.risk_tolerance} | Exp: {profile.experience_level} | Goal: {profile.goal}" if profile else ""
    payload_str = f"Ticker: {payload.ticker} | Timeframe: {payload.timeframe} | Profile: {profile_text}"
    is_safe, rejection_message = await check_input_safety(payload_str)
    if not is_safe:
        raise HTTPException(status_code=400, detail=rejection_message)

    # 1. Initialize your exact AnalysisState from the payload
    initial_state = {
        "ticker": payload.ticker.upper(),
        "timeframe": payload.timeframe.lower(),
        "user_profile": payload.user_profile.model_dump() if payload.user_profile else {},
        "bronze": None,
        "silver": None,
        "gold": None,
        "llm_output": None,
        "errors": [],
        "retry_count": 0,
        "correction_note": None
    }

    # 2. Invoke the LangGraph Workflow asynchronously
    try:
        final_state = await pipeline_graph.ainvoke(initial_state, config={"recursion_limit": 25})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph Execution Failed: {str(e)}")

    # 3. Handle gracefully caught errors from your nodes
    if final_state.get("errors"):
        logger.error("Pipeline failed for %s: %s", payload.ticker, final_state["errors"])
        return PipelineResponse(
            success=False,
            ticker=payload.ticker,
            timeframe=payload.timeframe,
            verdict=None,
            llm_analysis=None,
            errors=final_state["errors"]
        )

    # 5. Extract Gold Verdict
    gold_state = final_state.get("gold")
    if gold_state is None:
        gold_verdict = "UNKNOWN"
    elif isinstance(gold_state, dict):
        gold_verdict = gold_state.get("verdict", "UNKNOWN")
    elif hasattr(gold_state, "verdict"):
        gold_verdict = gold_state.verdict
    else:
        gold_verdict = "UNKNOWN"

    # Extract LLM output safely
    llm_output = final_state.get("llm_output")
    if isinstance(llm_output, dict):
        pass  
    elif hasattr(llm_output, "model_dump"):
        llm_output = llm_output.model_dump()

    # --- 4. STAGE 8: HYBRID LEDGER LOGGING (Fire & Forget) ---
    if final_state.get("silver") and final_state.get("gold"):
        
        silver_data = final_state["silver"].model_dump() if hasattr(final_state["silver"], "model_dump") else final_state["silver"]
        gold_data = final_state["gold"].model_dump() if hasattr(final_state["gold"], "model_dump") else final_state["gold"]
        
        session_id = getattr(payload, "session_id", "analytics-api-execution")

        # Telemetry: Wrap the background task so the Trace ID survives the thread hop
        traced_ledger_task = wrap_background_task(log_prediction_to_ledger)

        background_tasks.add_task(
            traced_ledger_task,
            session_id,
            silver_data,
            gold_data,
            llm_output
        )

    return PipelineResponse(
        success=True,
        ticker=payload.ticker,
        timeframe=payload.timeframe,
        verdict=gold_verdict,
        llm_analysis=llm_output,
        errors=None
    )