"""The brain can only serve a tag its own image registered with Ollama.

Ollama 404s on an unknown tag, and that 404 is invisible: ``health_check`` in
``unified_inference_adapter`` probes ``/api/tags`` for *reachability* and never
checks that ``model_name`` is in the returned list, so a mismatch reports
"online" while every generation fails. Prod ran that way -- the deployed
revision (image ``brain:af7d7e7f``, which bakes ``otaku-qwen:7b`` and
``qwen2.5:7b-instruct``) was pinned to ``qwen3.5:9b`` by ``deployments.yaml``.

``test_no_hardcoded_local_model.py`` could not catch it: it only scans
``backend/**/*.py``, and the drift lived in a YAML manifest. So this guard pins
the two places a served tag can come from -- the deploy manifest and the role
constant -- to the tags ``Dockerfile.brain`` actually bakes.
"""

import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "deploy" / "Dockerfile.brain"
DEPLOYMENTS = ROOT / "deploy" / "deployments.yaml"
LOCAL_MODELS = ROOT / "backend" / "core" / "utils" / "local_models.py"

# `ollama create $OLLAMA_MODEL` and `ollama pull $CONTROL_MODEL` are the only two
# tags the image registers; both read their value from these ARG defaults.
BAKED_ARGS = ("OLLAMA_MODEL", "CONTROL_MODEL")


def _baked_tags() -> set[str]:
    text = DOCKERFILE.read_text(encoding="utf-8")
    tags = set()
    for arg in BAKED_ARGS:
        match = re.search(rf"^ARG {arg}=(?P<tag>\S+)", text, re.MULTILINE)
        assert match, f"ARG {arg} vanished from Dockerfile.brain"
        tags.add(match.group("tag"))
    return tags


def test_brain_manifest_does_not_pin_an_unbaked_tag():
    brain_env = yaml.safe_load(DEPLOYMENTS.read_text(encoding="utf-8"))["gcp_services"][
        "brain"
    ]["env_vars"]
    pinned = brain_env.get("LLM_MODEL_NAME")
    if pinned is None:
        return  # No override: the role constant decides, covered by the test below.
    assert pinned in _baked_tags(), (
        f"deployments.yaml pins LLM_MODEL_NAME={pinned!r}, which Dockerfile.brain "
        f"never registers with Ollama (baked: {sorted(_baked_tags())}). The brain "
        "would 404 on every generation while /health still reported online."
    )


def test_local_models_default_tag_is_baked():
    # Read the literal rather than importing: a developer's LLM_MODEL_NAME must
    # not decide whether this guard passes.
    match = re.search(
        r'LLM_OLLAMA_MODEL = os\.getenv\(\s*"LLM_MODEL_NAME",\s*"(?P<tag>[^"]+)"',
        LOCAL_MODELS.read_text(encoding="utf-8"),
    )
    assert match, "LLM_OLLAMA_MODEL default no longer matches the expected shape"
    default = match.group("tag")
    assert default in _baked_tags(), (
        f"local_models.LLM_OLLAMA_MODEL defaults to {default!r}, which "
        f"Dockerfile.brain does not bake (baked: {sorted(_baked_tags())})."
    )
