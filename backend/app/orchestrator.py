import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from app.schemas.state import AnalysisState
from app.services.bronze_service import build_bronze_payload
from app.services.silver_service import compute_silver_metrics
from app.services.gold_service import evaluate_hard_gates
from app.schemas.llm import AnalysisOutput

# ==========================================
# NODE 1: Data Fetching (Bronze)
# ==========================================
async def fetch_data_node(state: AnalysisState) -> AnalysisState:
    print(f"  [Node] Fetching internet data for {state['ticker']}...")
    try:
        bronze = await build_bronze_payload(state['ticker'], state['timeframe'])
        return {"bronze": bronze}
    except Exception as e:
        return {"errors": [f"Bronze Fetch Error: {str(e)}"]}

# ==========================================
# NODE 2: Quantitative Engine (Silver & Gold)
# ==========================================
def quant_engine_node(state: AnalysisState) -> AnalysisState:
    if state.get("errors"): return state # Skip if previous node failed
    
    print(f"  [Node] Executing Quant Math & Hard Gates...")
    try:
        silver = compute_silver_metrics(state['bronze'])
        gold = evaluate_hard_gates(
            silver=silver, 
            circuit_status=state['bronze'].circuit_status,
            available_capital=state['user_profile']['available_capital']
        )
        return {"silver": silver, "gold": gold}
    except Exception as e:
        return {"errors": [f"Quant Engine Error: {str(e)}"]}

# ==========================================
# NODE 3: The LLM Synthesizer (Platinum)
# ==========================================

def llm_synthesizer_node(state: AnalysisState) -> AnalysisState:
    if state.get("errors"): return state
    
    print(f"  [Node] Passing Gold payload to LOCAL Llama-3.1 Synthesizer...")
    gold = state['gold']
    user = state['user_profile']
    
    try:
        llm = ChatOllama(model="llama3.1", temperature=0.0)
        structured_llm = llm.with_structured_output(AnalysisOutput)
        
        # 1. Updated Prompt to enforce numerical accuracy and dynamic reasoning
        # 1. Updated Prompt to enforce strict bulleted teardown and ban emojis
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a quantitative financial synthesizer. You receive pre-computed mathematical verdicts and translate them into strict, institutional-grade tear sheets.
            
            CRITICAL RULES:
            - Never contradict the quantitative verdict.
            - Use the exact numeric values from the 'Raw Quantitative Metrics'.
            - DO NOT invent price targets, percentages, or dates.
            - STRICTLY NO EMOJIS. Use standard text and dashes for lists.
            - Vocabulary level: {experience_level}
            - User goal: {goal}
            
            === EXPECTED OUTPUT FORMAT ===
            
            Format 'personalized_reasoning' as an array of strings following this exact narrative flow:
            "Reasons:"
            "- [Alignment with user timeframe and goal]"
            "- [Alignment with user risk tolerance ({risk_tolerance})]"
            "- [Overall macro or sector context]"
            "The stock [passes/fails] several key quality filters:"
            "- [Specific Metric 1 from Primary Reason]"
            "- [Specific Metric 2 from Primary Reason]"
            "- [Specific Metric 3 from Primary Reason]"
            
            Format 'what_to_watch' as an array of strings. Start with the 'Actionable Conditions' provided, then add 1-2 more conditions by extracting current values from the 'Raw Quantitative Metrics' (e.g., monitor specific RSI levels, Volume averages, or SMA gaps).
            
            Risk Warning: A 1-sentence strict risk disclaimer.
            """),
            
            ("human", """Stock: {ticker}
            Verdict: {verdict} | Confidence: {confidence_score}%
            Primary Reason: {primary_reason}
            Gate Results: {gate_results}
            
            Actionable Conditions:
            {what_to_watch}
            
            Raw Quantitative Metrics:
            {silver_metrics}
            
            Generate the structured analysis JSON.""")
        ])
        
        chain = prompt | structured_llm
        
        # 2. Injecting the exact mathematical payload (silver_metrics)
        response = chain.invoke({
            "experience_level": user.get('experience_level', 'intermediate'),
            "goal": user.get('goal', 'growth'),
            "risk_tolerance": user.get('risk_tolerance', 'moderate'),
            "ticker": state['ticker'],
            "verdict": gold.verdict,
            "confidence_score": gold.confidence_score,
            "primary_reason": gold.primary_reason,
            "gate_results": str(gold.gate_results),
            "what_to_watch": str(gold.what_to_watch),
            "silver_metrics": state['silver'].model_dump_json(exclude_none=True) # <-- Passes exact math to the LLM
        })
        
        return {"llm_output": response.model_dump()}
        
    except Exception as e:
        return {"errors": [f"Local LLM Error: {str(e)}"]}

# ==========================================
# GRAPH COMPILATION
# ==========================================
def build_pipeline_graph():
    workflow = StateGraph(AnalysisState)
    
    # Add Nodes
    workflow.add_node("fetch_data", fetch_data_node)
    workflow.add_node("quant_engine", quant_engine_node)
    workflow.add_node("llm_synthesizer", llm_synthesizer_node)
    
    # Add Edges (Linear Flow)
    workflow.set_entry_point("fetch_data")
    workflow.add_edge("fetch_data", "quant_engine")
    workflow.add_edge("quant_engine", "llm_synthesizer")
    workflow.add_edge("llm_synthesizer", END)
    
    return workflow.compile()