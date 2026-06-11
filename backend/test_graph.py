import asyncio
from app.orchestrator import build_pipeline_graph

async def run_langgraph():
    print("=" * 80)
    print("🤖 INITIATING LANGGRAPH ORCHESTRATOR")
    print("=" * 80)

    # 1. Define the Initial State (Including the Mock User Profile)
    initial_state = {
        "ticker": "INFY",
        "timeframe": "positional",
        "user_profile": {
            "risk_tolerance": "moderate",
            "experience_level": "beginner",
            "goal": "Consistent long-term compounding",
            "available_capital": 250000.0
        },
        "errors": []
    }

    # 2. Compile the Graph
    graph = build_pipeline_graph()

    # 3. Execute the Graph
    print("\n🚀 Invoking Pipeline...")
    # Because our fetch_node is async, we must use ainvoke()
    final_state = await graph.ainvoke(initial_state)

    # 4. Display the Results
    if final_state.get("errors"):
        print("\n❌ PIPELINE FAILED:")
        for err in final_state["errors"]:
            print(f"  - {err}")
        return

    print("\n" + "=" * 80)
    print("✨ FINAL LLM OUTPUT OBJECT (Sent to Frontend/Database)")
    print("=" * 80)
    
    output = final_state["llm_output"]
    print(f"🎯 Verdict:      {output['verdict']} ({output['confidence_score']}%)")
    print(f"⚠️ Risk Warning: {output['risk_warning']}")
    
    print("\n🧠 Personalized Reasoning:")
    for reason in output["personalized_reasoning"]:
        print(f"  - {reason}")
        
    print("\n👀 What to Watch:")
    for item in output["what_to_watch"]:
        print(f"  - {item}")
        
    print("\n📚 Tutor Triggers Detected:")
    print(f"  {', '.join(output['tutor_triggers'])}")

if __name__ == "__main__":
    asyncio.run(run_langgraph())