"""
OpenTelemetry Instrumentation for Orchestrator System.

Provides distributed tracing, metrics, and logging for production observability.
"""
from typing import Optional, Dict, Any, Callable
from functools import wraps
import time
import logging
from contextlib import asynccontextmanager

try:
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.metrics import Observation
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logging.warning("OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk")

logger = logging.getLogger(__name__)


class OrchestratorInstrumentation:
    """
    Instrumentation for orchestrator operations.
    
    Provides:
    - Distributed tracing with spans
    - Performance metrics (latency, throughput)
    - Error tracking
    - Custom attributes for debugging
    """
    
    def __init__(self, service_name: str = "braintrain-orchestrator"):
        self.service_name = service_name
        
        if OTEL_AVAILABLE:
            self.tracer = trace.get_tracer(__name__)
            self.meter = metrics.get_meter(__name__)
            
            # Create metrics
            self._setup_metrics()
        else:
            self.tracer = None
            self.meter = None
    
    def _setup_metrics(self):
        """Setup OpenTelemetry metrics."""
        
        if not OTEL_AVAILABLE or not self.meter:
            return
        
        # Latency histograms
        self.evaluation_latency = self.meter.create_histogram(
            name="orchestrator.evaluation.latency",
            description="Time taken for answer evaluation",
            unit="ms"
        )
        
        self.turn_decision_latency = self.meter.create_histogram(
            name="orchestrator.turn_decision.latency",
            description="Time taken for turn decision",
            unit="ms"
        )
        
        self.context_assembly_latency = self.meter.create_histogram(
            name="orchestrator.context_assembly.latency",
            description="Time taken for context assembly",
            unit="ms"
        )
        
        self.model_generation_latency = self.meter.create_histogram(
            name="orchestrator.model_generation.latency",
            description="Time taken for model generation",
            unit="ms"
        )
        
        self.knowledge_retrieval_latency = self.meter.create_histogram(
            name="orchestrator.knowledge_retrieval.latency",
            description="Time taken for knowledge retrieval",
            unit="ms"
        )
        
        # Counters
        self.evaluation_counter = self.meter.create_counter(
            name="orchestrator.evaluations.count",
            description="Number of evaluations performed"
        )
        
        self.turn_counter = self.meter.create_counter(
            name="orchestrator.turns.count",
            description="Number of turns processed"
        )
        
        self.model_calls_counter = self.meter.create_counter(
            name="orchestrator.model_calls.count",
            description="Number of model API calls"
        )
        
        self.fallback_counter = self.meter.create_counter(
            name="orchestrator.fallbacks.count",
            description="Number of fallbacks triggered"
        )
        
        # Gauges (via observable gauges)
        self.active_sessions = self.meter.create_up_down_counter(
            name="orchestrator.active_sessions",
            description="Number of active interview sessions"
        )
    
    @asynccontextmanager
    async def trace_operation(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracing async operations.
        
        Usage:
            async with instrumentation.trace_operation("evaluate_answer", {...}):
                result = await evaluate_answer(...)
        """
        
        if not OTEL_AVAILABLE or not self.tracer:
            # No-op if OpenTelemetry not available
            yield None
            return
        
        with self.tracer.start_as_current_span(
            operation_name,
            kind=SpanKind.INTERNAL
        ) as span:
            start_time = time.time()
            
            # Add attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
            
            finally:
                latency_ms = (time.time() - start_time) * 1000
                span.set_attribute("latency_ms", latency_ms)
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Record a metric value."""
        
        if not OTEL_AVAILABLE or not self.meter:
            return
        
        attrs = attributes or {}
        
        # Route to appropriate metric
        if metric_name == "evaluation_latency":
            self.evaluation_latency.record(value, attrs)
        elif metric_name == "turn_decision_latency":
            self.turn_decision_latency.record(value, attrs)
        elif metric_name == "context_assembly_latency":
            self.context_assembly_latency.record(value, attrs)
        elif metric_name == "model_generation_latency":
            self.model_generation_latency.record(value, attrs)
        elif metric_name == "knowledge_retrieval_latency":
            self.knowledge_retrieval_latency.record(value, attrs)
    
    def increment_counter(
        self,
        counter_name: str,
        value: int = 1,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Increment a counter."""
        
        if not OTEL_AVAILABLE or not self.meter:
            return
        
        attrs = attributes or {}
        
        if counter_name == "evaluations":
            self.evaluation_counter.add(value, attrs)
        elif counter_name == "turns":
            self.turn_counter.add(value, attrs)
        elif counter_name == "model_calls":
            self.model_calls_counter.add(value, attrs)
        elif counter_name == "fallbacks":
            self.fallback_counter.add(value, attrs)
    
    def update_active_sessions(self, delta: int, attributes: Optional[Dict[str, Any]] = None):
        """Update active sessions count."""
        
        if not OTEL_AVAILABLE or not self.meter:
            return
        
        self.active_sessions.add(delta, attributes or {})


# Singleton instance
_instrumentation: Optional[OrchestratorInstrumentation] = None


def get_instrumentation() -> OrchestratorInstrumentation:
    """Get singleton instrumentation instance."""
    global _instrumentation
    
    if _instrumentation is None:
        _instrumentation = OrchestratorInstrumentation()
    
    return _instrumentation


def trace_orchestrator_operation(operation_name: str):
    """
    Decorator for tracing orchestrator operations.
    
    Usage:
        @trace_orchestrator_operation("evaluate_answer")
        async def evaluate_answer(...):
            ...
    """
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            instrumentation = get_instrumentation()
            
            # Extract session_id if available
            attributes = {}
            if "session_id" in kwargs:
                attributes["session_id"] = kwargs["session_id"]
            
            async with instrumentation.trace_operation(operation_name, attributes):
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def setup_otel_exporter(
    endpoint: Optional[str] = None,
    service_name: str = "braintrain-orchestrator",
    environment: str = "development"
):
    """
    Setup OpenTelemetry exporters.
    
    Args:
        endpoint: OTLP endpoint (e.g., "http://localhost:4318")
        service_name: Service name for tracing
        environment: Environment (development, staging, production)
    
    Example:
        setup_otel_exporter(
            endpoint="http://localhost:4318",
            service_name="braintrain-orchestrator",
            environment="production"
        )
    """
    
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available. Skipping exporter setup.")
        return
    
    try:
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: service_name,
            DEPLOYMENT_ENVIRONMENT: environment,
            "service.version": "1.0.0",
            "service.namespace": "interview-platform"
        })
        
        # Setup tracing
        if endpoint:
            trace_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
            trace_provider = TracerProvider(resource=resource)
            trace_provider.add_span_processor(
                BatchSpanProcessor(trace_exporter)
            )
            trace.set_tracer_provider(trace_provider)
            
            logger.info(f"OpenTelemetry tracing configured: endpoint={endpoint}")
        
        # Setup metrics
        if endpoint:
            metric_exporter = OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics")
            metric_reader = PeriodicExportingMetricReader(
                metric_exporter,
                export_interval_millis=60000  # Export every 60 seconds
            )
            metric_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader]
            )
            metrics.set_meter_provider(metric_provider)
            
            logger.info(f"OpenTelemetry metrics configured: endpoint={endpoint}")
    
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry exporters: {e}", exc_info=True)


# Example integration points for existing orchestrators
class InstrumentedMixin:
    """Mixin to add instrumentation to orchestrators."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instrumentation = get_instrumentation()
    
    async def _trace_and_record(
        self,
        operation_name: str,
        operation_func: Callable,
        metric_name: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute operation with tracing and metrics."""
        
        async with self.instrumentation.trace_operation(operation_name, attributes) as span:
            start_time = time.time()
            
            try:
                result = await operation_func()
                
                # Record latency
                latency_ms = (time.time() - start_time) * 1000
                self.instrumentation.record_metric(metric_name, latency_ms, attributes)
                
                if span:
                    span.set_attribute("success", True)
                
                return result
            
            except Exception as e:
                if span:
                    span.set_attribute("success", False)
                    span.set_attribute("error", str(e))
                raise


if __name__ == "__main__":
    # Example usage
    print("OpenTelemetry Instrumentation for Orchestrators")
    print(f"Available: {OTEL_AVAILABLE}")
    
    if OTEL_AVAILABLE:
        # Setup with Jaeger (example)
        setup_otel_exporter(
            endpoint="http://localhost:4318",
            service_name="braintrain-orchestrator",
            environment="development"
        )
        
        print("Instrumentation configured!")
        print("Run Jaeger: docker run -d -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one:latest")
        print("View traces: http://localhost:16686")
    else:
        print("Install OpenTelemetry: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
