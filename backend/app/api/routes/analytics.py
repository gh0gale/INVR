from fastapi import APIRouter, HTTPException
from app.schemas.api import PipelineRequest, PipelineResponse
from app.orchestrator import build_pipeline_graph

router = APIRouter()

# Compile the LangGraph workflow once when the application boots
pipeline_graph = build_pipeline_graph()

@router.post("/process", response_model=PipelineResponse)
async def process_pipeline(payload: PipelineRequest):
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
        final_state = await pipeline_graph.ainvoke(initial_state)
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

    # 4. Extract Gold Verdict and the Local LLM Synthesizer output
    gold_verdict = final_state["gold"].verdict if final_state.get("gold") else "UNKNOWN"

    return PipelineResponse(
        success=True,
        ticker=payload.ticker,
        timeframe=payload.timeframe,
        verdict=gold_verdict,
        llm_analysis=final_state.get("llm_output"),
        errors=None
    )