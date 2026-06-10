# Manga Lab Reactivation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reactivate the Manga Lab by implementing dedicated views for cleaning and translating manga pages.

**Architecture:** Create `MangaCleanLabView` and `MangaTranslateLabView` in `backend/api/animetix/api/labs.py`. These views will handle file uploads, call the appropriate domain services (`InferencePort` and `MangaFlowService`), and return Base64 encoded images.

**Tech Stack:** Django REST Framework, Python 3.11+.

---

### Task 1: Implement Manga Lab Views

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Test: `tests/api/test_manga_lab.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_manga_lab.py`:
```python
import pytest
import base64
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from backend.api.animetix.api.labs import MangaCleanLabView, MangaTranslateLabView
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def dummy_image():
    return SimpleUploadedFile("test_manga.png", b"file_content", content_type="image/png")

def test_manga_clean_lab_view(dummy_image):
    factory = RequestFactory()
    request = factory.post('/api/v1/manga-lab/clean/', {'image': dummy_image})
    
    with patch('backend.api.animetix.api.labs.get_container') as mock_get_container:
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
    
    with patch('backend.api.animetix.api.labs.get_container') as mock_get_container:
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_manga_lab.py -v`
Expected: FAIL (ImportError: cannot import name 'MangaCleanLabView')

- [ ] **Step 3: Implement the views**

Add to `backend/api/animetix/api/labs.py`:
```python
import base64

class MangaCleanLabView(APIView):
    """Nettoie (inpaint) les bulles de texte d'une planche de manga."""
    permission_classes = [permissions.AllowAny] # Change to IsAuthenticated if needed in production

    def post(self, request):
        container = get_container()
        image_file = request.FILES.get('image')
        
        if not image_file:
            return Response({'error': 'Image file is required.'}, status=400)
            
        try:
            image_bytes = image_file.read()
            inference_engine = container.inference.primary()
            
            # Un nettoyage simple équivaut à un inpainting avec une liste de bulles vide.
            cleaned_bytes = inference_engine.inpaint_text_bubbles(image_bytes, [])
            
            b64_img = base64.b64encode(cleaned_bytes).decode('utf-8')
            return Response({
                'status': 'success',
                'image': b64_img
            })
        except Exception as e:
            logger.error(f"Error in MangaCleanLabView: {e}")
            return Response({'error': str(e)}, status=500)

class MangaTranslateLabView(APIView):
    """Traduit les bulles de texte d'une planche de manga."""
    permission_classes = [permissions.AllowAny] # Change to IsAuthenticated if needed in production

    def post(self, request):
        container = get_container()
        image_file = request.FILES.get('image')
        target_lang = request.data.get('target_lang', 'French')
        
        if not image_file:
            return Response({'error': 'Image file is required.'}, status=400)
            
        try:
            image_bytes = image_file.read()
            manga_flow_service = container.core.manga_flow_service()
            
            translated_bytes = manga_flow_service.translate_manga_page(image_bytes, target_lang)
            
            b64_img = base64.b64encode(translated_bytes).decode('utf-8')
            return Response({
                'status': 'success',
                'image': b64_img
            })
        except Exception as e:
            logger.error(f"Error in MangaTranslateLabView: {e}")
            return Response({'error': str(e)}, status=500)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_manga_lab.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/api/labs.py tests/api/test_manga_lab.py
git commit -m "feat(api): implement MangaCleanLabView and MangaTranslateLabView"
```

---

### Task 2: Update API Routes

**Files:**
- Modify: `backend/api/animetix/api_views.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Export views in proxy file**

Add to `backend/api/animetix/api_views.py`:
```python
from .api.labs import MangaCleanLabView, MangaTranslateLabView
```

- [ ] **Step 2: Update URL routing**

In `backend/api/animetix/urls/api.py`, replace:
```python
    # path('manga-lab/', api_views.MangaLabDataView.as_view(), name='api_manga_lab'),
```
With:
```python
    path('manga-lab/clean/', api_views.MangaCleanLabView.as_view(), name='api_manga_clean_lab'),
    path('manga-lab/translate/', api_views.MangaTranslateLabView.as_view(), name='api_manga_translate_lab'),
```

- [ ] **Step 3: Verify Django configuration**

Run: `python backend/api/manage.py check`
Expected: System check identified no issues (or only pre-existing warnings, no URL/Import errors).

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix/api_views.py backend/api/animetix/urls/api.py
git commit -m "feat(api): expose Manga Lab clean and translate endpoints"
```
