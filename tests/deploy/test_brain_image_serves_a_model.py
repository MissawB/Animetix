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


def test_the_model_the_code_asks_for_is_actually_in_the_image():
    """Ollama 404s on an unknown tag, and downstream that reads as "the whole brain
    is offline" -- exactly how prod broke (`qwen3.5` asked for, `qwen3.5:9b` baked).
    The image carries two tags now (the fine-tune and its control); the code must
    name one of them."""
    baked = {
        m.group(1)
        for m in re.finditer(r"ARG (?:OLLAMA_MODEL|CONTROL_MODEL)=(\S+)", DOCKERFILE)
    }
    assert baked, "the model must be baked in, not pulled at cold start"

    assert LLM_OLLAMA_MODEL in baked, (
        f"the code asks for {LLM_OLLAMA_MODEL!r} (core.utils.local_models."
        f"LLM_OLLAMA_MODEL) but the image only registers {sorted(baked)}"
    )


def test_ollama_is_pinned_to_a_version_the_cloud_run_driver_supports():
    """Cloud Run ships NVIDIA driver 535. Ollama >= ~0.6 demands 550+, refuses the
    L4 and silently falls back to CPU (4 tok/s). Unpinning this re-breaks the GPU
    with no error anywhere -- only a slow model."""
    pin = re.search(r"ARG OLLAMA_VERSION=(\S+)", DOCKERFILE)
    assert pin, "Ollama must be version-pinned: the latest rejects driver 535"

    major, minor = (int(p) for p in pin.group(1).split(".")[:2])
    assert (major, minor) <= (0, 5), (
        f"Ollama {pin.group(1)} likely requires driver 550+, which Cloud Run does "
        "not provide; the GPU would fall back to CPU"
    )


def test_the_served_model_is_the_fine_tune_not_a_stock_one():
    """The point of the brain is to serve OUR model. The LoRA must be merged into
    the base its adapter_config actually names -- grafting it onto another base is
    impossible, and that mismatch is why it went unserved for so long."""
    assert "peft" in DOCKERFILE and "merge_and_unload" in DOCKERFILE
    assert "MissawB/otaku-qwen-7b-adapter" in DOCKERFILE
    assert "unsloth/Qwen2.5-7B-Instruct" in DOCKERFILE
    assert "llama-quantize" in DOCKERFILE, "serving fp16 would not fit the L4"


def test_weights_are_baked_before_the_source_copy():
    """The GGUF layer is expensive to produce; a code change must not invalidate it."""
    assert DOCKERFILE.index("ollama create") < DOCKERFILE.index("COPY . .")


def test_model_server_is_started_and_awaited_before_the_api():
    """uvicorn taking traffic before Ollama answers = /health "offline" on every
    cold start, and the router drops the brain for the whole health-TTL window."""
    # Le CMD exec final (`CMD [...]`), pas le premier `CMD ` du dépôt : depuis
    # l'ajout du HEALTHCHECK (`HEALTHCHECK ... CMD curl .../health`), `"CMD "`
    # apparaît AVANT le vrai CMD, et la tranche captait le commentaire « uvicorn
    # takes traffic » -- « uvicorn » y précédait « ollama serve », d'où un faux
    # négatif. Le CMD exec est le seul au format `CMD [`.
    cmd = DOCKERFILE[DOCKERFILE.index("CMD [") :]

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
