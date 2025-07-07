"""
Phoenix setup for Docker deployment
Uses the Phoenix instance running in Docker container
Fixed async context handling for Google ADK
"""
import os
import logging
import asyncio
from contextvars import ContextVar
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.context import attach, detach, set_value

logger = logging.getLogger(__name__)

# Context var to track async boundaries
_adk_context = ContextVar('adk_context', default=None)

def setup_phoenix_docker():
    """
    Setup Phoenix telemetry for Docker deployment with async context fixes
    """
    try:
        # Set environment variables to handle async context issues
        os.environ["OTEL_PYTHON_CONTEXT"] = "contextvars"
        os.environ["OTEL_PYTHON_ASYNCIO_COROUTINE_CONTEXT_MANAGEMENT"] = "false"
        
        # Create resource with service name from env
        service_name = os.getenv('OTEL_SERVICE_NAME', 'nai-agent')
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "environment": os.getenv('ENVIRONMENT', 'development')
        })
        
        # Configure tracer provider with custom context
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Configure OTLP exporter to Phoenix container
        # Use gRPC exporter for Phoenix (port 4317)
        endpoint = os.getenv('PHOENIX_ENDPOINT', 'http://localhost:4317')
        # Remove http:// prefix if present for gRPC
        if endpoint.startswith('http://'):
            endpoint = endpoint.replace('http://', '')
        elif endpoint.startswith('https://'):
            endpoint = endpoint.replace('https://', '')
            
        otlp_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=os.getenv('OTEL_EXPORTER_OTLP_INSECURE', 'true').lower() == 'true'
        )
        
        # Add batch processor with custom executor for async safety
        span_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            export_timeout_millis=30000
        )
        tracer_provider.add_span_processor(span_processor)
        
        logger.info("✅ Phoenix OTLP telemetry configured")
        logger.info(f"   Endpoint: {endpoint} (gRPC)")
        logger.info(f"   Service: {service_name}")
        
        # Apply async context fix before instrumenting
        apply_async_context_fix()
        
        # Instrument Google ADK with context management disabled
        try:
            instrumentor = GoogleADKInstrumentor()
            # Try to disable context propagation if the option exists
            instrumentor.instrument(set_global_tracer=False)
            logger.info("✅ Google ADK instrumentation enabled with async fixes")
        except Exception as e:
            logger.warning(f"Standard instrumentation failed, applying workaround: {e}")
            # Apply manual instrumentation as fallback
            apply_manual_instrumentation(tracer_provider)
        
        # Verify Phoenix UI is accessible
        logger.info("📊 Phoenix UI: http://localhost:6006")
        
        return tracer_provider
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Phoenix: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def apply_async_context_fix():
    """
    Apply fixes for async context management in OpenTelemetry
    """
    # Monkey-patch the context management to handle async generators
    from opentelemetry import context as otel_context
    
    original_detach = otel_context.detach
    
    def safe_detach(token):
        """Safe detach that ignores context errors"""
        try:
            if token is not None:
                original_detach(token)
        except ValueError as e:
            # Ignore "was created in a different Context" errors
            if "was created in a different Context" not in str(e):
                raise
    
    otel_context.detach = safe_detach
    logger.info("✅ Applied async context fix for OpenTelemetry")

def apply_manual_instrumentation(tracer_provider):
    """
    Apply manual instrumentation for Google ADK as fallback
    """
    try:
        from google.adk import runners
        
        tracer = trace.get_tracer("google.adk", tracer_provider=tracer_provider)
        
        # Store original method
        original_run_async = runners.Runner.run_async
        
        async def instrumented_run_async(self, *args, **kwargs):
            """Instrumented version of run_async that handles contexts properly"""
            user_id = kwargs.get('user_id', 'unknown')
            session_id = kwargs.get('session_id', 'unknown')
            
            # Create a root span that won't interfere with async contexts
            span = tracer.start_span(
                "adk.runner.run",
                attributes={
                    "user.id": user_id,
                    "session.id": session_id,
                    "agent.name": getattr(self.agent, 'name', 'unknown')
                }
            )
            
            try:
                # Don't use context manager to avoid context issues
                async for event in original_run_async(self, *args, **kwargs):
                    yield event
                span.set_status(trace.Status(trace.StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise
            finally:
                span.end()
        
        # Replace method
        runners.Runner.run_async = instrumented_run_async
        logger.info("✅ Applied manual ADK instrumentation")
        
    except Exception as e:
        logger.error(f"Failed to apply manual instrumentation: {e}")