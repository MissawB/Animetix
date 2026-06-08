import pytest
import base64
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from animetix.api.labs import MangaCleanLabView, MangaTranslateLabView
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def dummy_image():
    return SimpleUploadedFile("test_manga.png", b"file_content", content_type="image/png")

def test_manga_clean_lab_view(dummy_image):
    factory = RequestFactory()
    request = factory.post('/api/v1/manga-lab/clean/', {'image': dummy_image})
    
    with patch('animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_primary = MagicMock()
        # Mock returns bytes
        mock_primary.inpaint_text_bubbles.return_value = b"cleaned_image_bytes"
        mock_container.inference.primary.return_value = mock_primary
        mock_get_container.return_value = mock_container
        
        view = MangaCleanLabView.as_view()
        response = view(request)
        
        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert response.data['image'] == base64.b64encode(b"cleaned_image_bytes").decode('utf-8')
        mock_primary.inpaint_text_bubbles.assert_called_once_with(b"file_content", [])

def test_manga_translate_lab_view(dummy_image):
    factory = RequestFactory()
    request = factory.post('/api/v1/manga-lab/translate/', {'image': dummy_image, 'target_lang': 'English'})
    
    with patch('animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.translate_manga_page.return_value = b"translated_image_bytes"
        mock_container.core.manga_flow_service.return_value = mock_service
        mock_get_container.return_value = mock_container
        
        view = MangaTranslateLabView.as_view()
        response = view(request)
        
        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert response.data['image'] == base64.b64encode(b"translated_image_bytes").decode('utf-8')
        mock_service.translate_manga_page.assert_called_once_with(b"file_content", 'English')
