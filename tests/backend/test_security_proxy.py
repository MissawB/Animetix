import pytest
import base64
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestSSRFProtection:
    def setup_method(self):
        self.client = APIClient()
        self.url_name = 'cdn_proxy'

    def _get_proxy_url(self, target_url):
        encoded = base64.b64encode(target_url.encode()).decode()
        return f"{reverse(self.url_name)}?url={encoded}"

    @patch('requests.get')
    def test_proxy_allows_external_url(self, mock_get):
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake image data'
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_get.return_value = mock_response

        target = "https://example.com/image.png"
        response = self.client.get(self._get_proxy_url(target))

        assert response.status_code == 200
        assert response.content == b'fake image data'
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_proxy_blocks_internal_ip_loopback(self, mock_get):
        target = "http://127.0.0.1:8000/admin/"
        response = self.client.get(self._get_proxy_url(target), follow=True)

        # We want it to return 403 and NOT call requests.get
        assert response.status_code == 403
        mock_get.assert_not_called()

    @patch('requests.get')
    def test_proxy_blocks_private_ip_range(self, mock_get):
        target = "http://192.168.1.1/setup"
        response = self.client.get(self._get_proxy_url(target), follow=True)

        assert response.status_code == 403
        mock_get.assert_not_called()

    @patch('requests.get')
    def test_proxy_blocks_invalid_scheme(self, mock_get):
        target = "file:///etc/passwd"
        response = self.client.get(self._get_proxy_url(target), follow=True)

        assert response.status_code == 403
        mock_get.assert_not_called()
