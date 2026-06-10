# Audio Lab Reactivation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reactivate the Audio Lab by implementing dedicated views for Soundscape generation (Video-to-Audio) and Speech-to-Speech (direct voice interaction).

**Architecture:** Implement three new API views in `backend/api/animetix/api/labs.py` that leverage `SoundscapeGenerationService` and `NativeSpeechLLMService`.

**Tech Stack:** Django REST Framework, Python 3.11+, AudioLDM / S2S (Inference).

---

### Task 1: Implement Audio Lab Views

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Test: `tests/api/test_audio_lab.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_audio_lab.py`:
```python
import pytest
import base64
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from backend.api.animetix.api.labs import AudioLabDataView, SoundscapeGenerationView, SpeechToSpeechLabView
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def dummy_video():
    return SimpleUploadedFile("clip.mp4", b"video_content", content_type="video/mp4")

@pytest.fixture
def dummy_audio():
    return SimpleUploadedFile("input.wav", b"audio_content", content_type="audio/wav")

def test_audio_lab_data_view():
    factory = RequestFactory()
    request = factory.get('/api/v1/labs/audio/')
    view = AudioLabDataView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert any(tool['id'] == 'soundscape' for tool in response.data['tools'])
    assert any(tool['id'] == 's2s' for tool in response.data['tools'])

def test_soundscape_generation_view(dummy_video):
    factory = RequestFactory()
    request = factory.post('/api/v1/labs/audio/soundscape/', {'video': dummy_video})
    
    with patch('backend.api.animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.generate_soundscape_for_video.return_value = "http://storage.com/ambient.wav"
        mock_container.core.soundscape_service.return_value = mock_service
        mock_get_container.return_value = mock_container
        
        # Bypass permissions for testing
        view = SoundscapeGenerationView.as_view(permission_classes=[])
        response = view(request)
        assert response.status_code == 200
        assert response.data['audio_url'] == "http://storage.com/ambient.wav"

def test_speech_to_speech_lab_view(dummy_audio):
    factory = RequestFactory()
    request = factory.post('/api/v1/labs/audio/s2s/', {'audio': dummy_audio, 'persona': 'Saber'})
    
    with patch('backend.api.animetix.api.labs.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.process_voice_interaction.return_value = {
            "status": "success", "audio_data": b"voice_output_bytes"
        }
        mock_container.core.native_speech_llm_service.return_value = mock_service
        mock_get_container.return_value = mock_container
        
        # Bypass permissions for testing
        view = SpeechToSpeechLabView.as_view(permission_classes=[])
        response = view(request)
        assert response.status_code == 200
        assert response.data['audio_data'] == base64.b64encode(b"voice_output_bytes").decode('utf-8')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_audio_lab.py -v`
Expected: FAIL (ImportError: cannot import name 'SoundscapeGenerationView')

- [ ] **Step 3: Implement the views**

Update `backend/api/animetix/api/labs.py`:
- Replace placeholder `AudioLabDataView`.
- Add `SoundscapeGenerationView` and `SpeechToSpeechLabView`.

```python
class AudioLabDataView(APIView):
    """Métadonnées pour les outils de l'Audio Lab."""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'status': 'active',
            'tools': [
                {
                    'id': 'soundscape',
                    'name': 'Soundscape Generation',
                    'description': 'Generate audio atmosphere for silent video clips (AudioLDM).',
                    'endpoint': '/api/v1/labs/audio/soundscape/'
                },
                {
                    'id': 's2s',
                    'name': 'Speech-to-Speech',
                    'description': 'Direct voice-to-voice interaction (End-to-End Voice).',
                    'endpoint': '/api/v1/labs/audio/s2s/'
                },
                {
                    'id': 'voice-cloning',
                    'name': 'Voice Cloning',
                    'description': 'Zero-shot character voice cloning (RVC).',
                    'endpoint': '/api/v1/voice-cloning/' # Re-using existing if already there
                }
            ]
        })

class SoundscapeGenerationView(APIView):
    """Génère une ambiance sonore à partir d'une vidéo."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        container = get_container()
        video_file = request.FILES.get('video')
        
        if not video_file:
            return Response({'error': 'Video file is required.'}, status=400)
            
        try:
            video_bytes = video_file.read()
            service = container.core.soundscape_service()
            result_url = service.generate_soundscape_for_video(video_bytes)
            return Response({
                'status': 'success',
                'audio_url': result_url,
                'message': "Ambiance sonore générée."
            })
        except Exception as e:
            logger.error(f"Error in SoundscapeGenerationView: {e}")
            return Response({'error': str(e)}, status=500)

class SpeechToSpeechLabView(APIView):
    """Interaction vocale directe (Voice-to-Voice)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        audio_file = request.FILES.get('audio')
        persona = request.data.get('persona', '')
        
        if not audio_file:
            return Response({'error': 'Audio file is required.'}, status=400)
            
        try:
            audio_bytes = audio_file.read()
            service = container.core.native_speech_llm_service()
            result = service.process_voice_interaction(audio_bytes, persona)
            
            if result['status'] == 'success':
                b64_audio = base64.b64encode(result['audio_data']).decode('utf-8')
                return Response({
                    'status': 'success',
                    'audio_data': b64_audio
                })
            return Response(result, status=500)
        except Exception as e:
            logger.error(f"Error in SpeechToSpeechLabView: {e}")
            return Response({'error': str(e)}, status=500)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_audio_lab.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/api/labs.py tests/api/test_audio_lab.py
git commit -m "feat(api): implement Audio Lab views for Soundscape and S2S"
```

---

### Task 2: Update API Routes

**Files:**
- Modify: `backend/api/animetix/api_views.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Export views in proxy file**

Add to `backend/api/animetix/api_views.py`:
```python
from .api.labs import AudioLabDataView, SoundscapeGenerationView, SpeechToSpeechLabView
```

- [ ] **Step 2: Update URL routing**

In `backend/api/animetix/urls/api.py`, replace:
```python
    path('audio-lab/', api_views.AudioLabDataView.as_view(), name='api_audio_lab'),
    # path('labs/soundscape/', api_views.SoundscapeLabDataView.as_view(), name='api_soundscape_lab'),
    # path('labs/s2s/', api_views.SpeechToSpeechLabDataView.as_view(), name='api_s2s_lab'),
```
With:
```python
    path('labs/audio/', api_views.AudioLabDataView.as_view(), name='api_audio_lab'),
    path('labs/audio/soundscape/', api_views.SoundscapeGenerationView.as_view(), name='api_audio_soundscape'),
    path('labs/audio/s2s/', api_views.SpeechToSpeechLabView.as_view(), name='api_audio_s2s'),
```

- [ ] **Step 3: Verify Django configuration**

Run: `python backend/api/manage.py check`
Expected: System check identified no issues.

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix/api_views.py backend/api/animetix/urls/api.py
git commit -m "feat(api): expose Audio Lab soundscape and S2S endpoints"
```
