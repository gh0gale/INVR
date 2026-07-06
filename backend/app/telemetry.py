import os
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry import trace, context as otel_context
from openinference.instrumentation.langchain import LangChainInstrumentor

def init_telemetry():
    """Initializes OpenTelemetry and LangChain auto-instrumentation."""
    import urllib.request
    import urllib.error
    import logging
    logger = logging.getLogger(__name__)

    # Defaults to local Phoenix or Jaeger collector
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:6060/v1/traces")
    
    # OTLP Collector Health Check
    try:
        # Check base URL / health endpoint if possible, or just parse hostname/port
        from urllib.parse import urlparse
        parsed = urlparse(endpoint)
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((parsed.hostname, parsed.port or 80))
        if result != 0:
            logger.warning(f"OTLP Collector at {endpoint} is offline/unreachable. Traces will be dropped!")
        sock.close()
    except Exception as e:
        logger.warning(f"Failed to verify OTLP Collector health at {endpoint}: {e}")

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