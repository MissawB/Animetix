# Spatial Lab Reactivation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reactivate the Spatial Lab by implementing dedicated views for monocular depth estimation and 3D Gaussian Splatting (Image-to-3D and Video-to-3D).

**Architecture:** Implement three new API views in `backend/api/animetix/api/labs.py` that leverage `SpatialComputingService` and `CinematicVolumetricReconstructionService`.

**Tech Stack:** Django REST Framework, Python 3.11+, Gaussian Splatting (Inference).

---

### Task 1: Implement Spatial Lab Views

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Test: `tests/api/test_spatial_lab.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_spatial_lab.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from backend.api.animetix.api.labs import SpatialLabDataView, Generate3DDataView, CinematicReconstructionView
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def dummy_image():
    return SimpleUploadedFile("poster.png", b"image_content", content_type="image/png")

@pytest.fixture
def dummy_video():
    return SimpleUploadedFile("clip.mp4", b"video_content", content_type="video/mp4")

def test_spatial_lab_data_view():
    factory = RequestFactory()
    request = factory.get('/api/v1/labs/spatial/')
    view = SpatialLabDataView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert any(tool['id'] == 'generate-3d' for tool in response.data['tools'])

def test_generate_3d_data_view(dummy_image):
    factory = RequestFactory()
    request = factory.post('/api/v1/labs/spatial/generate-3d/', {'image': dummy_image, 'title': 'Test Scene'})
    
    with patch('backend.api.animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.reconstruct_3d_scene.return_value = {
            "status": "success", "model_url": "http://storage.com/model.ply", "viewer_type": "gaussian_splatting"
        }
        mock_container.core.spatial_computing_service.return_value = mock_service
        mock_get_container.return_value = mock_container
        
        view = Generate3DDataView.as_view()
        response = view(request)
        assert response.status_code == 200
        assert response.data['model_url'] == "http://storage.com/model.ply"

def test_cinematic_reconstruction_view(dummy_video):
    factory = RequestFactory()
    request = factory.post('/api/v1/labs/spatial/cinematic/', {'video': dummy_video})
    
    with patch('backend.api.animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.reconstruct_dynamic_cinematic_scene.return_value = {
            "status": "success", "frames": [{"timestamp": 0, "model_url": "url"}]
        }
        mock_container.core.cinematic_volumetric_reconstruction_service.return_value = mock_service
        mock_get_container.return_value = mock_container
        
        view = CinematicReconstructionView.as_view()
        response = view(request)
        assert response.status_code == 200
        assert len(response.data['frames']) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_spatial_lab.py -v`
Expected: FAIL (ImportError: cannot import name 'Generate3DDataView')

- [ ] **Step 3: Implement the views**

Update `backend/api/animetix/api/labs.py`:
- Replace placeholder `SpatialLabDataView`.
- Add `Generate3DDataView` and `CinematicReconstructionView`.

```python
class SpatialLabDataView(APIView):
    """Métadonnées pour les outils de Calcul Spatial."""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'status': 'active',
            'tools': [
                {
                    'id': 'generate-3d',
                    'name': 'Image-to-3D',
                    'description': 'Generate a navigable 3D scene from a single image (Gaussian Splatting).',
                    'endpoint': '/api/v1/labs/spatial/generate-3d/'
                },
                {
                    'id': 'cinematic',
                    'name': 'Cinematic Reconstruction',
                    'description': 'Reconstruct dynamic volumetric 3D scenes from video clips.',
                    'endpoint': '/api/v1/labs/spatial/cinematic/'
                }
            ]
        })

class Generate3DDataView(APIView):
    """Génère une scène 3D (PLY) à partir d'une image."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        image_file = request.FILES.get('image')
        title = request.data.get('title', 'Poster 3D')
        
        if not image_file:
            return Response({'error': 'Image file is required.'}, status=400)
            
        try:
            image_bytes = image_file.read()
            service = container.core.spatial_computing_service()
            result = service.reconstruct_3d_scene(image_bytes, title)
            return Response(result)
        except Exception as e:
            logger.error(f"Error in Generate3DDataView: {e}")
            return Response({'error': str(e)}, status=500)

class CinematicReconstructionView(APIView):
    """Génère une séquence de scènes 3D à partir d'une vidéo."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        video_file = request.FILES.get('video')
        title = request.data.get('title', 'Cinematic 3D')
        
        if not video_file:
            return Response({'error': 'Video file is required.'}, status=400)
            
        try:
            video_bytes = video_file.read()
            service = container.core.cinematic_volumetric_reconstruction_service()
            result = service.reconstruct_dynamic_cinematic_scene(video_bytes, title)
            return Response(result)
        except Exception as e:
            logger.error(f"Error in CinematicReconstructionView: {e}")
            return Response({'error': str(e)}, status=500)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_spatial_lab.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/api/labs.py tests/api/test_spatial_lab.py
git commit -m "feat(api): implement Spatial Lab views for 3D reconstruction"
```

---

### Task 2: Update API Routes

**Files:**
- Modify: `backend/api/animetix/api_views.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Export views in proxy file**

Add to `backend/api/animetix/api_views.py`:
```python
from .api.labs import SpatialLabDataView, Generate3DDataView, CinematicReconstructionView
```

- [ ] **Step 2: Update URL routing**

In `backend/api/animetix/urls/api.py`, replace:
```python
    path('spatial-lab/', api_views.SpatialLabDataView.as_view(), name='api_spatial_lab'),
    # path('spatial-lab/generate-3d/', api_views.Generate3DDataView.as_view(), name='api_generate_3d'),
    # path('spatial-lab/cinematic-reconstruction/', api_views.CinematicReconstructionView.as_view(), name='api_cinematic_reconstruction'),
```
With:
```python
    path('labs/spatial/', api_views.SpatialLabDataView.as_view(), name='api_spatial_lab'),
    path('labs/spatial/generate-3d/', api_views.Generate3DDataView.as_view(), name='api_generate_3d'),
    path('labs/spatial/cinematic/', api_views.CinematicReconstructionView.as_view(), name='api_cinematic_reconstruction'),
```

- [ ] **Step 3: Verify Django configuration**

Run: `python backend/api/manage.py check`
Expected: System check identified no issues.

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix/api_views.py backend/api/animetix/urls/api.py
git commit -m "feat(api): expose Spatial Lab 3D reconstruction endpoints"
```
