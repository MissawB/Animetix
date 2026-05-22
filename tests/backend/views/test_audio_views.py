import pytest
from django.urls import reverse
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from io import BytesIO

@pytest.mark.django_db
@patch('animetix.views.audio.render')
def test_audio_lab_view(mock_render, client):
    mock_render.return_value = HttpResponse("fake content")
    url = reverse('audio_lab')
    response = client.get(url)
    assert response.status_code == 200
    mock_render.assert_called_once()
    args, kwargs = mock_render.call_args
    assert 'library_voices' in args[2]
    assert any(v['id'] == 'naruto' for v in args[2]['library_voices'])

@pytest.mark.django_db
@patch('animetix.views.audio.get_container')
@patch('animetix.views.audio.AudioSegment')
def test_clone_voice_api_success(mock_audio_segment, mock_get_container, client):
    # Setup mocks
    mock_container = MagicMock()
    mock_get_container.return_value = mock_container
    
    mock_vc_service = MagicMock()
    mock_container.voice_cloning_service = mock_vc_service
    mock_vc_service.generate_character_voice.return_value = b"fake_wav_data"
    
    mock_audio_instance = MagicMock()
    mock_audio_segment.from_wav.return_value = mock_audio_instance
    # Ensure export doesn't crash
    mock_audio_instance.export.return_value = None
    
    url = reverse('audio_clone')
    data = {
        'text': 'Hello world',
        'source_type': 'library',
        'voice_id': 'naruto'
    }
    
    # Mock file existence check if needed, but the code handles it by ref_audio_bytes check
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', MagicMock(return_value=BytesIO(b"reference_audio"))):
        response = client.post(url, data)
    
    assert response.status_code == 200
    res_json = response.json()
    assert res_json['status'] == 'success'
    assert 'audio_base64' in res_json
    assert res_json['audio_base64'].startswith('data:audio/mp3;base64,')

@pytest.mark.django_db
def test_clone_voice_api_missing_text(client):
    url = reverse('audio_clone')
    data = {
        'source_type': 'library',
        'voice_id': 'naruto'
    }
    response = client.post(url, data)
    assert response.status_code == 400
    assert 'Texte manquant' in response.json()['error']

@pytest.mark.django_db
def test_clone_voice_api_get_request(client):
    url = reverse('audio_clone')
    response = client.get(url)
    # The code does redirect('audio_lab') for non-POST
    assert response.status_code == 302
    assert response.url == reverse('audio_lab')
