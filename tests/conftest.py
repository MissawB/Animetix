import pytest
import asyncio
import sys
import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import os
from unittest.mock import MagicMock

class MockPackage(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__path__ = []

    def __getattr__(self, name):
        if name == 'Image':
            from PIL import Image
            return Image
        if name == 'ImageColor':
            from PIL import ImageColor
            return ImageColor
        if name == 'ImageFile':
            from PIL import ImageFile
            return ImageFile
        if name and name[0].isupper():
            # Dynamically create a class to prevent issubclass() and subclassing errors
            mock_cls = type(name, (object,), {
                "__getattr__": lambda s, attr: MagicMock(),
                "__init__": lambda *a, **k: None,
            })
            setattr(self, name, mock_cls)
            return mock_cls
        return super().__getattr__(name)

import sys
import pytest

@pytest.fixture(autouse=False)
def mock_heavy_packages(monkeypatch):
    """Provide on‑demand mocks for heavy optional packages.
    Tests that need a specific package can call this fixture and
    monkeypatch the module name to a ``MockPackage`` instance.
    """
    from tests.conftest import MockPackage
    packages = [
        'sentence_transformers', 'chromadb', 'chromadb.utils',
        'chromadb.utils.embedding_functions', 'chromadb.api',
        'chromadb.api.rust', 'chromadb.config', 'google.colab',
        'neo4j', 'pipeline.neo4j_client', 'z3', 'peft', 'torch',
        'sentry_sdk', 'sentry_sdk.integrations', 'sentry_sdk.integrations.django',
        'transformers', 'datasets', 'bleach', 'jwt', 'wandb'
    ]
    for pkg in packages:
        monkeypatch.setitem(sys.modules, pkg, MockPackage())
    return True
# Force Mock Container Module
mock_container_instance = MagicMock()
mock_container_instance.llm_service = MagicMock()
mock_container_instance.catalog_service = MagicMock()
mock_container_instance.blind_test_service = MagicMock()
mock_container_instance.cover_test_service = MagicMock()
mock_container_instance.game_service = MagicMock()
mock_container_instance.akinetix_service = MagicMock()
mock_container_instance.animinator_service = MagicMock()
mock_container_instance.vision_quest_service = MagicMock()
mock_container_instance.uncertainty_service = MagicMock()
mock_container_instance.graph_persistence_port = MagicMock()

# Setup default returns for services (MUST be serializable types for E2E tests session)
mock_container_instance.catalog_service.load_data.return_value = {
    'titles': ['Naruto', 'Bleach'], 
    'lookup': [{'title': 'Naruto', 'id': '1'}, {'title': 'Bleach', 'id': '2'}], 
    'title_to_full_data': {
        'Naruto': {'title': 'Naruto', 'id': '1', 'image': 'n.jpg'},
        'Bleach': {'title': 'Bleach', 'id': '2', 'image': 'b.jpg'}
    },
    'title_to_index': {'Naruto': 0, 'Bleach': 1}
}
mock_container_instance.blind_test_service.get_random_theme.return_value = {
    'anime_title': 'A', 'song_title': 'S', 'artists': 'Art', 'video_url': 'v.mp4', 'type': 'OP'
}
mock_container_instance.cover_test_service.get_random_cover.return_value = {
    'manga_title': 'M', 'cover_url': 'c.jpg', 'locale': 'ja', 'volume': '1'
}
mock_container_instance.game_service.select_secret.return_value = "Naruto"
mock_container_instance.game_service.select_secret_custom.return_value = "Naruto"
mock_container_instance.game_service.check_title_match.return_value = False
mock_container_instance.game_service.calculate_raw_similarity.return_value = 0.5
mock_container_instance.game_service.check_title_match.return_value = False
mock_container_instance.akinetix_service.start_new_game.return_value = {
    'history': [], 'current_q': 'Q?', 'current_attr': 'A', 'game_over': False, 'ai_guess': None, 'probs': {}, 'asked_attrs': []
}
mock_container_instance.akinetix_service.process_answer.return_value = {
    'history': [], 'current_q': 'Q2?', 'current_attr': 'A2', 'game_over': False, 'ai_guess': None, 'probs': {}, 'asked_attrs': []
}
mock_container_instance.animinator_service.select_secret.return_value = "Naruto"
mock_container_instance.animinator_service.start_new_game.return_value = {
    'history': [], 'current_q': 'Q?', 'current_attr': 'A', 'game_over': False, 'ai_guess': None, 'probs': {}, 'asked_attrs': []
}
mock_container_instance.animinator_service.process_question.return_value = {
    'history': [], 'current_q': 'Q2?', 'current_attr': 'A2', 'game_over': False, 'ai_guess': None, 'probs': {}, 'asked_attrs': [], 'answer': 'yes'
}
mock_container_instance.animinator_service.ask_oracle.return_value = {
    'answer': 'Oui', 'reasoning': 'Oracle reason'
}
mock_container_instance.vision_quest_service.select_secret.return_value = {'id': 1, 'title': 'Naruto', 'image': 'n.jpg'}
mock_container_instance.vision_quest_service.start_new_game.return_value = {'id': 1, 'title': 'Naruto', 'image': 'n.jpg'}

# Set the global container early to prevent import-time real instantiations
try:
    import animetix.containers
    animetix.containers._container = mock_container_instance
except ImportError:
    pass

# Patch global get_container
@pytest.fixture(autouse=True)
def patch_get_container(mocker):
    # Reset all mocks in the global container instance to prevent state leak
    for attr in dir(mock_container_instance):
        m = getattr(mock_container_instance, attr)
        if isinstance(m, MagicMock):
            m.reset_mock(return_value=True, side_effect=True)
            
    # Setup default returns for services again (after reset)
    mock_container_instance.catalog_service.load_data.return_value = {
        'titles': ['Naruto', 'Bleach'], 
        'lookup': [{'title': 'Naruto', 'id': '1'}, {'title': 'Bleach', 'id': '2'}], 
        'title_to_full_data': {
            'Naruto': {'title': 'Naruto', 'id': '1', 'image': 'n.jpg'},
            'Bleach': {'title': 'Bleach', 'id': '2', 'image': 'b.jpg'}
        },
        'title_to_index': {'Naruto': 0, 'Bleach': 1}
    }
    mock_container_instance.blind_test_service.get_random_theme.return_value = {
        'anime_title': 'A', 'song_title': 'S', 'artists': 'Art', 'video_url': 'v.mp4', 'type': 'OP'
    }
    mock_container_instance.cover_test_service.get_random_cover.return_value = {
        'manga_title': 'M', 'cover_url': 'c.jpg', 'locale': 'ja', 'volume': '1'
    }
    mock_container_instance.game_service.select_secret.return_value = "Naruto"
    mock_container_instance.game_service.select_secret_custom.return_value = "Naruto"
    mock_container_instance.game_service.check_title_match.return_value = False
    mock_container_instance.game_service.calculate_raw_similarity.return_value = 0.5
    
    mock_container_instance.akinetix_service.start_new_game.return_value = {
        'history': [], 'current_q': 'Q?', 'current_attr': 'A', 'game_over': False, 'ai_guess': None, 'probs': {}, 'asked_attrs': []
    }
    mock_container_instance.akinetix_service.process_answer.return_value = {
        'history': [], 'current_q': 'Q2?', 'current_attr': 'A2', 'game_over': False, 'ai_guess': None, 'probs': {}, 'asked_attrs': []
    }
    mock_container_instance.animinator_service.select_secret.return_value = "Naruto"
    mock_container_instance.animinator_service.start_new_game.return_value = {
        'history': [], 'current_q': 'Q?', 'current_attr': 'A', 'game_over': False, 'ai_guess': None, 'probs': {}, 'asked_attrs': []
    }
    mock_container_instance.animinator_service.process_question.return_value = {
        'history': [], 'current_q': 'Q2?', 'current_attr': 'A2', 'game_over': False, 'ai_guess': None, 'probs': {}, 'asked_attrs': [], 'answer': 'yes'
    }
    mock_container_instance.vision_quest_service.select_secret.return_value = {'id': 1, 'title': 'Naruto', 'image': 'n.jpg'}
    mock_container_instance.vision_quest_service.start_new_game.return_value = {'id': 1, 'title': 'Naruto', 'image': 'n.jpg'}
    # Force import to ensure attributes exist
    import animetix.containers
    import animetix.services

    # Pour les tests E2E, on veut éviter les MagicMocks qui polluent la session Django
    mocker.patch('animetix.containers.get_container', return_value=mock_container_instance)
    mocker.patch('animetix.services.get_container', return_value=mock_container_instance)

    # Patch tasks ONLY if it has get_container
    import animetix.tasks
    if hasattr(animetix.tasks, 'get_container'):
        mocker.patch('animetix.tasks.get_container', return_value=mock_container_instance)

    # Try to patch views if they are reachable, otherwise skip (core tests don't need them)
    try:
        from animetix.views import common
        if hasattr(common, 'get_container'):
            mocker.patch.object(common, 'get_container', return_value=mock_container_instance)
    except ImportError:
        pass
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
    mock = MagicMock(spec=AnimetixService)
    # Forward common methods to the container's mock if needed
    mock.load_data = mock_container.catalog_service.load_data
    mock.game_service = mock_container.game_service
    mock.blind_test_service = mock_container.blind_test_service
    mock.cover_test_service = mock_container.cover_test_service
    return mock

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

