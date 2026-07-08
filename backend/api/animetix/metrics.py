from prometheus_client import REGISTRY, Gauge


def _gauge(name, documentation, labelnames=()):
    """Idempotent Gauge factory.

    Prometheus registers every metric on a process-global default registry and
    raises ``ValueError: Duplicated timeseries in CollectorRegistry`` if the same
    name is registered twice. That happens whenever this module is imported a
    second time in one process — e.g. a test that ``importlib.reload``s a module
    which transitively imports this one. Returning the already-registered
    collector makes re-import a no-op instead of a crash, so metric-consuming
    tests stop failing based on suite import order.
    """
    existing = REGISTRY._names_to_collectors.get(name)
    if existing is not None:
        return existing
    return Gauge(name, documentation, labelnames)


# --- Archetype Drift Metrics ---
ARCHETYPE_DRIFT_INTENSITY = _gauge(
    "animetix_mlops_archetype_drift_intensity",
    "Intensity of the user archetype drift",
    ["user_id", "archetype_id"],
)

# --- Reasoning Model Stability Metrics ---
MODEL_REASONING_CONFIDENCE = _gauge(
    "animetix_mlops_reasoning_stability_confidence",
    "Confidence score of the reasoning model reasoning",
)

MODEL_REASONING_ENTROPY = _gauge(
    "animetix_mlops_reasoning_stability_entropy",
    "Average entropy of the reasoning model output tokens",
)

MODEL_REASONING_PERPLEXITY = _gauge(
    "animetix_mlops_reasoning_stability_perplexity",
    "Perplexity of the reasoning model output",
)
