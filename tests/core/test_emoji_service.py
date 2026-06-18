from unittest.mock import MagicMock

import pytest
from core.domain.services.emoji_service import EmojiDomainService


@pytest.fixture
def mock_llm_service():
    return MagicMock()


@pytest.fixture
def emoji_service(mock_llm_service):
    return EmojiDomainService(llm_service=mock_llm_service)


def test_select_secret(emoji_service):
    catalog = {"titles": ["A", "B"], "title_to_full_data": {"A": {}, "B": {}}}
    secret = emoji_service.select_secret(catalog)
    assert secret in ["A", "B"]


def test_select_secret_empty(emoji_service):
    catalog = {"titles": []}
    assert emoji_service.select_secret(catalog) is None


def test_generate_emojis(emoji_service, mock_llm_service):
    mock_llm_service.generate_emojis.return_value = "🍥🦊"
    res = emoji_service.generate_emojis("Anime", "Naruto", "Ninja story")
    assert res == "🍥🦊"
    mock_llm_service.generate_emojis.assert_called_once_with(
        "Anime", "Naruto", "Ninja story"
    )
