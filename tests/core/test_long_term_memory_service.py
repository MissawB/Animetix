from unittest.mock import MagicMock

import pytest
from core.domain.services.long_term_memory_service import LongTermMemoryService
from core.domain.services.prompt_manager import PromptManager


@pytest.fixture
def mock_chroma():
    return MagicMock()


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def mock_prompt_manager():
    manager = MagicMock(spec=PromptManager)
    manager.get_prompt.return_value = (
        "Formatted history summary",
        "System prompt memory",
    )
    return manager


@pytest.fixture
def memory_service(mock_chroma, mock_engine, mock_prompt_manager):
    return LongTermMemoryService(
        chroma_resource=mock_chroma,
        inference_engine=mock_engine,
        prompt_manager=mock_prompt_manager,
    )


def test_store_memory(memory_service, mock_chroma, mock_engine, mock_prompt_manager):
    # Setup mocks
    mock_coll = MagicMock()
    mock_chroma.get_collection.return_value = mock_coll
    mock_engine.generate.return_value = "User likes action anime."

    history = [{"role": "user", "content": "I love Naruto"}]
    memory_service.store_memory("user123", history)

    # Assertions
    mock_prompt_manager.get_prompt.assert_called_once()
    assert "long_term_memory_summary" in mock_prompt_manager.get_prompt.call_args[0]

    mock_engine.generate.assert_called_once_with(
        "Formatted history summary", system_prompt="System prompt memory"
    )
    mock_coll.add.assert_called_once()
    args, kwargs = mock_coll.add.call_args
    assert "User likes action anime." in kwargs["documents"]
    assert kwargs["metadatas"][0]["user_id"] == "user123"


def test_retrieve_relevant_memories(memory_service, mock_chroma):
    mock_coll = MagicMock()
    mock_chroma.get_collection.return_value = mock_coll
    mock_coll.query.return_value = {"documents": [["Memory 1", "Memory 2"]]}

    res = memory_service.retrieve_relevant_memories("user123", "Naruto")

    assert "Memory 1" in res
    assert "Memory 2" in res
    mock_coll.query.assert_called_once()
