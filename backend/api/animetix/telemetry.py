import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger("animetix.telemetry")


def init_telemetry(service_name: str):
    """
    Initializes Google Cloud Profiler and OpenTelemetry tracing.
    """
    # 1. Start Google Cloud Profiler in production
    if os.getenv("DJANGO_ENV") == "production":
        try:
            import googlecloudprofiler  # noqa: E402

            googlecloudprofiler.start(
                service=service_name,
                verbose=2,
            )
            logger.info(f"✅ Google Cloud Profiler started for service: {service_name}")
        except Exception as e:
            logger.warning(f"Could not start Google Cloud Profiler: {e}")

    # 2. Setup OpenTelemetry Tracer Provider
    try:
        provider = TracerProvider(
            resource=Resource.create({"service.name": service_name})
        )
        trace.set_tracer_provider(provider)

        if os.getenv("DJANGO_ENV") == "production":
            from opentelemetry.exporter.gcp.trace import CloudTraceSpanExporter  # noqa: E402

            exporter = CloudTraceSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                f"✅ OpenTelemetry CloudTraceSpanExporter configured for: {service_name}"
            )
        else:
            logger.info("ℹ️ Telemetry initialized in local dev mode (no exporter).")

    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry: {e}")


def inject_trace_context(headers: dict):
    """Injects current W3C trace context into target headers dictionary."""
    TraceContextTextMapPropagator().inject(headers)


def extract_trace_context(headers: dict):
    """Extracts W3C trace context from incoming request headers."""
    return TraceContextTextMapPropagator().extract(headers)
