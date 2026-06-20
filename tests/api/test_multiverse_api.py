from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user(api_client, db):
    user = User.objects.create_user(username="testuser", password="password")
    api_client.force_authenticate(user=user)
    return user


@pytest.mark.django_db
def test_multiverse_gallery_view(api_client, authenticated_user, mock_container):
    # Mock Neo4j execute_query for Gallery
    # Record format: m (media), g (genre), characters (list of characters)
    mock_media = MagicMock()
    mock_media.get.side_effect = lambda key, default=None: {
        "name": "Synthetic Naruto",
        "description": "A synthetic ninja world",
        "cosmology": "Chakra system",
    }.get(key, default)

    mock_genre = MagicMock()
    mock_genre.get.side_effect = lambda key, default=None: {
        "name": "Shonen",
    }.get(key, default)

    mock_char = MagicMock()
    mock_char.get.side_effect = lambda key, default=None: {
        "name": "Boruto",
    }.get(key, default)

    mock_record = {
        "m": mock_media,
        "g": mock_genre,
        "characters": [mock_char],
    }

    mock_container.graph_persistence_port.execute_query.return_value = [mock_record]

    with container.persistence.graph_persistence_port.override(
        providers.Object(mock_container.graph_persistence_port)
    ):
        url = reverse("api_multiverse_gallery")
        response = api_client.get(url)

        assert response.status_code == 200
        res_json = response.json()
        assert "nodes" in res_json
        assert "links" in res_json

        # Verify nodes formatting
        nodes = res_json["nodes"]
        assert any(n["id"] == "genre_Shonen" and n["type"] == "genre" for n in nodes)
        assert any(
            n["id"] == "Synthetic Naruto"
            and n["type"] == "universe"
            and n["metadata"]["description"] == "A synthetic ninja world"
            for n in nodes
        )

        # Verify links formatting
        links = res_json["links"]
        assert any(
            link["source"] == "Synthetic Naruto" and link["target"] == "genre_Shonen"
            for link in links
        )


@pytest.mark.django_db
def test_multiverse_catalog_view(api_client, authenticated_user, mock_container):
    # Mock Neo4j execute_query calls for:
    # 1. Count query
    # 2. Main data query
    # 3. Available genres query
    mock_container.graph_persistence_port.execute_query.side_effect = [
        [{"total": 1}],  # Count result
        [  # Data result
            {
                "media": {
                    "name": "Synthetic One Piece",
                    "description": "Pirates and oceans",
                    "cosmology": "Devil fruits",
                    "created_at": "2026-06-19T00:00:00Z",
                },
                "genre": {"name": "Shonen"},
                "characters": [
                    {"name": "Luffy", "role": "Protagonist", "power_level": 9000}
                ],
                "char_count": 1,
            }
        ],
        [{"name": "Shonen", "count": 1}],  # Genres result
    ]

    with container.persistence.graph_persistence_port.override(
        providers.Object(mock_container.graph_persistence_port)
    ):
        url = reverse("api_multiverse_catalog")
        response = api_client.get(
            url,
            {
                "search": "Pirate",
                "genre": "Shonen",
                "sort": "newest",
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        res_json = response.json()

        # Verify pagination
        assert "pagination" in res_json
        assert res_json["pagination"]["total"] == 1
        assert res_json["pagination"]["total_pages"] == 1

        # Verify results
        assert "results" in res_json
        assert len(res_json["results"]) == 1
        univ = res_json["results"][0]
        assert univ["name"] == "Synthetic One Piece"
        assert univ["genre"] == "Shonen"
        assert len(univ["characters"]) == 1
        assert univ["characters"][0]["name"] == "Luffy"

        # Verify filters echoed back
        assert "filters" in res_json
        assert res_json["filters"]["search"] == "Pirate"
        assert res_json["filters"]["genre"] == "Shonen"
        assert res_json["filters"]["sort"] == "newest"

        # Verify available genres list
        assert "available_genres" in res_json
        assert res_json["available_genres"][0]["name"] == "Shonen"
        assert res_json["available_genres"][0]["count"] == 1
