import pytest
from core.brain import app
from fastapi.testclient import TestClient
import os
from unittest.mock import patch

client = TestClient(app)

def test_health_check_api_mode():
    """Vérifie que le health check indique le mode Fallback si aucun modèle n'est chargé."""
    # On s'assure que le modèle est None pour ce test
    with patch("core.brain.model", None):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "online"
        assert response.json()["engine"] == "Fallback-API"

def test_health_check_local_mode():
    """Vérifie que le health check indique le mode Local si un modèle est chargé."""
    with patch("core.brain.model", "MockModel"):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["engine"] == "Animetix-Expert-Local"

@patch("requests.post")
def test_generate_fallback_huggingface(mock_post):
    """Vérifie que l'API bascule sur Hugging Face en cas d'absence de modèle local."""
    # Configurer le mock pour simuler une réponse de Hugging Face
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = [{"generated_text": "<|assistant|>\nVoici une réponse d'expert."}]
    
    # Simuler l'absence de modèle local et présence de token
    with patch("core.brain.model", None), \
         patch.dict(os.environ, {"HF_TOKEN": "mock_token"}):
        
        response = client.post("/generate", json={
            "prompt": "Qui est Naruto ?",
            "system_prompt": "Expert mode"
        })
        
        assert response.status_code == 200
        assert "Voici une réponse d'expert" in response.json()["text"]
        assert mock_post.called

def test_generate_no_provider_available():
    """Vérifie le message d'erreur si aucun provider (local ou API) n'est dispo."""
    with patch("core.brain.model", None), \
         patch.dict(os.environ, {}, clear=True):
        
        response = client.post("/generate", json={"prompt": "test"})
        assert response.status_code == 200
        assert "aucune unité de calcul d'IA n'est disponible" in response.json()["text"]
