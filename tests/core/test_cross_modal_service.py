import pytest
import numpy as np
from unittest.mock import MagicMock
from core.domain.services.cross_modal_service import CrossModalSearchService, VlmIndexingService

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def mock_vector_db():
    return MagicMock()

@pytest.fixture
def cross_modal_service(mock_engine, mock_vector_db):
    return CrossModalSearchService(inference_engine=mock_engine, vector_db=mock_vector_db)

@pytest.fixture
def vlm_service(mock_engine):
    return VlmIndexingService(inference_engine=mock_engine)

def test_deep_multimodal_search_text_only(cross_modal_service, mock_vector_db):
    mock_vector_db.search_by_vector.return_value = [{'title': 'Found'}]
    res = cross_modal_service.deep_multimodal_search("query", limit=5)
    assert res[0]['title'] == 'Found'
    mock_vector_db.search_by_vector.assert_called_once()

def test_deep_multimodal_search_image_only(cross_modal_service, mock_engine, mock_vector_db):
    mock_engine.get_image_embedding.return_value = [0.1] * 512
    mock_vector_db.search_by_vector.return_value = []
    cross_modal_service.deep_multimodal_search("", image_data=b"img")
    mock_engine.get_image_embedding.assert_called_with(b"img", model_id="openai/clip-vit-base-patch32")

def test_describe_poster(vlm_service, mock_engine):
    mock_engine.generate_image_description.return_value = "Cool poster"
    assert vlm_service.describe_poster(b"data", "Title") == "Cool poster"

def test_index_visual_narrative(vlm_service, mock_engine):
    mock_engine.generate_image_description.return_value = "Description"
    res = vlm_service.index_visual_narrative({'title': 'X'}, b"data")
    assert res == "Description"
