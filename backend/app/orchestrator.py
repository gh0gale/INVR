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
        
        # 1. Hybrid Prompt: Strict Template + Deep Analytical Requirements
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an elite quantitative financial synthesizer. You translate mathematical verdicts into deep, institutional-grade tear sheets.

            CRITICAL RULES:
            1. NEVER output my template instructions back to me. Provide actual analysis.
            2. STRICTLY NO EMOJIS. Use standard text and dashes.
            3. Every claim MUST be backed by exact numbers from the 'Raw Quantitative Metrics' or 'Gate Results'.
            4. 'tutor_triggers' MUST be an array of 2-4 single financial jargon words ONLY (e.g., ["SMA", "CAGR", "RSI"]). Strictly NO sentences.

            === EXACT OUTPUT FORMAT FOR 'personalized_reasoning' ===
            Format as an array of strings using this exact structure. Replace the bracketed instructions with deep, analytical sentences:

            "INVESTMENT THESIS & PROFILE ALIGNMENT"
            "- [Write 2 detailed sentences explaining if the stock's {timeframe} trajectory matches the user goal of {goal}, citing specific growth or trend data from the metrics]."
            "- [Write 2 detailed sentences analyzing the risk fit for a {risk_tolerance} investor, citing the stock's debt trajectory, market regime, or volatility]."

            "QUANTITATIVE SCORECARD"
            "- [Metric 1 from data]: [Value] -- [PASS/FAIL/WATCH] -- [Write a detailed sentence explaining the financial implication of this number on the overall business health or price action]."
            "- [Metric 2 from data]: [Value] -- [PASS/FAIL/WATCH] -- [Write a detailed sentence explaining the financial implication of this number on the overall business health or price action]."
            "- [Metric 3 from data]: [Value] -- [PASS/FAIL/WATCH] -- [Write a detailed sentence explaining the financial implication of this number on the overall business health or price action]."

            "OVERALL VERDICT RATIONALE"
            "- [Write a dense, 4-5 sentence analytical paragraph explaining exactly why the {verdict} was reached. Synthesize the strengths and weaknesses, and explain the mathematical weight of the primary failing/passing gates.]"

            === EXACT OUTPUT FORMAT FOR 'what_to_watch' ===
            Format as an array of strings.
            - Start with each Actionable Condition provided, formatted as: "[Condition] -- Current: [value]. [Add a detailed sentence explaining why this specific level acts as a critical structural pivot]."
            - Add 1-2 forward-looking triggers from the data: "[Metric Name]: Watch for [Trigger level] -- Current: [value]. [Add a detailed sentence explaining the risk/reward of this trigger]."
            - "KEY RISK MONITOR: [Identify the weakest metric]. [Write 1-2 sentences explaining exactly how further deterioration here threatens the capital]."
            """),
            
            ("human", """Ticker: {ticker}
            Timeframe: {timeframe}
            Verdict: {verdict} | Confidence: {confidence_score}%
            Primary Reason: {primary_reason}
            Gate Results: {gate_results}
            
            Actionable Conditions from System:
            {what_to_watch}
            
            Raw Quantitative Metrics (Silver Layer):
            {silver_metrics}
            
            User Profile:
            - Goal: {goal}
            - Risk Tolerance: {risk_tolerance}
            
            Generate the structured analysis JSON following the exact template.""")
        ])
        
        chain = prompt | structured_llm
        
        response = chain.invoke({
            "goal": user.get('goal', 'wealth growth'),
            "risk_tolerance": user.get('risk_tolerance', 'moderate'),
            "ticker": state['ticker'],
            "timeframe": state['timeframe'],
            "verdict": gold.verdict,
            "confidence_score": gold.confidence_score,
            "primary_reason": gold.primary_reason,
            "gate_results": str(gold.gate_results),
            "what_to_watch": str(gold.what_to_watch),
            "silver_metrics": state['silver'].model_dump_json(exclude_none=True)
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