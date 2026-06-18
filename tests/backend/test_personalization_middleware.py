import json
from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from animetix.middleware import PersonalizationMiddleware
from core.domain.entities.personalization import VisualConfig
from dependency_injector import providers
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory


@pytest.mark.django_db
class TestPersonalizationMiddleware:
    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="test_personalization_user", password="password"
        )
        # Ensure cache is completely clear before each test
        cache.clear()

    def test_unauthenticated_request_bypasses_caching(self):
        # Setup mock response
        def get_response(request):
            response = JsonResponse({"status": "ok"})
            return response

        # Setup mock drift service
        mock_drift_service = MagicMock()

        middleware = PersonalizationMiddleware(get_response)
        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False

        with container.core.archetype_drift_service.override(
            providers.Object(mock_drift_service)
        ):
            response = middleware(request)

            # Verify calculate_drift was not called
            mock_drift_service.calculate_drift.assert_not_called()

            # Response should remain unchanged
            data = json.loads(response.content)
            assert "meta" not in data

    def test_authenticated_json_request_caches_visual_config(self):
        # Setup mock response
        def get_response(request):
            response = JsonResponse({"status": "ok"})
            return response

        # Setup mock drift service
        mock_drift_service = MagicMock()
        mock_config = VisualConfig(
            archetype_id="shonen_hero",
            primary_accent="#FD7706",
            aura_type="fire",
            aura_intensity=1.0,
            font_vibe="manga",
        )
        mock_drift_service.calculate_drift.return_value = mock_config

        middleware = PersonalizationMiddleware(get_response)
        request = self.factory.get("/")
        request.user = self.user

        with container.core.archetype_drift_service.override(
            providers.Object(mock_drift_service)
        ):
            # First request: should hit service and write to cache
            response1 = middleware(request)
            data1 = json.loads(response1.content)
            assert data1["meta"]["visual_config"]["archetype_id"] == "shonen_hero"
            mock_drift_service.calculate_drift.assert_called_once()

            # Verify it wrote to cache
            cache_key = f"personalization_drift_user_{self.user.id}"
            cached_data = cache.get(cache_key)
            assert cached_data is not None
            assert cached_data["archetype_id"] == "shonen_hero"

            # Reset call count
            mock_drift_service.calculate_drift.reset_mock()

            # Second request: should hit cache and NOT call the service again
            response2 = middleware(request)
            data2 = json.loads(response2.content)
            assert data2["meta"]["visual_config"]["archetype_id"] == "shonen_hero"
            mock_drift_service.calculate_drift.assert_not_called()

    def test_non_json_response_bypasses_caching(self):
        def get_response(request):
            return HttpResponse("Hello World", content_type="text/plain")

        mock_drift_service = MagicMock()
        middleware = PersonalizationMiddleware(get_response)
        request = self.factory.get("/")
        request.user = self.user

        with container.core.archetype_drift_service.override(
            providers.Object(mock_drift_service)
        ):
            response = middleware(request)
            mock_drift_service.calculate_drift.assert_not_called()
            assert response.content == b"Hello World"
