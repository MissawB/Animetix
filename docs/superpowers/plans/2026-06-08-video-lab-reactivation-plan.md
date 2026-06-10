# Video Lab Reactivation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reactivate the Video Lab by implementing a dedicated view for FateZero style transfer and a metadata endpoint for available styles.

**Architecture:** Implement `VideoFateZeroLabView` and `VideoLabDataView` in `backend/api/animetix/api/labs.py`. These views will leverage the `StudioTransformService` to apply anime studio styles to uploaded videos with temporal consistency.

**Tech Stack:** Django REST Framework, Python 3.11+.

---

### Task 1: Implement Video Lab Views

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Test: `tests/api/test_video_lab.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_video_lab.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from backend.api.animetix.api.labs import VideoFateZeroLabView, VideoLabDataView
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def dummy_video():
    return SimpleUploadedFile("test_video.mp4", b"video_content", content_type="video/mp4")

def test_video_lab_data_view():
    factory = RequestFactory()
    request = factory.get('/api/v1/labs/video/')
    view = VideoLabDataView.as_view()
    response = view(request)
    
    assert response.status_code == 200
    assert response.data['status'] == 'active'
    assert any(tool['id'] == 'fatezero' for tool in response.data['tools'])

def test_video_fatezero_lab_view(dummy_video):
    factory = RequestFactory()
    request = factory.post('/api/v1/labs/video/fatezero/', {'video': dummy_video, 'studio_style': 'Ghibli'})
    
    with patch('backend.api.animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.transform_video_to_anime_sota.return_value = "http://storage.com/result.mp4"
        mock_container.core.studio_transform_service.return_value = mock_service
        mock_get_container.return_value = mock_container
        
        view = VideoFateZeroLabView.as_view()
        response = view(request)
        
        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert response.data['video_url'] == "http://storage.com/result.mp4"
        mock_service.transform_video_to_anime_sota.assert_called_once_with(b"video_content", 'Ghibli')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_video_lab.py -v`
Expected: FAIL (ImportError: cannot import name 'VideoFateZeroLabView')

- [ ] **Step 3: Implement the views**

Add to `backend/api/animetix/api/labs.py`:
```python
class VideoFateZeroLabView(APIView):
    """Transforme une vidéo avec transfert de style SOTA (FateZero)."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        container = get_container()
        video_file = request.FILES.get('video')
        studio_style = request.data.get('studio_style', 'Ufotable')
        
        if not video_file:
            return Response({'error': 'Video file is required.'}, status=400)
            
        try:
            video_bytes = video_file.read()
            service = container.core.studio_transform_service()
            
            result_url = service.transform_video_to_anime_sota(video_bytes, studio_style)
            
            return Response({
                'status': 'success',
                'video_url': result_url,
                'message': f"Transformation {studio_style} (FateZero) réussie."
            })
        except Exception as e:
            logger.error(f"Error in VideoFateZeroLabView: {e}")
            return Response({'error': str(e)}, status=500)

class VideoLabDataView(APIView):
    """Métadonnées pour les outils du Video Lab."""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'status': 'active',
            'tools': [
                {
                    'id': 'fatezero',
                    'name': 'FateZero Style Transfer',
                    'description': 'Temporally consistent anime style transfer for real videos.',
                    'endpoint': '/api/v1/labs/video/fatezero/',
                    'supported_styles': ['Shaft', 'Ufotable', 'Kyoto', 'Ghibli']
                }
            ]
        })
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_video_lab.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/api/labs.py tests/api/test_video_lab.py
git commit -m "feat(api): implement VideoFateZeroLabView and VideoLabDataView"
```

---

### Task 2: Update API Routes

**Files:**
- Modify: `backend/api/animetix/api_views.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Export views in proxy file**

Add to `backend/api/animetix/api_views.py`:
```python
from .api.labs import VideoFateZeroLabView, VideoLabDataView
```

- [ ] **Step 2: Update URL routing**

In `backend/api/animetix/urls/api.py`, replace:
```python
    # path('labs/video/', api_views.VideoLabDataView.as_view(), name='api_video_lab'),
```
With:
```python
    path('labs/video/', api_views.VideoLabDataView.as_view(), name='api_video_lab'),
    path('labs/video/fatezero/', api_views.VideoFateZeroLabView.as_view(), name='api_video_fatezero_lab'),
```

- [ ] **Step 3: Verify Django configuration**

Run: `python backend/api/manage.py check`
Expected: System check identified no issues.

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix/api_views.py backend/api/animetix/urls/api.py
git commit -m "feat(api): expose Video Lab style transfer endpoints"
```
