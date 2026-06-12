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
        # 1. Initialize the Local Model via Ollama
        # temperature=0 makes it deterministic and less likely to hallucinate
        llm = ChatOllama(model="llama3.1", temperature=0.0)
        
        # 2. Force structured JSON output
        structured_llm = llm.with_structured_output(AnalysisOutput)
        
        # 3. Create the System Prompt with a "Few-Shot" Example
        # 3. Create the System Prompt with a "Few-Shot" Example
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial analysis synthesizer. You receive pre-computed quantitative 
            verdicts from a deterministic Python engine and translate them into clear, accurate, 
            personalized explanations.
            
            CRITICAL RULES:
            - Never contradict the quantitative verdict. The math is ground truth.
            - Never invent price targets, percentages, or dates not present in the input data.
            - Never use phrases like 'I think' or 'possibly' about the verdict.
            - Vocabulary level: {experience_level}
            - User goal: {goal}
            - Risk profile: {risk_tolerance}
            
            === EXAMPLE INPUT ===
            Verdict: WAIT | Confidence: 65.0%
            Reason: Failed 2 critical structural gates.
            Gate Results: {{'trend': 'PASS', 'death_cross': 'FAIL', 'revenue_growth': 'FAIL'}}
            What to Watch: ['Confirmed Death Cross. Avoid until 50-day SMA reclaims 200-day SMA.', 'Revenue CAGR is lagging the 10.0% target.']
            
            === EXPECTED OUTPUT FORMAT ===
            Personalized Reasoning: 
            - "As a beginner focused on long-term compounding, this stock triggered a WAIT."
            - "The quantitative engine flagged that the asset failed 2 critical structural gates."
            - "We are strictly adhering to your moderate risk profile by avoiding entry during a fundamental and technical breakdown."
            What to Watch: 
            - "Confirmed Death Cross. Avoid until 50-day SMA reclaims 200-day SMA."
            - "Revenue CAGR is lagging the 10.0% target."
            Risk Warning: "Attempting to catch a falling asset during a death cross carries severe downside risk."
            Tutor Triggers: ["Death Cross", "SMA", "CAGR"]
            """),
            
            ("human", """Stock: {ticker}
            Verdict: {verdict} | Confidence: {confidence_score}%
            Reason: {primary_reason}
            
            Gate Results:
            {gate_results}
            
            What to Watch:
            {what_to_watch}
            
            Generate the structured analysis JSON based on the example provided.""")
        ])
        
        # 4. Chain them together and execute
        chain = prompt | structured_llm
        
        # We format the lists/dicts to strings so the prompt injects them cleanly
        response = chain.invoke({
            "experience_level": user['experience_level'],
            "goal": user['goal'],
            "risk_tolerance": user['risk_tolerance'],
            "ticker": state['ticker'],
            "verdict": gold.verdict,
            "confidence_score": gold.confidence_score,
            "primary_reason": gold.primary_reason,
            "gate_results": str(gold.gate_results),
            "what_to_watch": str(gold.what_to_watch)
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