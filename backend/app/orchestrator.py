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
    
    print(f"  [Node] Passing Gold payload to LLM Synthesizer...")
    gold = state['gold']
    user = state['user_profile']
    
    # ---------------------------------------------------------
    # TODO: In the next step, we will replace this mock with 
    # ChatOpenAI.with_structured_output(AnalysisOutput)
    # ---------------------------------------------------------
    
    # For now, we mock the LLM understanding the Gold data and writing a report
    mock_llm_response = {
        "verdict": gold.verdict,
        "confidence_score": gold.confidence_score,
        "personalized_reasoning": [
            f"As a {user['experience_level']} investor focused on {user['goal']}, this stock triggered a {gold.verdict}.",
            f"The quantitative engine flagged the following primary reason: {gold.primary_reason}",
            f"We are strictly adhering to your {user['risk_tolerance']} risk profile."
        ],
        "what_to_watch": gold.what_to_watch,
        "risk_warning": "All equities carry market risk; position sizing must be respected.",
        "tutor_triggers": ["Death Cross", "SMA", "RSI", "CAGR"]
    }
    
    return {"llm_output": mock_llm_response}

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