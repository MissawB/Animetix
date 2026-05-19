import pytest
import asyncio
import sys

@pytest.fixture(scope="session", autouse=True)
def set_event_loop_policy():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
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
mock_container_instance.llm_service = MagicMock()
mock_container_instance.catalog_service = MagicMock()
mock_container_instance.blind_test_service = MagicMock()
mock_container_instance.cover_test_service = MagicMock()
mock_container_instance.game_service = MagicMock()

# Setup default returns for services (MUST be serializable types for E2E tests session)
mock_container_instance.catalog_service.load_data.return_value = {
    'titles': ['Naruto'], 
    'lookup': [{'title': 'Naruto', 'id': '1'}], 
    'title_to_full_data': {'Naruto': {'title': 'Naruto', 'id': '1'}},
    'title_to_index': {'Naruto': 0}
}
mock_container_instance.blind_test_service.get_random_theme.return_value = {'anime_title': 'A'}
mock_container_instance.cover_test_service.get_random_cover.return_value = {'manga_title': 'M'}
mock_container_instance.game_service.select_secret.return_value = "Naruto"
mock_container_instance.game_service.select_secret_custom.return_value = "Naruto"

# Patch global get_container
@pytest.fixture(autouse=True)
def patch_get_container(mocker):
    # Force import to ensure attributes exist
    import animetix.containers
    import animetix.services
    try:
        import animetix.views.common
    except ImportError:
        pass

    # Pour les tests E2E, on veut éviter les MagicMocks qui polluent la session Django
    mocker.patch('animetix.containers.get_container', return_value=mock_container_instance)
    mocker.patch('animetix.services.get_container', return_value=mock_container_instance)
    mocker.patch('animetix.tasks.get_container', return_value=mock_container_instance)
    
    # Try to patch views if they are reachable, otherwise skip (core tests don't need them)
    try:
        from animetix.views import common
        mocker.patch.object(common, 'get_container', return_value=mock_container_instance)
        
        from animetix.services import AnimetixService
        mock_service = MagicMock(spec=AnimetixService)
        mock_service.load_data = mock_container_instance.catalog_service.load_data
        mock_service.game_service = mock_container_instance.game_service
        
        mocker.patch.object(common, 'animetix_service', mock_service)
    except (ImportError, AttributeError):
        pass
    
    return mock_container_instance

# --- 2. SIMPLE FIXTURES ---
@pytest.fixture(autouse=True)
def mock_container(patch_get_container):
    """Fixture to provide access to the mock container in tests."""
    return patch_get_container

@pytest.fixture
def mock_animetix_service(mock_container):
    """Legacy compatibility fixture."""
    from animetix.services import AnimetixService
    return AnimetixService()

@pytest.fixture(autouse=True)
def mock_heavy_services(mocker):
# ... code ...

    mocker.patch('requests.post', return_value=MagicMock(
        status_code=200, 
        json=lambda: {"text": "{}", "score": 0.5, "image_url": "http://img", "answer": "Naruto", "ready": True, "reasoning": "R"}
    ))
    mocker.patch('requests.get', return_value=MagicMock(
        status_code=200, 
        json=lambda: {"status": "ok"}
    ))

