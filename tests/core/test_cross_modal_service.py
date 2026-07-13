from unittest.mock import MagicMock

import pytest
from core.domain.exceptions import SearchIndexUnavailableError
from core.domain.services.cross_modal_service import (
    CrossModalSearchService,
    VlmIndexingService,
)
from core.domain.services.prompt_manager import PromptManager


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def mock_vector_db():
    """Non-empty by default (``unified_clip_space`` holds vectors): most tests
    exercise the "index exists" path. Tests for the empty-index guard
    override ``get_collection_count`` back to 0 explicitly."""
    m = MagicMock()
    m.get_collection_count.return_value = 42
    return m


@pytest.fixture
def mock_prompt_manager():
    manager = MagicMock(spec=PromptManager)
    manager.get_prompt.return_value = ("Formatted prompt", "System prompt")
    return manager


@pytest.fixture
def cross_modal_service(mock_engine, mock_vector_db):
    return CrossModalSearchService(
        inference_engine=mock_engine, vector_db=mock_vector_db
    )


@pytest.fixture
def vlm_service(mock_engine, mock_prompt_manager):
    return VlmIndexingService(
        inference_engine=mock_engine, prompt_manager=mock_prompt_manager
    )


def test_deep_multimodal_search_text_only(cross_modal_service, mock_vector_db):
    mock_vector_db.search_by_vector.return_value = [{"title": "Found"}]
    res = cross_modal_service.deep_multimodal_search("query", limit=5)
    assert res[0]["title"] == "Found"
    mock_vector_db.search_by_vector.assert_called_once()


def test_deep_multimodal_search_image_only(
    cross_modal_service, mock_engine, mock_vector_db
):
    mock_engine.get_image_embedding.return_value = [0.1] * 512
    mock_vector_db.search_by_vector.return_value = []
    cross_modal_service.deep_multimodal_search("", image_data=b"img")
    mock_engine.get_image_embedding.assert_called_with(
        b"img", model_id="dudcjs2779/anime-style-tag-clip"
    )


def test_describe_poster(vlm_service, mock_engine, mock_prompt_manager):
    mock_engine.generate_image_description.return_value = "Cool poster"
    res = vlm_service.describe_poster(b"data", "Title")
    assert res == "Cool poster"
    mock_prompt_manager.get_prompt.assert_called_with(
        "cross_modal_analysis", title="Title"
    )


def test_index_visual_narrative(vlm_service, mock_engine):
    mock_engine.generate_image_description.return_value = "Description"
    res = vlm_service.index_visual_narrative({"title": "X"}, b"data")
    assert res == "Description"


# --------------------------------------------------------------------------- #
# Empty-index guard: `unified_clip_space` has no reachable writer today, so a
# search against it can never return a real match. The service must say so
# instead of silently querying and returning [].
# --------------------------------------------------------------------------- #
def test_is_available_true_when_collection_has_vectors(
    cross_modal_service, mock_vector_db
):
    mock_vector_db.get_collection_count.return_value = 7
    assert cross_modal_service.is_available() is True
    mock_vector_db.get_collection_count.assert_called_once_with("unified_clip_space")


def test_is_available_false_when_collection_empty(cross_modal_service, mock_vector_db):
    mock_vector_db.get_collection_count.return_value = 0
    assert cross_modal_service.is_available() is False


def test_deep_multimodal_search_raises_when_collection_empty(
    cross_modal_service, mock_engine, mock_vector_db
):
    """No writer ever populates `unified_clip_space` for a normal user -- the
    service must refuse the search up front, before touching the inference
    engine or issuing a vector query."""
    mock_vector_db.get_collection_count.return_value = 0

    with pytest.raises(SearchIndexUnavailableError):
        cross_modal_service.deep_multimodal_search("query", image_data=b"img")

    mock_engine.get_text_embedding.assert_not_called()
    mock_engine.get_image_embedding.assert_not_called()
    mock_vector_db.search_by_vector.assert_not_called()


def test_failed_text_embedding_does_not_fall_back_to_random_vector(
    cross_modal_service, mock_engine, mock_vector_db
):
    """A failed embedding must never be replaced by `np.random.rand(...)` --
    that turned a broken inference call into a confident-looking, made-up
    result set. It must propagate instead."""
    mock_engine.get_text_embedding.side_effect = RuntimeError("embedding backend down")

    with pytest.raises(RuntimeError):
        cross_modal_service.deep_multimodal_search("some query")

    mock_vector_db.search_by_vector.assert_not_called()
