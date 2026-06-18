import pytest
import base64
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestSSRFProtection:
    def setup_method(self):
        self.client = APIClient()
        self.url_name = "cdn_proxy"

    def _get_proxy_url(self, target_url):
        from core.utils.security import sign_proxy_url  # noqa: E402

        encoded = base64.b64encode(target_url.encode()).decode()
        sig = sign_proxy_url(target_url)
        return f"{reverse(self.url_name)}?url={encoded}&sig={sig}"

    def test_proxy_allows_external_url(self):
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        # 1x1 transparent GIF bytes to pass validate_file_mime_type
        mock_response.content = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        mock_response.headers = {"Content-Type": "image/gif"}

        with patch("animetix.api.core.safe_http_request") as mock_get:
            mock_get.return_value = mock_response

            target = "https://example.com/image.gif"
            response = self.client.get(self._get_proxy_url(target))

            assert response.status_code == 200
            assert response.content == mock_response.content
            mock_get.assert_called_once()

    @patch("requests.get")
    def test_proxy_blocks_internal_ip_loopback(self, mock_get):
        target = "http://127.0.0.1:8000/admin/"
        response = self.client.get(self._get_proxy_url(target), follow=True)

        # We want it to return 403 and NOT call requests.get
        assert response.status_code == 403
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_proxy_blocks_private_ip_range(self, mock_get):
        target = "http://192.168.1.1/setup"
        response = self.client.get(self._get_proxy_url(target), follow=True)

        assert response.status_code == 403
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_proxy_blocks_invalid_scheme(self, mock_get):
        target = "file:///etc/passwd"
        response = self.client.get(self._get_proxy_url(target), follow=True)

        assert response.status_code == 403
        mock_get.assert_not_called()
