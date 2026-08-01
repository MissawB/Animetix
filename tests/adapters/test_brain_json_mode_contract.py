"""Le décodage contraint doit survivre au passage web -> brain -> moteur.

La modération du guardrail demande `json_mode=True`. Trois maillons peuvent le
perdre en silence, et aucun ne le signale : `BrainAPIAdapter` le range dans le
payload via `**kwargs`, Pydantic JETTE tout champ non déclaré sur
`GenerateRequest`, et l'endpoint doit encore le repasser au moteur. Un maillon
manquant ne casse rien de visible : le modèle génère alors à température 0.7
sans `response_format`, rend de la prose une fois sur N, et une modération
illisible est une modération sautée.
"""

import os
from unittest.mock import MagicMock, patch

from adapters.inference.brain_api_adapter import BrainAPIAdapter
from fastapi.testclient import TestClient

# brain_service.py appelle sys.exit(1) à l'import si BRAIN_API_KEY manque.
os.environ.setdefault("BRAIN_API_KEY", "test-env-key-12345")

from adapters.inference.brain_service import (  # noqa: E402
    GenerateRequest,
    app,
    brain_engine,
    verify_api_key,
)


def _sent_payload(**kwargs) -> dict:
    """Le corps HTTP réellement construit par l'adaptateur web."""
    adapter = BrainAPIAdapter(api_url="http://brain:5000", api_key="k")
    response = MagicMock()
    response.json.return_value = {"text": "{}", "usage": {}}
    with patch(
        "adapters.inference.brain_api_adapter.safe_http_request",
        return_value=response,
    ) as req:
        adapter.generate("prompt", "system", **kwargs)
    return req.call_args.kwargs["json"]


def test_the_adapter_puts_json_mode_in_the_payload():
    assert _sent_payload(json_mode=True)["json_mode"] is True


def test_the_brain_schema_keeps_json_mode_instead_of_dropping_it():
    # Le maillon silencieux : un champ non déclaré sur le modèle Pydantic
    # disparaît sans erreur, et l'appelant croirait avoir contraint la sortie.
    parsed = GenerateRequest(**_sent_payload(json_mode=True))
    assert parsed.json_mode is True

    # Et l'absence du champ reste le comportement historique (texte libre).
    assert GenerateRequest(**_sent_payload()).json_mode is False


def test_the_generate_endpoint_forwards_json_mode_to_the_engine(monkeypatch):
    app.dependency_overrides[verify_api_key] = lambda: "test-env-key-12345"
    seen = {}

    class _Res:
        text = "{}"
        metadata = None

    def _generate(*args, **kwargs):
        seen.update(kwargs)
        return _Res()

    monkeypatch.setattr(brain_engine, "generate", _generate)
    try:
        res = TestClient(app).post(
            "/generate",
            json={"prompt": "p", "json_mode": True},
            headers={"X-API-Key": "test-env-key-12345"},
        )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    assert seen.get("json_mode") is True
