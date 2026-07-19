"""Guards for the `.env.example` template.

Audit dette 2026-07-19: the template had drifted ~18 keys behind what the
code actually reads (GEMINI_API_KEY, TMDB_API_KEY, IGDB_*, HF_TOKEN, ...) —
onboarding from the example produced a `.env` the app could not run on.

Two invariants:
1. every env key the code load-bears on is documented in the template;
2. the template never carries a real-looking secret value (placeholders only).
"""

import re
from pathlib import Path

import pytest

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"

# Keys consumed by settings/adapters/deploy scripts that a developer must be
# able to discover from the template. Source of truth: grep of
# os.environ/os.getenv/env() over backend/ + scripts/ (2026-07-19).
REQUIRED_KEYS = [
    # Django core
    "DJANGO_ENV",
    "DJANGO_DEBUG",
    "DJANGO_SECRET_KEY",
    "ALLOWED_HOSTS",
    # Stores
    "DATABASE_URL",
    "REDIS_URL",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    # Brain / LLM
    "BRAIN_API_URL",
    "BRAIN_API_KEY",
    "LLM_API_KEY",
    "LLM_MODEL_NAME",
    "LOCAL_MODEL_ID",
    # AI providers
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "COHERE_API_KEY",
    "TAVILY_API_KEY",
    # Media catalogs
    "TMDB_API_KEY",
    "IGDB_CLIENT_ID",
    "IGDB_CLIENT_SECRET",
    # Hugging Face / MLOps
    "HF_TOKEN",
    "HUGGINGFACE_API_KEY",
    "HF_SPACES",
    "WANDB_API_KEY",
    # Observability
    "SENTRY_DSN",
    # Manga server
    "SUWAYOMI_URL",
    "SUWAYOMI_PASSWORD",
    # Gemini model roles
    "ANIMETIX_GEMINI_MODEL",
    "ANIMETIX_GEMINI_LIVE_MODEL",
    "ANIMETIX_GEMINI_EMBEDDING_MODEL",
]

# Value shapes that only ever appear in *real* credentials, never placeholders.
SECRET_VALUE_PATTERNS = [
    r"AIza[0-9A-Za-z_-]{30,}",  # Google API key
    r"hf_[A-Za-z0-9]{30,}",  # Hugging Face token
    r"(sk|pk|cs)_(test|live)_[A-Za-z0-9]{24,}",  # Stripe
    r"tsk_[A-Za-z0-9]{30,}",  # Tripo
    r"wandb_v1_[A-Za-z0-9_-]{30,}",  # W&B service token
    r"postgres(ql)?://\w+:[^@\s]{8,}@(?!db:|localhost|127\.0\.0\.1)",  # real DB creds
    r"npg_[A-Za-z0-9]{8,}",  # Neon password prefix
]


@pytest.fixture(scope="module")
def example_keys():
    keys = set()
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.add(line.split("=", 1)[0].strip())
    return keys


def test_env_example_documents_every_load_bearing_key(example_keys):
    missing = [k for k in REQUIRED_KEYS if k not in example_keys]
    assert not missing, f".env.example is missing documented keys: {missing}"


def test_env_example_contains_no_real_secret_values():
    content = ENV_EXAMPLE.read_text(encoding="utf-8")
    hits = [p for p in SECRET_VALUE_PATTERNS if re.search(p, content)]
    assert not hits, f".env.example carries real-looking credentials: {hits}"
