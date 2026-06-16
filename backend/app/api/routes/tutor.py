from fastapi import APIRouter
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
            # 1. Use stream_mode="messages" (The bulletproof way to stream in LangGraph)
            async for chunk, metadata in tutor_graph.astream(initial_state, stream_mode="messages"):
                
                # 2. Only yield chunks that are coming from the 'generate' node (ignore the router LLM)
                if metadata.get("langgraph_node") == "generate":
                    if chunk.content:
                        yield f"data: {json.dumps({'token': chunk.content})}\n\n"
                        
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"Streaming Error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")