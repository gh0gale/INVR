from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
import json

from app.schemas.tutor import ChatRequest
from app.pipeline.tutor_graph import build_tutor_graph

router = APIRouter(tags=["Tutor System"])
tutor_graph = build_tutor_graph()

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streams the tutor's response back to the client token-by-token."""
    
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "analysis_state": request.analysis_context,
        "user_profile": request.user_profile,
        "routed_mode": "",
        "tool_data": ""
    }

    async def event_generator():
        try:
            # astream_events allows us to listen to internal LangGraph/LLM tokens
            async for event in tutor_graph.astream_events(initial_state, version="v2"):
                # Filter specifically for the LLM generating text tokens
                if event["event"] == "on_chat_model_stream":
                    token = event["data"]["chunk"].content
                    if token:
                        # Yield standard SSE format
                        yield f"data: {json.dumps({'token': token})}\n\n"
                        
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")