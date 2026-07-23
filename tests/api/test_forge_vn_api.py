from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from animetix.models import CreativeFusion
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status


@pytest.fixture
def mock_user(db):
    user = User.objects.create_user(username="testuser", password="password")
    return user


@pytest.fixture
def other_user(db):
    user = User.objects.create_user(username="otheruser", password="password")
    return user


@pytest.fixture
def sample_fusion(db, mock_user):
    return CreativeFusion.objects.create(
        title_a="Anime A",
        title_b="Anime B",
        media_type_a="Anime",
        media_type_b="Anime",
        scenario_text="Un scénario épique.",
        creator=mock_user,
    )


@pytest.mark.django_db
class TestTheaterGallery:
    """Public VN gallery (TheaterListView) — bounded, N+1-free, field-whitelisted."""

    @staticmethod
    def _make_fusions(creator, count, script=True):
        return [
            CreativeFusion.objects.create(
                title_a=f"A{i}",
                title_b=f"B{i}",
                media_type_a="Anime",
                media_type_b="Anime",
                scenario_text="Scénario.",
                creator=creator,
                vn_script={"title": f"S{i}", "scenes": []} if script else None,
            )
            for i in range(count)
        ]

    def test_gallery_is_bounded(self, api_client, mock_user):
        from animetix.api.forge_vn import GALLERY_MAX_ITEMS

        self._make_fusions(mock_user, GALLERY_MAX_ITEMS + 5)
        url = reverse("api_theater_list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == GALLERY_MAX_ITEMS

    def test_gallery_query_count_does_not_grow_with_items(
        self, api_client, mock_user, other_user
    ):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        url = reverse("api_theater_list")
        api_client.get(url)  # warm-up (middleware get_or_create SiteConfiguration)

        for fusion in self._make_fusions(mock_user, 3):
            fusion.likes.add(mock_user, other_user)
        with CaptureQueriesContext(connection) as small:
            response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert all(item["likes_count"] == 2 for item in response.data)

        for fusion in self._make_fusions(mock_user, 7):
            fusion.likes.add(mock_user, other_user)
        with CaptureQueriesContext(connection) as large:
            response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 10

        # Sans prefetch, likes_count/creator_name émettent des requêtes PAR
        # LIGNE : passer de 3 à 10 items ferait grossir le décompte.
        assert len(large.captured_queries) == len(small.captured_queries)

    def test_gallery_does_not_expose_raw_liker_ids(self, api_client, mock_user):
        fusion = self._make_fusions(mock_user, 1)[0]
        fusion.likes.add(mock_user)
        url = reverse("api_theater_list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        item = response.data[0]
        assert "likes" not in item
        assert item["likes_count"] == 1
        assert item["creator_name"] == mock_user.username

    def test_gallery_is_liked_reflects_authenticated_user(
        self, api_client, mock_user, other_user
    ):
        liked, not_liked = self._make_fusions(mock_user, 2)
        liked.likes.add(other_user)
        api_client.force_authenticate(user=other_user)
        url = reverse("api_theater_list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        by_id = {item["id"]: item for item in response.data}
        assert by_id[liked.id]["is_liked"] is True
        assert by_id[not_liked.id]["is_liked"] is False


@pytest.mark.django_db
class TestForgeVNAPI:
    def test_get_vn_script(self, api_client, sample_fusion):
        url = reverse("api_forge_vn", kwargs={"fusion_id": sample_fusion.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["vn_script"] is None

    def test_generate_vn_script_unauthorized(
        self, api_client, other_user, sample_fusion
    ):
        api_client.force_authenticate(user=other_user)
        url = reverse("api_forge_vn", kwargs={"fusion_id": sample_fusion.id})
        data = {"action": "generate"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_generate_vn_script_success(
        self, api_client, mock_user, sample_fusion, mock_container
    ):
        api_client.force_authenticate(user=mock_user)
        url = reverse("api_forge_vn", kwargs={"fusion_id": sample_fusion.id})
        data = {"action": "generate"}

        mock_script_data = {
            "title": "Fusion Script",
            "scenes": [
                {
                    "character": "Protagonist",
                    "text": "Hello world",
                    "mood": "Happy",
                    "bg_prompt": "Forest",
                }
            ],
        }

        # Create a mock that behaves like a Pydantic model
        class MockScript:
            def model_dump(self):
                return mock_script_data

        # Configure the global mock_container
        mock_container.visual_novel_service.generate_script.return_value = MockScript()
        mock_container.visual_novel_service.return_value.generate_script.return_value = (
            MockScript()
        )

        mock_guardrail = MagicMock()
        mock_guardrail.validate_input.return_value = {"is_safe": True}
        mock_guardrail.validate_output.return_value = {"is_safe": True}

        mock_usage = MagicMock()
        mock_usage.check_quota.return_value = True

        with (
            container.core.visual_novel_service.override(
                providers.Object(mock_container.visual_novel_service)
            ),
            container.core.guardrail_service.override(providers.Object(mock_guardrail)),
            container.infrastructure.usage_port.override(providers.Object(mock_usage)),
        ):
            response = api_client.post(url, data, format="json")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["vn_script"]["title"] == "Fusion Script"

            # Verify persistence
            sample_fusion.refresh_from_db()
            assert sample_fusion.vn_script["title"] == "Fusion Script"

    @pytest.mark.integration  # exercises the live VN-script generation pipeline (no ollama in CI)
    def test_update_vn_script_success(self, api_client, mock_user, sample_fusion):
        api_client.force_authenticate(user=mock_user)
        url = reverse("api_forge_vn", kwargs={"fusion_id": sample_fusion.id})

        new_script = {"title": "Updated Title", "scenes": []}
        data = {"action": "update", "vn_script": new_script}

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["vn_script"]["title"] == "Updated Title"

        sample_fusion.refresh_from_db()
        assert sample_fusion.vn_script["title"] == "Updated Title"
