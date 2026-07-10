import logging
import json
import os
import numpy as np
from typing import Dict, Any
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END


from app.config import settings

logger = logging.getLogger(__name__)

from config.gate_thresholds import GATE_THRESHOLDS
from app.schemas.tutor import TutorState
from app.tools.market_data import fetch_stock_news

# Initialize Ollama Embeddings using the dedicated local embedding model
embedder = OllamaEmbeddings(model="nomic-embed-text")

# Pre-defined category descriptions to serve as similarity centroids
CATEGORY_DESCRIPTIONS = {
    "definition": "Explain what a financial term, acronym, or metric means with a clear example.",
    "portfolio": "Evaluate personal risk, investment goals, asset allocation, or capital constraints.",
    "scenario": "Analyze what to do next, buy or sell triggers, price targets, and future market conditions.",
    "news": "Fetch recent events, market announcements, or news headlines about a specific stock.",
    "fallback": "General financial questions or ambiguous queries that do not fit other categories."
}

ROUTER_MODE = os.getenv("ROUTER_MODE", "enforce")



_CATEGORY_VECTORS = None

async def get_category_vectors() -> Dict[str, np.ndarray]:
    """Lazy-loads and caches centroid embeddings on first execution."""
    global _CATEGORY_VECTORS
    if _CATEGORY_VECTORS is None:
        logger.info("Pre-computing category embeddings for mathematical semantic router...")
        _CATEGORY_VECTORS = {}
        for k, v in CATEGORY_DESCRIPTIONS.items():
            embedding = await embedder.aembed_query(v)
            _CATEGORY_VECTORS[k] = np.array(embedding)
    return _CATEGORY_VECTORS

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Computes pure cosine similarity between two dimensional vectors."""
    return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)))

# --- 1. MATHEMATICAL SEMANTIC ROUTER (Phase 1 Blueprint Upgrade) ---
from opentelemetry import trace
async def semantic_router_node(state: TutorState) -> Dict[str, Any]:
    logger.info("Calculating semantic user intent via vector similarity...")
    
    last_msg = state["messages"][-1].content
    
    # 1. Generate embedding vector for the inbound message asynchronously
    query_vector = np.array(await embedder.aembed_query(last_msg))
    centroids = await get_category_vectors()
    
    # 2. Calculate distance metrics against centroids
    scores = {cat: cosine_similarity(query_vector, centroid) for cat, centroid in centroids.items()}
    best_match = max(scores, key=scores.get)
    best_score = scores[best_match]
    
    # 3. Apply configurable safety gate threshold
    routed_mode = best_match
    threshold = settings.ROUTER_CONFIDENCE_THRESHOLD
    if best_score <= threshold:
        if ROUTER_MODE == "log_only":
            logger.info("Semantic Router: Below confidence threshold (%.3f <= %.3f), but running in log_only mode. Keeping %s.", best_score, threshold, best_match)
        else:
            logger.info("Semantic Router: Below confidence threshold (%.3f <= %.3f). Falling back to 'fallback'.", best_score, threshold)
            routed_mode = "fallback"
    
    logger.info("Semantic Router resolution: '%s' (Confidence Score: %.3f)", routed_mode.upper(), best_score)
    
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute("router.category", routed_mode)
        span.set_attribute("router.confidence", best_score)
        
    return {"routed_mode": routed_mode}

# --- 2. TOOL EXECUTION NODE ---
async def news_tool_node(state: TutorState) -> TutorState:
    logger.info("Fetching live market news...")
    ticker = state["analysis_state"].get("ticker", "RELIANCE.NS")
    news_text = await fetch_stock_news(ticker)
    return {"tool_data": news_text}

def extract_relevant_state(analysis_state: Dict[str, Any], mode: str) -> str:
    """Extracts only the relevant parts of the analysis state based on routed mode to save tokens."""
    if not analysis_state:
        return "{}"
    
    if mode == "definition":
        return "{}"  # Minimal state needed for purely educational definitions
    
    extracted = {}
    extracted["ticker"] = analysis_state.get("ticker", "UNKNOWN")
    
    if mode == "portfolio":
        # Include risk, allocation, and current summary
        extracted["risk_warning"] = analysis_state.get("risk_warning")
        extracted["verdict"] = analysis_state.get("verdict")
    elif mode == "scenario":
        # Include triggers, technicals
        extracted["tutor_triggers"] = analysis_state.get("tutor_triggers")
        extracted["what_to_watch"] = analysis_state.get("what_to_watch")
        extracted["verdict"] = analysis_state.get("verdict")
    elif mode == "news":
        # Minimal context for news synthesis
        extracted["verdict"] = analysis_state.get("verdict")
        extracted["tutor_triggers"] = analysis_state.get("tutor_triggers")
    else: # fallback
        extracted["verdict"] = analysis_state.get("verdict")
        
    return json.dumps(extracted)

# --- 3. GENERATION NODE ---
async def generation_node(state: TutorState, config: RunnableConfig) -> TutorState:
    mode = state["routed_mode"]
    ticker = state["analysis_state"].get("ticker", "UNKNOWN")
    logger.info("Generating response via mode: %s", mode.upper())
    
    llm = ChatOllama(model="llama3.1", temperature=0.3) 
    
    analysis_state_str = extract_relevant_state(state.get('analysis_state', {}), mode)


    sys_instruction = f"""You are an elite quantitative financial tutor.
    User Profile: Level: {state['user_profile'].get('experience_level')}, Goal: {state['user_profile'].get('goal')}.
    
    CRITICAL DIRECTIVES:
    1. QUOTE-FIRST: When discussing the specific stock, anchor your answer using exact numbers from the Analysis State. 
    2. ANALOGY-MAPPING: Tailor analogies to the user's experience level.
    3. GRACEFUL FALLBACK: If the user asks to define a financial term, ALWAYS define it using a clear example.
    
    --- CURRENT ANALYSIS STATE ---
    {analysis_state_str}
    """
    
    if mode == "news" and state.get("tool_data"):
        sys_instruction += f"\n\n--- LATEST NEWS ---\n{state['tool_data']}"
        sys_instruction += "\nSynthesize the recent news with the current analysis state."
    elif mode == "definition":
        sys_instruction += "\nProvide a clear explanation of the requested term. Instead of repeating the overall stock verdict, use a brief, clear numeric example to show how the math works."
    elif mode == "portfolio":
        sys_instruction += "\nEvaluate the user's question explicitly against their existing portfolio allocations and stated goals. Reference historical trends if applicable."
    elif mode == "scenario":
        sys_instruction += "\nBreak down the 'what_to_watch' conditions. Explain the mechanics of the triggers and why they mathematically matter. Cross-reference past historical reasoning to highlight trend shifts."
        sys_instruction += f"\n\n--- STATIC GATE THRESHOLDS ---\n{json.dumps(GATE_THRESHOLDS, indent=2)}\nUse these static thresholds to explain why certain triggers are mathematically relevant."
    elif mode == "fallback":
        sys_instruction += "\nProvide a general educational overview. Do not give specific financial advice."

    chat_history = state["messages"][-10:]
    messages = [SystemMessage(content=sys_instruction)] + chat_history
    
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
    
    workflow.add_node("router", semantic_router_node)
    workflow.add_node("news_tool", news_tool_node)
    workflow.add_node("generate", generation_node)
    
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_edge)
    workflow.add_edge("news_tool", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()