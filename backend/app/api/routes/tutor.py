import json
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

from app.schemas.tutor import ChatRequest
from app.pipeline.tutor_graph import build_tutor_graph
from app.services.memory_service import manage_session_memory

router = APIRouter(tags=["Tutor System"])
limiter = Limiter(key_func=get_remote_address)
tutor_graph = build_tutor_graph()

@router.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, request_data: ChatRequest, background_tasks: BackgroundTasks):
    
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
            
            # Delegate DB operations entirely to the service layer
            test_user_id = "51928e80-ce4e-4846-9a40-f1fad08cb431" 
            
            background_tasks.add_task(
                manage_session_memory, 
                request_data.session_id, 
                test_user_id,
                request_data.message, 
                full_ai_response,
                topic_changed=False 
            )
            
        except Exception as e:
            logger.error("Streaming Error: %s", str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")