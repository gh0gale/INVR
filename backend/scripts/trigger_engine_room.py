import sys
import os

# Add the root backend path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pipeline.engine_room_graph import build_engine_room_graph

def run():
    print("Triggering Engine Room Workflow...")
    graph = build_engine_room_graph()
    
    # Run the graph
    config = {"configurable": {"thread_id": "engine-room-run-1"}}
    state = {}
    
    print("Running pipeline (until human review)...")
    # This will run until the human_review node interrupts it
    for event in graph.stream(state, config=config):
        for key, value in event.items():
            print(f"Node '{key}': {value}")
            
    # Check if we hit the interrupt
    current_state = graph.get_state(config)
    if not current_state.next:
        print("Pipeline finished (no insights to review).")
        return
        
    print(f"\n[!] PIPELINE PAUSED AT: {current_state.next}")
    print("Pending values:")
    print(current_state.values)
    
    if current_state.values.get("metric") == "none":
        return
        
    # Simulate HITL prompt
    ans = input(f"\nApprove update to {current_state.values['metric']}? (y/n): ")
    if ans.lower() == 'y':
        print("Approving update...")
        # Inject the approval into the state
        graph.update_state(config, {"approved": True})
    else:
        print("Rejecting update...")
        graph.update_state(config, {"approved": False})
        
    # Resume the graph
    print("Resuming pipeline...")
    for event in graph.stream(None, config=config):
        for key, value in event.items():
            print(f"Node '{key}': {value}")
            
    print("Workflow complete.")

if __name__ == "__main__":
    run()
