import asyncio
import json
import os
import sys
from datetime import datetime

# Ensure we can import from the app folder if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage
from app.orchestrator import build_pipeline_graph
from app.pipeline.tutor_graph import build_tutor_graph

def default_json_serializer(obj):
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    return str(obj)

async def main():
    print("=== INVR QUANT PIPELINE & TUTOR CHAT ===")
    ticker = input("Enter ticker (e.g. RELIANCE): ").strip()
    if not ticker:
        return
        
    timeframe = input("Enter timeframe (intraday/swing/positional/long_term) [swing]: ").strip()
    if not timeframe:
        timeframe = "swing"
        
    output_filename = f"{ticker}_analysis_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print(f"\n[1/3] Running Quantitative Pipeline for {ticker} ({timeframe})...")
    pipeline = build_pipeline_graph()
    
    user_profile = {
        "risk_tolerance": "moderate",
        "experience_level": "intermediate",
        "goal": "Capital preservation and steady growth",
        "available_capital": 100000.0
    }
    
    initial_state = {
        "ticker": ticker.upper(),
        "timeframe": timeframe.lower(),
        "user_profile": user_profile,
        "bronze": None,
        "silver": None,
        "gold": None,
        "llm_output": None,
        "errors": []
    }
    
    try:
        final_state = await pipeline.ainvoke(initial_state, config={"recursion_limit": 10})
    except Exception as e:
        print(f"\n❌ Pipeline crashed: {e}")
        return
        
    if final_state.get("errors"):
        print(f"\n❌ Pipeline returned errors: {final_state['errors']}")
        return
        
    print(f"[2/3] Analysis complete! Saving output to {output_filename}...")
    
    analysis_output = final_state.get("llm_output", {})
    
    # Save initial analysis to file
    with open(output_filename, "a", encoding="utf-8") as f:
        f.write(f"=== QUANT PIPELINE ANALYSIS FOR {ticker} ===\n")
        f.write(json.dumps(analysis_output, indent=2, default=default_json_serializer) + "\n\n")
        f.write(f"=== TUTOR CHAT SESSION ===\n\n")
        
    print(f"\n[3/3] Tutor chat initialized. You can now ask questions about {ticker}.")
    print("Type 'quit' or 'exit' to end the session.\n")
    
    tutor_graph = build_tutor_graph()
    chat_history = []
    
    # Safely extract silver and gold dicts to pass to the Tutor graph
    silver = final_state.get("silver")
    gold = final_state.get("gold")
    silver_dict = silver.model_dump() if hasattr(silver, "model_dump") else (silver or {})
    gold_dict = gold.model_dump() if hasattr(gold, "model_dump") else (gold or {})
    
    # Ensure they are fully json serializable before putting them into tutor state
    safe_analysis_context = json.loads(json.dumps({
        "silver": silver_dict,
        "gold": gold_dict
    }, default=default_json_serializer))
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
            
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Session ended.")
            break
            
        if not user_input:
            continue
            
        chat_history.append(HumanMessage(content=user_input))
        
        tutor_initial_state = {
            "messages": chat_history,
            "analysis_state": safe_analysis_context,
            "user_profile": user_profile,
            "routed_mode": "",
            "tool_data": ""
        }
        
        print("Tutor: ", end="", flush=True)
        
        try:
            # Run the tutor graph
            tutor_final = await tutor_graph.ainvoke(tutor_initial_state, config={"recursion_limit": 10})
            
            # Get the last AI message
            ai_msg = tutor_final["messages"][-1]
            response_text = ai_msg.content
            print(f"{response_text}\n")
            
            # Keep history in sync
            chat_history = tutor_final["messages"]
            
            # Save interaction to file
            with open(output_filename, "a", encoding="utf-8") as f:
                f.write(f"User: {user_input}\n")
                f.write(f"Tutor: {response_text}\n\n")
                
        except Exception as e:
            print(f"[Error] Tutor crashed: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
