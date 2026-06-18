from unittest.mock import MagicMock
from core.domain.services.creative.manga_flow import MangaFlowService


def test_translate_manga_page_iterates_bubbles():
    mock_inference = MagicMock()
    # Mock OCR returning two text bubbles
    mock_inference.process_manga_page.return_value = {
        "text": "Full text",
        "layout": [
            {"text": "Hello", "bbox": [10, 10, 50, 50]},
            {"text": "World", "bbox": [60, 60, 100, 100]},
        ],
    }
    mock_inference.inpaint_text_bubbles.return_value = "base64_image_data"

    mock_llm = MagicMock()
    # LLM translates sequentially
    mock_llm.generate.side_effect = ["Bonjour", "Monde"]

    mock_prompt_mgr = MagicMock()
    mock_prompt_mgr.get_prompt.return_value = ("prompt", "system")

    service = MangaFlowService(mock_inference, mock_llm, mock_prompt_mgr)

    res = service.translate_manga_page(b"fake_image", "French")

    assert res == "base64_image_data"
    # Ensure LLM was called for each bubble
    assert mock_llm.generate.call_count == 2
    # Ensure inpaint was called with the aggregated translated bubbles
    mock_inference.inpaint_text_bubbles.assert_called_once()
    args, kwargs = mock_inference.inpaint_text_bubbles.call_args
    bubbles = args[1]
    assert len(bubbles) == 2
    assert bubbles[0]["text"] == "Bonjour"
    assert bubbles[0]["bbox"] == [10, 10, 50, 50]
    assert bubbles[1]["text"] == "Monde"
    assert bubbles[1]["bbox"] == [60, 60, 100, 100]
