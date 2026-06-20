from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.schemas.api import PipelineRequest, PipelineResponse
from app.orchestrator import build_pipeline_graph

from app.services.ledger_service import log_prediction_to_ledger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Compile the LangGraph workflow once when the application boots
pipeline_graph = build_pipeline_graph()

@router.post("/process", response_model=PipelineResponse)
@limiter.limit("10/minute")
async def process_pipeline(request: Request, payload: PipelineRequest, background_tasks: BackgroundTasks):
    """
    Triggers the Medallion Data Pipeline and LangGraph orchestrator for a specific ticker.
    """
    # 1. Initialize your exact AnalysisState from the payload
    initial_state = {
        "ticker": payload.ticker.upper(),
        "timeframe": payload.timeframe.lower(),
        "user_profile": payload.user_profile.model_dump() if payload.user_profile else {},
        "bronze": None,
        "silver": None,
        "gold": None,
        "llm_output": None,
        "errors": []
    }

    # 2. Invoke the LangGraph Workflow asynchronously
    try:
        final_state = await pipeline_graph.ainvoke(initial_state, config={"recursion_limit": 10})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph Execution Failed: {str(e)}")

    # 3. Handle gracefully caught errors from your nodes
    if final_state.get("errors"):
        return PipelineResponse(
            success=False,
            ticker=payload.ticker,
            timeframe=payload.timeframe,
            verdict=None,
            llm_analysis=None,
            errors=final_state["errors"]
        )

    # --- 4. STAGE 8: HYBRID LEDGER LOGGING (Fire & Forget) ---
    if final_state.get("silver") and final_state.get("gold"):
        
        # Safely convert Pydantic models to dicts if they aren't already
        silver_data = final_state["silver"].model_dump() if hasattr(final_state["silver"], "model_dump") else final_state["silver"]
        gold_data = final_state["gold"].model_dump() if hasattr(final_state["gold"], "model_dump") else final_state["gold"]
        
        # Safely grab session_id (default to a system tag if called outside of a chat context)
        session_id = getattr(payload, "session_id", "analytics-api-execution")

        background_tasks.add_task(
            log_prediction_to_ledger,
            session_id,
            silver_data,
            gold_data
        )
    # 5. Extract Gold Verdict and the Local LLM Synthesizer output
    gold_verdict = final_state["gold"].verdict if hasattr(final_state.get("gold"), "verdict") else "UNKNOWN"

    return PipelineResponse(
        success=True,
        ticker=payload.ticker,
        timeframe=payload.timeframe,
        verdict=gold_verdict,
        llm_analysis=final_state.get("llm_output"),
        errors=None
    )