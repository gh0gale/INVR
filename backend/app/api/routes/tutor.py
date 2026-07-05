import json
from fastapi import APIRouter, BackgroundTasks, Request, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

from app.schemas.tutor import ChatRequest
from app.pipeline.tutor_graph import build_tutor_graph
from app.services.memory_service import manage_session_memory
from app.services.guardrail_service import check_input_safety
from app.api.deps import get_current_user_id
from app.telemetry import wrap_background_task

router = APIRouter(tags=["Tutor System"])
limiter = Limiter(key_func=get_remote_address)
tutor_graph = build_tutor_graph()

@router.post("/chat/stream")
@limiter.limit("30/minute")
async def chat_stream(request: Request, request_data: ChatRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user_id)):
    
    # ==========================================
    # PHASE 1: DETERMINISTIC INBOUND GUARDRAIL
    # ==========================================
    is_safe, rejection_message = check_input_safety(request_data.message)
    
    if not is_safe:
        logger.warning("Guardrail blocked prompt injection attempt from user %s", user_id)
        
        async def short_circuit_stream():
            yield f"data: {json.dumps({'token': rejection_message})}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingResponse(short_circuit_stream(), media_type="text/event-stream")

    # ==========================================
    # NORMAL EXECUTION LAYER
    # ==========================================
    initial_state = {
        "messages": [HumanMessage(content=request_data.message)],
        "analysis_state": request_data.analysis_context,
        "user_profile": request_data.user_profile,
        "routed_mode": "",
        "tool_data": ""
    }

    async def event_generator():
        full_ai_response = ""
        
        try:
            async for chunk, metadata in tutor_graph.astream(initial_state, stream_mode="messages", config={"recursion_limit": 10}):
                if metadata.get("langgraph_node") == "generate":
                    if chunk.content:
                        full_ai_response += chunk.content
                        yield f"data: {json.dumps({'token': chunk.content})}\n\n"
                        
            yield "data: [DONE]\n\n"
            
            # Telemetry: Wrap memory service background execution context
            traced_memory_task = wrap_background_task(manage_session_memory)
            
            background_tasks.add_task(
                traced_memory_task, 
                request_data.session_id, 
                user_id,
                request_data.message, 
                full_ai_response,
                False 
            )
            
        except Exception as e:
            logger.error("Streaming Error: %s", str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")