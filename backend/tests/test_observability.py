import pytest
import asyncio
from typing import Dict, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# Import the nodes we want to test
from app.orchestrator import fetch_data_node, quant_engine_node

# Use a global exporter so we don't try to re-initialize TracerProvider
_exporter = InMemorySpanExporter()
_provider_set = False

@pytest.fixture
def memory_exporter():
    global _provider_set
    if not _provider_set:
        provider = TracerProvider()
        processor = SimpleSpanProcessor(_exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _provider_set = True
    
    yield _exporter
    
    _exporter.clear()

def test_fetch_data_node_tracing(memory_exporter, monkeypatch):
    # Mock the bronze fetcher so we don't hit the internet
    async def mock_build_bronze_payload(ticker, timeframe):
        return {"mock": "data", "circuit_status": "none"}
        
    import app.orchestrator
    monkeypatch.setattr(app.orchestrator, "build_bronze_payload", mock_build_bronze_payload)
    
    # Run the node
    state = {"ticker": "RELIANCE.NS", "timeframe": "swing"}
    
    async def run_test():
        return await fetch_data_node(state)
        
    result = asyncio.run(run_test())
    
    # Verify the span was generated and attributes match
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1, "Expected exactly 1 span to be generated."
    
    span = spans[0]
    assert span.name == "fetch_data_node"
    assert span.attributes.get("ticker") == "RELIANCE.NS"
    assert span.attributes.get("timeframe") == "swing"

def test_quant_engine_node_tracing(memory_exporter, monkeypatch):
    # Mock the background math threads
    def mock_compute_silver(bronze):
        return {"rsi": 50}
        
    def mock_evaluate_hard_gates(silver, circuit_status, available_capital):
        return {"verdict": "BUY"}
        
    import app.orchestrator
    monkeypatch.setattr(app.orchestrator, "compute_silver_metrics", mock_compute_silver)
    monkeypatch.setattr(app.orchestrator, "evaluate_hard_gates", mock_evaluate_hard_gates)
    
    state = {
        "ticker": "RELIANCE.NS",
        "bronze": {"circuit_status": "none"},
        "user_profile": {"available_capital": 10000}
    }
    
    async def run_test():
        return await quant_engine_node(state)
        
    result = asyncio.run(run_test())
    
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    
    span = spans[0]
    assert span.name == "quant_engine_node"
    assert span.attributes.get("circuit_status") == "none"

def test_full_pipeline_tracing(memory_exporter, monkeypatch):
    import app.orchestrator
    from langchain_core.outputs import ChatResult, ChatGeneration
    from langchain_core.messages import AIMessage
    from langchain_ollama import ChatOllama
    
    # 1. Mock Data Fetching
    async def mock_build_bronze_payload(ticker, timeframe):
        return {"circuit_status": "none"}
    monkeypatch.setattr(app.orchestrator, "build_bronze_payload", mock_build_bronze_payload)
    
    # 2. Mock Quant Engine
    def mock_compute_silver(bronze):
        return {"rsi": 50}
    def mock_evaluate_hard_gates(silver, circuit_status, available_capital):
        return {"verdict": "BUY"}
    monkeypatch.setattr(app.orchestrator, "compute_silver_metrics", mock_compute_silver)
    monkeypatch.setattr(app.orchestrator, "evaluate_hard_gates", mock_evaluate_hard_gates)
    
    # 3. Mock LLM to avoid real Ollama call but still trigger LangChainInstrumentor span
    async def mock_agenerate(*args, **kwargs):
        with trace.get_tracer(__name__).start_as_current_span("ChatOllama") as span:
            span.set_attribute("llm.usage.total_tokens", 195)
            msg = AIMessage(
                content='<thinking>Evaluating risk.</thinking>\n```json\n{"personalized_reasoning": ["A", "B", "C"], "what_to_watch": ["X", "Y"], "risk_warning": "High risk", "tutor_triggers": ["RSI", "MACD"]}\n```',
                response_metadata={"prompt_eval_count": 150, "eval_count": 45}
            )
            return ChatResult(generations=[ChatGeneration(message=msg)])
        
    monkeypatch.setattr(ChatOllama, "_agenerate", mock_agenerate)
    
    # 4. Run the full graph
    graph = app.orchestrator.build_pipeline_graph()
    state = {
        "ticker": "RELIANCE.NS",
        "timeframe": "swing",
        "user_profile": {"available_capital": 10000}
    }
    
    async def run_test():
        # Wrap the whole execution in a root trace as if it was an API request
        with trace.get_tracer(__name__).start_as_current_span("orchestrator_pipeline"):
            return await graph.ainvoke(state)
            
    result = asyncio.run(run_test())
    
    spans = memory_exporter.get_finished_spans()
    
    print("\n--- TRACE HIERARCHY OUTPUT ---")
    def print_tree(span_id, level=0):
        # Find children of this span
        children = [s for s in spans if s.parent and s.parent.span_id == span_id]
        # Sort by start time to maintain execution order
        children.sort(key=lambda x: x.start_time)
        for s in children:
            print("  " * level + f"|-- {s.name} (Span)")
            # Print important attributes
            for k, v in s.attributes.items():
                # Filter down to the specific attributes requested by the user to avoid noise
                if k in ["ticker", "timeframe", "circuit_status", "sanitized_input", "sanitized_output"] or "token" in k or k == "llm.usage.total_tokens":
                    # Truncate long strings for display
                    val_str = str(v).replace('\n', ' ')
                    if len(val_str) > 60: val_str = val_str[:57] + "..."
                    print("  " * (level+1) + f"Attributes: {k}={val_str}")
            print_tree(s.context.span_id, level + 1)

    # Find the root span
    root_spans = [s for s in spans if not s.parent]
    for r in root_spans:
        if r.name == "orchestrator_pipeline":
            latency = (r.end_time - r.start_time) / 1e9
            print(f"\n{r.name} (Trace Root, Latency: {latency:.4f}s)")
            print_tree(r.context.span_id, 1)
    
    print("------------------------------\n")
