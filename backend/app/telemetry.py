import os
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry import trace, context as otel_context
from openinference.instrumentation.langchain import LangChainInstrumentor

def init_telemetry():
    """Initializes OpenTelemetry and LangChain auto-instrumentation."""
    # Defaults to local Phoenix or Jaeger collector
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:6060/v1/traces")
    
    resource = Resource(attributes={"service.name": "finai-orchestrator"})
    provider = TracerProvider(resource=resource)
    
    # Batch processing ensures telemetry doesn't add latency to API responses
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # CRITICAL: This must run before LangGraph/LangChain are imported
    LangChainInstrumentor().instrument(tracer_provider=provider)
    
    return trace.get_tracer(__name__)

def wrap_background_task(func):
    """
    Decorator/Wrapper to forcefully carry the OpenTelemetry Trace ID 
    from the main FastAPI thread into a detached BackgroundTask.
    """
    ctx = otel_context.get_current()
    
    async def wrapper(*args, **kwargs):
        token = otel_context.attach(ctx)
        try:
            return await func(*args, **kwargs)
        finally:
            otel_context.detach(token)
            
    return wrapper