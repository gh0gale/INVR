import json
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.schemas.tutor import ChatRequest
from app.pipeline.tutor_graph import build_tutor_graph
from app.services.memory_service import manage_session_memory

router = APIRouter(tags=["Tutor System"])
tutor_graph = build_tutor_graph()

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, background_tasks: BackgroundTasks):
    
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "analysis_state": request.analysis_context,
        "user_profile": request.user_profile,
        "routed_mode": "",
        "tool_data": ""
    }

    async def event_generator():
        full_ai_response = ""
        
        try:
            async for chunk, metadata in tutor_graph.astream(initial_state, stream_mode="messages"):
                if metadata.get("langgraph_node") == "generate":
                    if chunk.content:
                        full_ai_response += chunk.content
                        yield f"data: {json.dumps({'token': chunk.content})}\n\n"
                        
            yield "data: [DONE]\n\n"
            
            # Delegate DB operations entirely to the service layer
            test_user_id = "51928e80-ce4e-4846-9a40-f1fad08cb431" 
            
            background_tasks.add_task(
                manage_session_memory, 
                request.session_id, 
                test_user_id,
                request.message, 
                full_ai_response,
                topic_changed=False 
            )
            
        except Exception as e:
            print(f"Streaming Error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")