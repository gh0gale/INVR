import os
import re
import json
import logging
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage
from pydantic import ValidationError
from opentelemetry import trace

from app.schemas.state import AnalysisState
from app.schemas.llm import AnalysisOutput
from app.services.vector_store import query_ledger_history

from app.services.bronze_service import build_bronze_payload
from app.services.silver_service import compute_silver_metrics
from app.services.gold_service import evaluate_hard_gates

logger = logging.getLogger(__name__)

# ==========================================
# NODE 1: Data Fetching (Bronze)
# ==========================================
async def fetch_data_node(state: AnalysisState) -> AnalysisState:
    logger.info("Fetching internet data for %s", state['ticker'])
    try:
        bronze = await build_bronze_payload(state['ticker'], state['timeframe'])
        return {"bronze": bronze}
    except Exception as e:
        logger.error("Bronze Fetch Error for %s: %s", state.get('ticker'), str(e), exc_info=True)
        return {"errors": [f"Bronze Fetch Error: {str(e)}"]}

# ==========================================
# NODE 2: Quantitative Engine (Silver & Gold)
# ==========================================
import asyncio
async def quant_engine_node(state: AnalysisState) -> AnalysisState:
    if state.get("errors"): return state # Skip if previous node failed
    
    logger.info("Executing Quant Math & Hard Gates...")
    try:
        bronze = state['bronze']
        # LangGraph may deserialize Pydantic models to plain dicts; handle both cases
        if isinstance(bronze, dict):
            circuit_status = bronze.get('circuit_status', 'none')
        else:
            circuit_status = bronze.circuit_status
        
        available_capital = state['user_profile'].get('available_capital', 100000.0)
        
        # P7-01: Offload synchronous Pandas math to background thread
        silver = await asyncio.to_thread(compute_silver_metrics, bronze)
        gold = await asyncio.to_thread(
            evaluate_hard_gates,
            silver, 
            circuit_status,
            available_capital
        )
        return {"silver": silver, "gold": gold}
    except Exception as e:
        logger.error("Quant Engine Error for %s: %s", state.get('ticker'), str(e), exc_info=True)
        return {"errors": [f"Quant Engine Error: {str(e)}"]}

# ==========================================
# HELPERS: CoT & Safe Access
# ==========================================
def strip_thinking_block(raw_text: str) -> tuple[str, str]:
    """Phase 4: CoT Isolation. Strips <thinking> tags to extract clean JSON."""
    thinking = ""
    clean_output = raw_text
    
    thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw_text, re.DOTALL)
    if thinking_match:
        thinking = thinking_match.group(1).strip()
        clean_output = re.sub(r"<thinking>.*?</thinking>", "", raw_text, flags=re.DOTALL).strip()
        
    # Strip markdown formatting if the LLM wraps the JSON
    if "```json" in clean_output:
        clean_output = clean_output.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_output:
        clean_output = clean_output.split("```")[1].split("```")[0].strip()
        
    return thinking, clean_output

def _safe_get(obj, attr, default=None):
    """LangGraph may return state nodes as plain dicts after serialization."""
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

# ==========================================
# NODE 3: The LLM Synthesizer (Platinum)
# ==========================================
async def llm_synthesizer_node(state: AnalysisState) -> Dict[str, Any]:
    if state.get("errors"): return {}
    
    logger.info("Passing Gold payload to LOCAL Llama-3.1 Synthesizer...")
    gold = state['gold']
    user = state['user_profile']
    silver = state['silver']
    
    try:
        # Standard inference without structural wrapper to allow CoT reasoning
        llm = ChatOllama(model="llama3.1", temperature=0.0)
        
        # Sanitize untrusted input to prevent prompt injection
        safe_silver = (silver.model_dump_json(exclude_none=True) if hasattr(silver, 'model_dump_json') else str(silver)).replace("<", "&lt;").replace(">", "&gt;")
        safe_watch = str(_safe_get(gold, 'what_to_watch', [])).replace("<", "&lt;").replace(">", "&gt;")
        
        # Phase 3: Inject dynamic correction notes if looping
        correction_instruction = ""
        if state.get("correction_note"):
            correction_instruction = f"\nCRITICAL CORRECTION REQUIRED FROM PREVIOUS ATTEMPT:\n{state['correction_note']}\nFix this specific schema error."

        # RAG context for Analytics Pipeline (Phase 2 requirement)
        historical_context = await query_ledger_history(state['ticker'], routed_mode="scenario")

        sys_prompt = f"""You are an elite quantitative financial synthesizer. You translate mathematical verdicts into deep, institutional-grade tear sheets.

CRITICAL INSTRUCTIONS:
1. Before producing the final JSON, think through your reasoning inside <thinking>...</thinking> tags.
2. Do NOT include any analysis inside the JSON keys themselves. The JSON must exactly match the schema.
3. Output strictly valid JSON immediately after your thinking block.
4. EVERY claim MUST be backed by exact numbers from the metrics.
5. 'tutor_triggers' MUST be an array of 2-4 single financial jargon words ONLY.{correction_instruction}

REQUIRED JSON SCHEMA:
{{
    "personalized_reasoning": [
        "INVESTMENT THESIS & PROFILE ALIGNMENT",
        "- [Write 2 detailed sentences explaining if the trajectory matches the user goal, citing specific data].",
        "- [Write 2 detailed sentences analyzing the risk fit for the investor]."
    ],
    "what_to_watch": [
        "- [Actionable Condition] -- Current: [value]. [Explain why this level acts as a critical structural pivot].",
        "KEY RISK MONITOR: [Weakest metric]. [Explain exactly how deterioration threatens capital]."
    ],
    "risk_warning": "[1 mandatory sentence regarding the highest risk data point]",
    "tutor_triggers": ["string (jargon)", "string (jargon)"]
}}

--- QUANTITATIVE DATA ---
TICKER: {state['ticker']}
TIMEFRAME: {state['timeframe']}
USER GOAL: {user.get('goal', 'growth')}
USER RISK: {user.get('risk_tolerance', 'moderate')}

VERDICT: {_safe_get(gold, 'verdict', 'MONITOR')}
PRIMARY REASON: {_safe_get(gold, 'primary_reason', '')}
GATE RESULTS: {str(_safe_get(gold, 'gate_results', {{}}))}
ACTIONABLE CONDITIONS: {safe_watch}

SILVER METRICS: {safe_silver}

--- HISTORICAL ALGORITHMIC CONTEXT ---
{historical_context}
"""

        response = await llm.ainvoke([SystemMessage(content=sys_prompt)])
        
        thinking, clean_json_str = strip_thinking_block(response.content)
        if thinking:
            logger.info(f"LLM CoT Execution Completed. (Thinking length: {len(thinking)} chars)")
            
        # Return the raw string to the validation node
        return {"llm_output": {"raw_json_string": clean_json_str}}
        
    except Exception as e:
        logger.warning("LLM Offline/Failed. Falling back to deterministic verdict. Error: %s", str(e))
        gold_verdict = _safe_get(gold, 'verdict', 'MONITOR')
        gold_confidence = _safe_get(gold, 'confidence_score', 50.0)
        gold_reason = _safe_get(gold, 'primary_reason', 'Deterministic analysis completed.')
        gold_watch = _safe_get(gold, 'what_to_watch', [])
        
        fallback_dict = {
            "verdict": gold_verdict,
            "confidence_score": gold_confidence,
            "personalized_reasoning": [
                "SYSTEM NOTICE: AI Synthesizer is currently offline.",
                f"DETERMINISTIC VERDICT: {gold_verdict}",
                f"PRIMARY REASON: {gold_reason}"
            ],
            "what_to_watch": gold_watch,
            "tutor_triggers": ["LLM_OFFLINE", "FALLBACK"],
            "regulatory_disclaimer": "This analysis is generated by an AI for educational purposes only. It does not constitute financial advice. Please consult a SEBI-registered investment advisor."
        }
        return {"llm_output": fallback_dict, "correction_note": None}

# ==========================================
# NODE 4: Schema Validation (Phase 3)
# ==========================================
def validate_synthesis_node(state: AnalysisState) -> Dict[str, Any]:
    if state.get("errors"): return {}
        
    logger.info("Validating LLM output schema...")
    llm_output = state.get("llm_output", {})
    
    # If the LLM failed and we generated a deterministic dict, bypass validation
    if "raw_json_string" not in llm_output:
        return {}
        
    raw_str = llm_output.get("raw_json_string", "")
    
    try:
        parsed_dict = json.loads(raw_str)
        validated_data = AnalysisOutput(**parsed_dict).model_dump()
        
        # Post-LLM Injection: Guaranteeing mathematical integrity
        gold = state["gold"]
        validated_data["verdict"] = _safe_get(gold, 'verdict', 'MONITOR')
        validated_data["confidence_score"] = _safe_get(gold, 'confidence_score', 50.0)
        validated_data["regulatory_disclaimer"] = "This analysis is generated by an AI for educational purposes only. It does not constitute financial advice. Please consult a SEBI-registered investment advisor."
        
        logger.info("Synthesis schema validation PASSED.")
        # Clear the correction note and output the finalized dictionary
        return {"llm_output": validated_data, "correction_note": None}
        
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(f"Synthesis validation FAILED: {str(e)}")
        return {"correction_note": f"Schema Validation Error: {str(e)}\nPlease ensure your output is strictly valid JSON matching the exact schema."}

# ==========================================
# CONDITIONAL EDGES
# ==========================================
def route_validation(state: AnalysisState) -> str:
    """Evaluates if the graph should loop back, terminate, or fallback."""
    if state.get("errors"): return END
    
    # Validation cleared the correction note = success
    if not state.get("correction_note"):
        return END
        
    current_retries = state.get("retry_count", 0)
    
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute("analysis.retry_count", current_retries + 1)
        span.set_attribute("analysis.correction_note", state.get("correction_note"))
        
    if current_retries >= 2:
        logger.error("Max retries hit. Graph terminating with errors.")
        return END
        
    logger.info(f"Self-Healing: Routing back to LLM synthesizer (Retry {current_retries + 1}/2)")
    return "increment_retry"

def increment_retry_node(state: AnalysisState) -> Dict[str, Any]:
    return {"retry_count": state.get("retry_count", 0) + 1}

# ==========================================
# GRAPH COMPILATION
# ==========================================
def build_pipeline_graph():
    workflow = StateGraph(AnalysisState)
    
    # Add Nodes
    workflow.add_node("fetch_data", fetch_data_node)
    workflow.add_node("quant_engine", quant_engine_node)
    workflow.add_node("llm_synthesizer", llm_synthesizer_node)
    workflow.add_node("validate_synthesis", validate_synthesis_node)
    workflow.add_node("increment_retry", increment_retry_node)
    
    # Add Edges (Linear Flow to Synthesizer)
    workflow.set_entry_point("fetch_data")
    workflow.add_edge("fetch_data", "quant_engine")
    workflow.add_edge("quant_engine", "llm_synthesizer")
    workflow.add_edge("llm_synthesizer", "validate_synthesis")
    
    # The Self-Healing Conditional Loop
    workflow.add_conditional_edges(
        "validate_synthesis",
        route_validation,
        {
            "increment_retry": "increment_retry",
            END: END
        }
    )
    workflow.add_edge("increment_retry", "llm_synthesizer")
    
    return workflow.compile()