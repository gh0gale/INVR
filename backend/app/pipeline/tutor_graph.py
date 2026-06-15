from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import Literal

from app.schemas.tutor import TutorState
from app.tools.market_data import fetch_stock_news

# --- 1. ROUTER CLASSIFICATION ---
class RouteDecision(BaseModel):
    mode: Literal["definition", "portfolio", "scenario", "news"] = Field(
        description="Classify user intent: 'definition' (jargon/terms), 'portfolio' (risk/goals/holdings), 'scenario' (what to watch/buy triggers), 'news' (recent events/updates)."
    )

def semantic_router_node(state: TutorState) -> TutorState:
    print("  [Tutor] Classifying user intent...")
    llm = ChatOllama(model="llama3.1", temperature=0.0)
    structured_llm = llm.with_structured_output(RouteDecision)
    
    last_msg = state["messages"][-1].content
    decision = structured_llm.invoke([
        SystemMessage(content="You are a routing supervisor. Classify the user's financial question into exactly one category based on intent."),
        HumanMessage(content=last_msg)
    ])
    
    return {"routed_mode": decision.mode}

# --- 2. TOOL EXECUTION NODE ---
async def news_tool_node(state: TutorState) -> TutorState:
    print("  [Tutor] Fetching live market news...")
    ticker = state["analysis_state"].get("ticker", "RELIANCE.NS")
    news_text = await fetch_stock_news(ticker)
    return {"tool_data": news_text}

# --- 3. GENERATION NODE (The Tutor Brain) ---
def generation_node(state: TutorState) -> TutorState:
    mode = state["routed_mode"]
    print(f"  [Tutor] Generating response via mode: {mode.upper()}...")
    
    llm = ChatOllama(model="llama3.1", temperature=0.3) # Slight temp for conversational variety
    
    # Base instructions enforcing Analogy and Quote-First directives
    sys_instruction = f"""You are an elite quantitative financial tutor.
    User Profile: Level: {state['user_profile'].get('experience_level')}, Goal: {state['user_profile'].get('goal')}.
    Portfolio Breakdown: {state['user_profile'].get('portfolio', 'No existing portfolio')}.
    
    CRITICAL DIRECTIVES:
    1. QUOTE-FIRST: You MUST anchor your answer using exact numbers from the provided Analysis State. 
    2. ANALOGY-MAPPING: Tailor analogies to the user's experience level.
    3. NO HALLUCINATIONS: If the user asks about a metric not in the Analysis State, say "I don't have that metric in the current analysis."
    
    --- CURRENT ANALYSIS STATE ---
    {state['analysis_state']}
    """
    
    # Inject tool data if we routed through news
    if mode == "news" and state.get("tool_data"):
        sys_instruction += f"\n\n--- LATEST NEWS ---\n{state['tool_data']}"
        sys_instruction += "\nSynthesize the recent news with the current analysis state."
        
    elif mode == "definition":
        sys_instruction += """
        \nProvide a clear explanation of the requested term. 
        Instead of repeating the overall stock verdict, use a brief, clear numeric example to show how the math works. 
        Then, contrast the metric's typical healthy level against the specific value found in this stock's Analysis State to show why it matters here.
        """
        
    elif mode == "portfolio":
        sys_instruction += "\nEvaluate the user's question explicitly against their existing portfolio allocations and stated goals."
        
    elif mode == "scenario":
        sys_instruction += "\nBreak down the 'what_to_watch' conditions. Explain the mechanics of the triggers and why they mathematically matter."

    # Trim memory to last 5 interactions (10 messages + 1 new system message)
    chat_history = state["messages"][-10:]
    messages = [SystemMessage(content=sys_instruction)] + chat_history
    
    response = llm.invoke(messages)
    return {"messages": [response]}

# --- 4. CONDITIONAL EDGE ---
def route_edge(state: TutorState) -> str:
    if state["routed_mode"] == "news":
        return "news_tool"
    return "generate"

# --- GRAPH COMPILATION ---
def build_tutor_graph():
    workflow = StateGraph(TutorState)
    
    workflow.add_node("router", semantic_router_node)
    workflow.add_node("news_tool", news_tool_node)
    workflow.add_node("generate", generation_node)
    
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_edge)
    workflow.add_edge("news_tool", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()