import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.manga_ocr_adapter import MangaOcrAdapter

@patch("adapters.inference.manga_ocr_adapter.InferenceClient")
def test_manga_ocr_calls_hf_api(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    # Mock dots.mocr response
    mock_client.post.return_value = '{"generated_text": "\u3053\u3093\u306b\u3061\u306f"}'.encode("utf-8")
    
    adapter = MangaOcrAdapter(token="fake_token")
    result = adapter.process_manga_page(b"fake_image_data")
    
    assert "\u3053\u3093\u306b\u3061\u306f" in result["text"]
    assert result["model"] == "dots.mocr"
