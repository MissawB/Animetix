from prometheus_client import Gauge

# --- Archetype Drift Metrics ---
ARCHETYPE_DRIFT_INTENSITY = Gauge(
    "animetix_mlops_archetype_drift_intensity",
    "Intensity of the user archetype drift",
    ["user_id", "archetype_id"],
)

# --- Reasoning Model Stability Metrics ---
MODEL_REASONING_CONFIDENCE = Gauge(
    "animetix_mlops_reasoning_stability_confidence",
    "Confidence score of the reasoning model reasoning",
)

MODEL_REASONING_ENTROPY = Gauge(
    "animetix_mlops_reasoning_stability_entropy",
    "Average entropy of the reasoning model output tokens",
)

MODEL_REASONING_PERPLEXITY = Gauge(
    "animetix_mlops_reasoning_stability_perplexity",
    "Perplexity of the reasoning model output",
)
