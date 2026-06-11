import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from unittest.mock import MagicMock, patch
import io

@pytest.mark.django_db
def test_voice_cloning_api_endpoint():
    user = User.objects.create_user(username='testuser', password='password')
    client = APIClient()
    client.force_authenticate(user=user)
    
    url = reverse('api_voice_cloning')
    
    # Mocking the container and service
    # The path to get_container depends on where it's imported in labs.py
    # In labs.py it's: from ..containers import get_container
    # So it's animetix.containers.get_container or animetix.api.labs.get_container
    with patch('animetix.api.labs.get_container') as mock_get_container:
        mock_service = MagicMock()
        mock_service.clone.return_value = b"fake_audio_content"
        
        mock_container = MagicMock()
        mock_container.core.voice_cloning_service.return_value = mock_service
        mock_get_container.return_value = mock_container
        
        # Create a dummy audio file
        size_bytes = 100
        header = (
            b'RIFF' + 
            (size_bytes + 36).to_bytes(4, 'little') + 
            b'WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x22\x56\x00\x00\x44\xac\x00\x00\x02\x00\x10\x00data' + 
            size_bytes.to_bytes(4, 'little')
        )
        audio_file = io.BytesIO(header + b'\x00' * size_bytes)
        audio_file.name = 'test.wav'
        
        # Sending as multipart to include the file
        response = client.post(url, {
            'target_text': 'Hello world',
            'reference_audio': audio_file,
            'pitch': 0
        }, format='multipart')
        
        if response.status_code != 200:
            print(f"Response error: {response.data}")
            
        assert response.status_code == 200
        assert response.data['status'] == 'success'
        assert 'audio_data' in response.data
        assert response.data['audio_data'].startswith('data:audio/wav;base64,')

@pytest.mark.django_db
def test_voice_cloning_api_invalid_pitch():
    user = User.objects.create_user(username='testuser2', password='password')
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse('api_voice_cloning')
    
    audio_file = io.BytesIO(b"fake_audio")
    audio_file.name = 'test.wav'
    
    response = client.post(url, {
        'target_text': 'Hello',
        'reference_audio': audio_file,
        'pitch': 'invalid'
    }, format='multipart')
    
    assert response.status_code == 400
    assert "error" in response.data

@pytest.mark.django_db
def test_voice_cloning_api_file_too_large():
    user = User.objects.create_user(username='testuser3', password='password')
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse('api_voice_cloning')
    
    # Create a 6MB "audio" file
    large_file = io.BytesIO(b"0" * (6 * 1024 * 1024))
    large_file.name = 'large.wav'
    
    response = client.post(url, {
        'target_text': 'Hello',
        'reference_audio': large_file,
        'pitch': 0
    }, format='multipart')
    
    assert response.status_code == 400
    assert "too large" in response.data.get('error', '').lower()

@pytest.mark.django_db
def test_voice_cloning_api_invalid_file_type():
    user = User.objects.create_user(username='testuser4', password='password')
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse('api_voice_cloning')
    
    txt_file = io.BytesIO(b"this is a text file")
    txt_file.name = 'test.txt'
    
    response = client.post(url, {
        'target_text': 'Hello',
        'reference_audio': txt_file,
        'pitch': 0
    }, format='multipart')
    
    assert response.status_code == 400
    assert "invalid file type" in response.data.get('error', '').lower()
