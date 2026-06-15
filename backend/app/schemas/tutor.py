from pydantic import BaseModel, Field
from typing import Annotated, TypedDict, Dict, Any, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class TutorState(TypedDict):
    # add_messages automatically appends new messages to the history list
    messages: Annotated[List[BaseMessage], add_messages]
    analysis_state: Dict[str, Any]  # The Phase 2 JSON Tear Sheet
    user_profile: Dict[str, Any]    # Risk, Goal, Experience, Portfolio
    routed_mode: str                # definition | portfolio | scenario | tool
    tool_data: Optional[str]        # Holds scraped data (like news)

class ChatRequest(BaseModel):
    message: str
    session_id: str
    # The frontend will pass the Phase 2 analysis state here so the Tutor has context
    analysis_context: Dict[str, Any] = Field(..., description="The JSON output from the Quantitative Engine")
    user_profile: Dict[str, Any] = Field(default_factory=dict)