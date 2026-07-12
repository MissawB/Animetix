"""The brain image must actually run a model server at LLM_API_BASE.

`brain_service` builds its engine as an OpenAI-compatible client against
LLM_API_BASE (default http://localhost:11434/v1) and exposes /health as that
engine's health. For the life of the project the image ran NO server on that
port: the L4 GPU sat idle, every text generation failed, /health answered
{"status":"offline"} and the web router wrote the whole brain off -- which is how
production ended up loading a 3B model into the 4 GiB web container instead.

These assertions are about the CONTRACT between the code and the image, which no
unit test can reach: the port the client dials, and the server the image starts.
"""

import re
from pathlib import Path

import yaml
from core.utils.local_models import LLM_OLLAMA_MODEL

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = (REPO_ROOT / "deploy" / "Dockerfile.brain").read_text(encoding="utf-8")
CLOUDBUILD = yaml.safe_load(
    (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8-sig")
)


def test_image_installs_a_model_server():
    assert "ollama.com/install.sh" in DOCKERFILE, (
        "brain_service dials LLM_API_BASE for every generation; without a model "
        "server in the image nothing listens there and the GPU is dead weight"
    )


def test_baked_model_matches_the_model_the_code_asks_for():
    """The image bakes one model; the engine requests another -> `model not found`."""
    baked = re.search(r"ARG OLLAMA_MODEL=(\S+)", DOCKERFILE)
    assert baked, "the model must be baked in, not pulled at cold start"

    assert baked.group(1) == LLM_OLLAMA_MODEL, (
        f"image bakes {baked.group(1)!r} but the code asks for "
        f"{LLM_OLLAMA_MODEL!r} (core.utils.local_models.LLM_OLLAMA_MODEL)"
    )


def test_weights_are_baked_before_the_source_copy():
    """A 6.6 GB layer must not be invalidated by every code change."""
    assert DOCKERFILE.index("ollama pull") < DOCKERFILE.index("COPY . .")


def test_model_server_is_started_and_awaited_before_the_api():
    """uvicorn taking traffic before Ollama answers = /health "offline" on every
    cold start, and the router drops the brain for the whole health-TTL window."""
    cmd = DOCKERFILE[DOCKERFILE.index("CMD ") :]

    assert "ollama serve" in cmd, "the model server must run alongside the API"
    assert "/api/tags" in cmd, "the API must wait for the model server to answer"
    assert cmd.index("ollama serve") < cmd.index("uvicorn")


def test_ollama_host_matches_the_port_the_engine_dials():
    """OLLAMA_HOST and LLM_API_BASE must agree, or the client dials a dead port."""
    assert "OLLAMA_HOST=127.0.0.1:11434" in DOCKERFILE


def test_cloudbuild_can_actually_build_the_image():
    """Default Cloud Build = 10 min deadline and a 100 GB disk; this image is
    ~13 GB and spends minutes pulling weights. The defaults fail it."""
    assert CLOUDBUILD["timeout"] != "600s"
    assert int(CLOUDBUILD["timeout"].rstrip("s")) >= 1800

    options = CLOUDBUILD["options"]
    assert int(options["diskSizeGb"]) >= 150
