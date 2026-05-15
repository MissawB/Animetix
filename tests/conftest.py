import pytest
import os
from unittest.mock import MagicMock

# --- 1. MOCK HEAVY LIBRARIES ---
# We use a simple mocking strategy that doesn't trigger Django registration.
class MockPackage(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__path__ = []

import sys
for pkg in [
    'sentence_transformers', 'chromadb', 'chromadb.utils', 
    'chromadb.utils.embedding_functions', 'chromadb.api', 
    'chromadb.api.rust', 'chromadb.config', 'google.colab',
    'neo4j', 'pipeline.neo4j_client', 'z3', 'peft', 'torch',
    'sentry_sdk', 'sentry_sdk.integrations', 'sentry_sdk.integrations.django',
    'transformers', 'datasets', 'bleach', 'jwt', 'wandb'
]:
    sys.modules[pkg] = MockPackage()

# Force Mock Container Module
mock_container_instance = MagicMock()
mock_container_module = MagicMock()
mock_container_module.get_container.return_value = mock_container_instance
sys.modules['animetix.containers'] = mock_container_module

# --- 2. SIMPLE FIXTURES ---
@pytest.fixture(autouse=True)
def mock_heavy_services(mocker):
    mocker.patch('requests.post', return_value=MagicMock(
        status_code=200, 
        json=lambda: {"text": "{}", "score": 0.5, "image_url": "http://img", "answer": "Naruto", "ready": True, "reasoning": "R"}
    ))
    mocker.patch('requests.get', return_value=MagicMock(
        status_code=200, 
        json=lambda: {"status": "ok"}
    ))

@pytest.fixture(autouse=True)
def mock_animetix_service(mocker):
    # Mocking services directly
    mock_instance = MagicMock()
    mocker.patch('animetix.views.AnimetixService', return_value=mock_instance)
    mocker.patch('animetix.services.AnimetixService', return_value=mock_instance)
    mocker.patch('animetix.api_views.AnimetixService', return_value=mock_instance)
    mocker.patch('animetix.schema.AnimetixService', return_value=mock_instance)
    return mock_instance
