"""Le safety_engine du guardrail doit parler à un backend qui existe.

Il était câblé sur l'UnifiedInferenceAdapter, qui pointe sur localhost:11434 --
adresse où rien n'écoute dans le conteneur web (ni LLM_API_BASE ni LLM_MODEL_NAME
n'y sont définis). Chaque modération payait donc un appel voué à l'échec avant de
retomber sur le gros modèle.
"""

import re
from pathlib import Path

CONTAINER = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "api"
    / "animetix"
    / "containers"
    / "inference.py"
)


def _provider_block(name: str) -> str:
    source = CONTAINER.read_text(encoding="utf-8")
    match = re.search(
        rf"^    {name} = providers\.Singleton\((.*?)^    \)", source, re.M | re.S
    )
    assert match, f"provider {name} not found in inference.py"
    return match.group(1)


def test_local_guardrail_is_wired_to_the_brain_not_to_localhost():
    block = _provider_block("local_guardrail_adapter")
    assert "brain_guardrail_adapter" in block
    assert "unified_inference_adapter" not in block


def test_brain_guardrail_adapter_is_pinned_to_the_guardrail_role():
    block = _provider_block("brain_guardrail_adapter")
    assert "GUARDRAIL_OLLAMA_MODEL" in block
