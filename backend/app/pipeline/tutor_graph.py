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
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

from config.gate_thresholds import GATE_THRESHOLDS
from app.schemas.tutor import TutorState
from app.prompts import TUTOR_MAX_TOKENS, TUTOR_PROMPT_VERSION
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
    
    with tracer.start_as_current_span("semantic_router_node") as span:
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
        
        span.set_attribute("router.category", routed_mode)
        span.set_attribute("router.confidence", best_score)
            
        return {"routed_mode": routed_mode}

# --- 2. TOOL EXECUTION NODE ---
async def news_tool_node(state: TutorState) -> TutorState:
    with tracer.start_as_current_span("news_tool_node"):
        logger.info("Fetching live market news...")
        ticker = (state.get("analysis_state") or {}).get("ticker")
        if not ticker:
            # Falling back to some other company's news would be worse than
            # saying nothing, so say nothing.
            return {"tool_data": "No ticker is loaded, so no news was fetched."}
        news_text = await fetch_stock_news(ticker)
        return {"tool_data": news_text}

def extract_relevant_state(analysis_state: Dict[str, Any], mode: str) -> str:
    """Extracts only the relevant parts of the analysis state based on routed mode to save tokens."""
    if not analysis_state:
        return "{}"
    
    extracted = {}
    extracted["ticker"] = analysis_state.get("ticker", "UNKNOWN")
    extracted["timeframe"] = analysis_state.get("timeframe")
    metrics = analysis_state.get("metrics") or {}

    if mode == "definition":
        # Enough to anchor the term to the stock actually on screen.
        extracted["verdict"] = analysis_state.get("verdict")
        extracted["metrics"] = metrics
        return json.dumps(extracted, default=str)
    
    if mode == "portfolio":
        # Include risk, allocation, and current summary
        extracted["risk_warning"] = analysis_state.get("risk_warning")
        extracted["verdict"] = analysis_state.get("verdict")
        extracted["trade_setup"] = analysis_state.get("trade_setup")
    elif mode == "scenario":
        # Include triggers, technicals
        extracted["tutor_triggers"] = analysis_state.get("tutor_triggers")
        extracted["what_to_watch"] = analysis_state.get("what_to_watch")
        extracted["verdict"] = analysis_state.get("verdict")
        extracted["gate_results"] = analysis_state.get("gate_results")
        extracted["metrics"] = metrics
    elif mode == "news":
        # Minimal context for news synthesis
        extracted["verdict"] = analysis_state.get("verdict")
        extracted["tutor_triggers"] = analysis_state.get("tutor_triggers")
    else: # fallback
        extracted["verdict"] = analysis_state.get("verdict")
        extracted["metrics"] = metrics

    return json.dumps(extracted, default=str)

# --- 3. GENERATION NODE ---
async def generation_node(state: TutorState, config: RunnableConfig) -> TutorState:
    with tracer.start_as_current_span("generation_node"):
        mode = state["routed_mode"]
        ticker = state["analysis_state"].get("ticker", "UNKNOWN")
        logger.info("Generating response via mode: %s", mode.upper())
        
        llm = ChatOllama(
            model="llama3.1",
            temperature=0.3,
            num_predict=TUTOR_MAX_TOKENS,
        )
        trace.get_current_span().set_attribute("prompt.version", TUTOR_PROMPT_VERSION)
        
        analysis_state_str = extract_relevant_state(state.get('analysis_state', {}), mode)


        profile = state.get("user_profile") or {}
        experience = profile.get("experience_level", "intermediate")
        goal = profile.get("goal", "wealth_growth")

        # NOTE: single braces. These were doubled previously, which made every
        # placeholder render literally and left the model with no context at
        # all, so it invented whichever stock it felt like.
        sys_instruction = f"""You are an elite quantitative financial tutor for the Indian market.
User profile: experience {experience}, goal {goal}.

THE STOCK CURRENTLY ON SCREEN IS {ticker}. Every answer must be about {ticker}.
Never discuss or name a different company unless the user explicitly asks about one.

CRITICAL DIRECTIVES:
1. QUOTE-FIRST: anchor your answer in the exact numbers from the analysis state below.
2. ANALOGY-MAPPING: tailor analogies to the user's experience level.
3. CONTEXTUAL EXPLANATION: when defining a term, explain it against {ticker}'s own metrics and verdict rather than giving a generic definition.
4. INDIAN CONTEXT: use INR and Indian market framing.
5. CONCISE: short and direct. Reasoning and supporting figures, no filler.
6. FORMAT: write in "Header: Content" blocks, each header on its own line. Mark headers with **double asterisks**. Do not write large paragraphs.

--- CURRENT ANALYSIS STATE ---
{analysis_state_str}
"""

        if mode == "news" and state.get("tool_data"):
            sys_instruction += f"\n\n--- LATEST NEWS ---\n{state['tool_data']}"
            sys_instruction += "\nSynthesize the recent news with the current analysis state."
        elif mode == "definition":
            sys_instruction += f"\nExplain the requested term by linking it directly to {ticker}'s verdict and metrics. Show why it matters for this specific stock."
        elif mode == "portfolio":
            sys_instruction += "\nEvaluate the question against the user's stated allocations and goals."
        elif mode == "scenario":
            sys_instruction += "\nBreak down the 'what_to_watch' conditions. Explain the mechanics of each trigger and why it matters mathematically."
            sys_instruction += f"\n\n--- STATIC GATE THRESHOLDS ---\n{json.dumps(GATE_THRESHOLDS, indent=2)}\nUse these thresholds to explain why the triggers are relevant."
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