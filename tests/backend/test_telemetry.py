import pytest
from unittest.mock import MagicMock
from django.test import RequestFactory
from django.http import HttpResponse
from animetix.telemetry import inject_trace_context, extract_trace_context
from animetix.middleware import TracingMiddleware


@pytest.fixture
def rf():
    return RequestFactory()


def test_telemetry_inject_extract_context():
    from opentelemetry import trace  # noqa: E402

    tracer = trace.get_tracer("test-tracer")

    headers = {}
    with tracer.start_as_current_span("parent-span"):
        inject_trace_context(headers)

    assert "traceparent" in headers

    # Extract trace context
    extracted_context = extract_trace_context(headers)
    assert extracted_context is not None


def test_tracing_middleware_creates_span(rf):
    request = rf.get("/explore/")
    # Mock trace context
    request.META["HTTP_TRACEPARENT"] = (
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    )

    middleware = TracingMiddleware(lambda req: HttpResponse("OK"))

    # Directly mock the tracer instance on the middleware
    mock_tracer = MagicMock()
    middleware.tracer = mock_tracer

    middleware(request)
    mock_tracer.start_as_current_span.assert_called_once()

    # Verify it passed the custom context from HTTP_TRACEPARENT
    call_args = mock_tracer.start_as_current_span.call_args
    assert call_args[0][0] == "HTTP GET /explore/"
    assert "context" in call_args[1]
