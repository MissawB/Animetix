import os

from fastapi.testclient import TestClient

os.environ["BRAIN_API_KEY"] = "test-env-key-12345"

from adapters.inference.brain_api import app, brain_engine, verify_api_key  # noqa: E402

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200


def test_unauthenticated_generate():
    response = client.post("/generate", json={"prompt": "test"})
    assert response.status_code == 401


def test_authenticated_generate(monkeypatch):
    # Override de la dépendance de clé d'API
    app.dependency_overrides[verify_api_key] = lambda: "test-env-key-12345"

    # Mock de UnifiedInferenceAdapter.generate
    class MockInferenceResponse:
        text = "Hello world"
        metadata = None

    monkeypatch.setattr(
        brain_engine, "generate", lambda *args, **kwargs: MockInferenceResponse()
    )

    response = client.post(
        "/generate",
        json={"prompt": "Bonjour"},
        headers={"X-API-Key": "test-env-key-12345"},
    )
    assert response.status_code == 200
    assert response.json()["text"] == "Hello world"

    # Nettoyage des overrides
    app.dependency_overrides.clear()
