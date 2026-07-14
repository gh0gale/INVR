import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from supabase import create_client

from app.config import settings

logger = logging.getLogger(__name__)

supabase = create_client(os.getenv("SUPABASE_URL", settings.SUPABASE_URL), os.getenv("SUPABASE_SERVICE_ROLE_KEY", settings.SUPABASE_SERVICE_ROLE_KEY))

class DriftLoopState(TypedDict):
    insight_id: Optional[str]
    metric: str
    current_threshold: float
    suggested_threshold: float
    reasoning: str
    risk_tier: Optional[str]      # "low" | "high"
    approved: bool

# Critical constants that have high blast-radius
HIGH_RISK_METRICS = [
    "debt_equity_max",
    "roe_min",
    "revenue_cagr_min",
    "eps_cagr_min",
    "max_pe"
]

def load_insight_node(state: DriftLoopState) -> DriftLoopState:
    logger.info("Loading latest pending threshold insights...")
    
    # We look for insights inserted recently (assuming a 'status' column exists, or we just grab the latest)
    # If the database doesn't have a status column, we grab the most recent one that doesn't match our current config.
    try:
        # Try to select where status is pending
        res = supabase.table("threshold_insights").select("*").eq("status", "pending").order("created_at", desc=True).limit(1).execute()
        data = res.data
    except Exception:
        # Fallback if 'status' column doesn't exist
        res = supabase.table("threshold_insights").select("*").order("created_at", desc=True).limit(1).execute()
        data = res.data
        
    if not data:
        logger.info("No new threshold insights found.")
        return {"metric": "none"}
        
    insight = data[0]
    return {
        "insight_id": str(insight.get("id", "")),
        "metric": insight["metric"],
        "current_threshold": insight["current_threshold"],
        "suggested_threshold": insight["suggested_threshold"],
        "reasoning": insight["reasoning"],
    }

def classify_risk_node(state: DriftLoopState) -> DriftLoopState:
    if state.get("metric") == "none":
        return state
        
    metric = state["metric"]
    logger.info(f"Classifying risk for metric: {metric}")
    
    # High risk = Position sizing, strict fundamental quality, or stop-loss logic
    # Low risk = Cosmetic indicators (RSI, SMA gaps, volume ratios)
    if metric in HIGH_RISK_METRICS:
        risk_tier = "high"
    else:
        risk_tier = "low"
        
    return {"risk_tier": risk_tier}

def human_review_node(state: DriftLoopState) -> DriftLoopState:
    if state.get("metric") == "none":
        return state
        
    # This node acts as a pause point. In a real persistent LangGraph setup, 
    # we would interrupt here. For this script, we simulate it by checking 'approved' flag 
    # passed in or simply pausing execution if run interactively.
    
    logger.info(f"--- HUMAN REVIEW REQUIRED ---")
    logger.info(f"Metric: {state['metric']}")
    logger.info(f"Current: {state['current_threshold']} -> Suggested: {state['suggested_threshold']}")
    logger.info(f"Reason: {state['reasoning']}")
    logger.info(f"Risk Tier: {state['risk_tier'].upper()}")
    
    # We will assume approval is injected via update_state, but if running synchronously
    # we can default to False to prevent auto-commit of high-risk items unless explicitly approved.
    if state.get("approved") is None:
        state["approved"] = False
        
    return state

def apply_update_node(state: DriftLoopState) -> DriftLoopState:
    if state.get("metric") == "none" or not state.get("approved"):
        logger.info("Update bypassed or rejected.")
        return state
        
    logger.info(f"Applying update to {state['metric']} -> {state['suggested_threshold']}")
    
    # Programmatically update gate_thresholds.py
    # We will load the file, use regex/string replacement to update the value, and add to history
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "gate_thresholds.py")
    
    with open(config_path, "r") as f:
        content = f.read()
        
    # Replace the numeric value in the dictionary
    import re
    # Find the line like: "rsi_overbought": 70.0,
    pattern = rf'("{state["metric"]}"\s*:\s*)([\d\.-]+)(.*)'
    replacement = rf'\g<1>{state["suggested_threshold"]}\g<3>'
    
    new_content = re.sub(pattern, replacement, content)
    
    # Append to history list
    history_entry = {
        "date": datetime.utcnow().isoformat(),
        "metric": state["metric"],
        "old": state["current_threshold"],
        "new": state["suggested_threshold"],
        "reason": state["reasoning"]
    }
    
    # Find GATE_THRESHOLDS_HISTORY and insert
    history_str = f"    {json.dumps(history_entry)},\n"
    new_content = new_content.replace("GATE_THRESHOLDS_HISTORY = [", "GATE_THRESHOLDS_HISTORY = [\n" + history_str)
    
    with open(config_path, "w") as f:
        f.write(new_content)
        
    # Optionally update status in Supabase
    if state.get("insight_id"):
        try:
            supabase.table("threshold_insights").update({"status": "applied"}).eq("id", state["insight_id"]).execute()
        except Exception as e:
            logger.warning(f"Could not update status in Supabase (may not exist): {e}")

    logger.info("Configuration successfully versioned and updated.")
    return state

def build_engine_room_graph():
    builder = StateGraph(DriftLoopState)
    
    builder.add_node("load_insight", load_insight_node)
    builder.add_node("classify_risk", classify_risk_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("apply_update", apply_update_node)
    
    builder.add_edge(START, "load_insight")
    
    def check_insight(state: DriftLoopState):
        if state.get("metric") == "none":
            return END
        return "classify_risk"
        
    builder.add_conditional_edges("load_insight", check_insight)
    builder.add_edge("classify_risk", "human_review")
    builder.add_edge("human_review", "apply_update")
    builder.add_edge("apply_update", END)
    
    # We compile with a checkpointer so we can pause at human_review
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    return builder.compile(checkpointer=memory, interrupt_before=["human_review"])
