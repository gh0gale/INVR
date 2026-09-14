import json
from fastapi import APIRouter, BackgroundTasks, Request, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
import logging

from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
from app.schemas.tutor import ChatRequest
from app.pipeline.tutor_graph import build_tutor_graph
from app.services.memory_service import load_working_memory, manage_session_memory
from app.services.guardrail_service import check_input_safety
from app.api.deps import get_current_user_id
from app.telemetry import wrap_background_task
from app.rate_limit import limiter
from app.llm import message_text

router = APIRouter(tags=["Tutor System"])
tutor_graph = build_tutor_graph()

# Nodes whose messages reach the client: the generated answer, and the scope
# gate's fixed refusal (audit OBS-02), which is a node output, not a model call.
STREAMED_NODES = {"generate", "refuse"}

@router.post("/chat/stream")
@limiter.limit("30/minute")
async def chat_stream(request: Request, request_data: ChatRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user_id)):
    
    # ==========================================
    # PHASE 1: DETERMINISTIC INBOUND GUARDRAIL
    # ==========================================
    is_safe, rejection_message = await check_input_safety(request_data.message)
    
    if not is_safe:
        logger.warning("Guardrail blocked prompt injection attempt from user %s", user_id)
        
        async def short_circuit_stream():
            yield f"data: {json.dumps({'token': rejection_message})}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingResponse(short_circuit_stream(), media_type="text/event-stream")

    # ==========================================
    # NORMAL EXECUTION LAYER
    # ==========================================
    # Prior turns for this session. Without this the tutor answered every
    # question cold, because working_memory was written but never read back
    # (audit finding NEW-LLM-01). Trimmed to a token budget rather than a
    # message count, so ten long turns cannot overflow the window.
    history = await load_working_memory(request_data.session_id)
    prior = [
        HumanMessage(content=m["content"]) if m["role"] == "human"
        else AIMessage(content=m["content"])
        for m in history
    ]

    initial_state = {
        "messages": [*prior, HumanMessage(content=request_data.message)],
        "analysis_state": request_data.analysis_context,
        "user_profile": request_data.user_profile,
        "routed_mode": "",
        "tool_data": ""
    }

    async def event_generator():
        with tracer.start_as_current_span("api_chat_stream") as span:
            span.set_attribute("user_id", user_id)
            
            full_ai_response = ""
            
            try:
                async for chunk, metadata in tutor_graph.astream(initial_state, stream_mode="messages", config={"recursion_limit": 25}):
                    if metadata.get("langgraph_node") in STREAMED_NODES:
                        # message_text, not .content: Gemini streams a list of
                        # parts, which json.dumps would send as an array.
                        token = message_text(chunk)
                        if token:
                            full_ai_response += token
                            yield f"data: {json.dumps({'token': token})}\n\n"
                            
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
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                logger.error("Streaming Error: %s", str(e))
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")