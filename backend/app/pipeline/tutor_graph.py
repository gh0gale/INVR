from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import Literal

from app.schemas.tutor import TutorState
from app.tools.market_data import fetch_stock_news

# --- 1. ROUTER CLASSIFICATION (Converted to Async) ---
class RouteDecision(BaseModel):
    mode: Literal["definition", "portfolio", "scenario", "news"] = Field(
        description="Classify user intent: 'definition' (jargon/terms), 'portfolio' (risk/goals/holdings), 'scenario' (what to watch/buy triggers), 'news' (recent events/updates)."
    )

async def semantic_router_node(state: TutorState) -> TutorState:
    print("  [Tutor] Classifying user intent...")
    # Initialize LLM with zero temperature for deterministic routing
    llm = ChatOllama(model="llama3.1", temperature=0.0)
    structured_llm = llm.with_structured_output(RouteDecision)
    
    last_msg = state["messages"][-1].content
    
    decision = await structured_llm.ainvoke([
        SystemMessage(content="""You are a routing supervisor. Classify the user's intent. 
        CRITICAL ROUTING RULES:
        - 'definition': ALWAYS use this if the user asks what a term, acronym, or metric means (e.g., 'What is CAGR?', 'Explain SMA').
        - 'portfolio': Use if they ask about their personal risk, goals, or capital.
        - 'scenario': Use if they ask what to do next, when to buy/sell, or future triggers.
        - 'news': Use if they ask for recent events or updates."""),
        HumanMessage(content=last_msg)
    ])
    
    return {"routed_mode": decision.mode}

# --- 2. TOOL EXECUTION NODE (Already Async) ---
async def news_tool_node(state: TutorState) -> TutorState:
    print("  [Tutor] Fetching live market news...")
    ticker = state["analysis_state"].get("ticker", "RELIANCE.NS")
    news_text = await fetch_stock_news(ticker)
    return {"tool_data": news_text}

# --- 3. GENERATION NODE (Fully Optimized Async) ---
async def generation_node(state: TutorState, config: RunnableConfig) -> TutorState:
    mode = state["routed_mode"]
    print(f"  [Tutor] Generating response via mode: {mode.upper()}...")
    
    llm = ChatOllama(model="llama3.1", temperature=0.3) 
    
    import json
    analysis_state_str = json.dumps(state.get('analysis_state', {}))
    if len(analysis_state_str) > 2000:
        analysis_state_str = analysis_state_str[:1997] + "..."

    sys_instruction = f"""You are an elite quantitative financial tutor.
    User Profile: Level: {state['user_profile'].get('experience_level')}, Goal: {state['user_profile'].get('goal')}.
    
    CRITICAL DIRECTIVES:
    1. QUOTE-FIRST: When discussing the specific stock, anchor your answer using exact numbers from the Analysis State. 
    2. ANALOGY-MAPPING: Tailor analogies to the user's experience level.
    3. GRACEFUL FALLBACK: If the user asks to define a financial term, ALWAYS define it using a clear example. If the exact value for that metric is NOT in the Analysis State, provide the definition, but clarify: "This specific metric is not actively highlighted in the current analysis for this stock." Do not refuse to explain a concept.
    
    --- CURRENT ANALYSIS STATE ---
    {analysis_state_str}
    """
    
    if mode == "news" and state.get("tool_data"):
        sys_instruction += f"\n\n--- LATEST NEWS ---\n{state['tool_data']}"
        sys_instruction += "\nSynthesize the recent news with the current analysis state."
    elif mode == "definition":
        sys_instruction += "\nProvide a clear explanation of the requested term. Instead of repeating the overall stock verdict, use a brief, clear numeric example to show how the math works."
    elif mode == "portfolio":
        sys_instruction += "\nEvaluate the user's question explicitly against their existing portfolio allocations and stated goals."
    elif mode == "scenario":
        sys_instruction += "\nBreak down the 'what_to_watch' conditions. Explain the mechanics of the triggers and why they mathematically matter."

    chat_history = state["messages"][-10:]
    messages = [SystemMessage(content=sys_instruction)] + chat_history
    
    # 3. CRITICAL: Pass the 'config' to .ainvoke()
    # This automatically unlocks token-by-token streaming back to your FastAPI route!
    response = await llm.ainvoke(messages, config)
    
    return {"messages": [response]}

# --- 4. CONDITIONAL EDGE ---
def route_edge(state: TutorState) -> str:
    if state["routed_mode"] == "news":
        return "news_tool"
    return "generate"

# --- GRAPH COMPILATION ---
def build_tutor_graph():
    workflow = StateGraph(TutorState)
    
    # Add nodes natively
    workflow.add_node("router", semantic_router_node)
    workflow.add_node("news_tool", news_tool_node)
    workflow.add_node("generate", generation_node)
    
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_edge)
    workflow.add_edge("news_tool", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()