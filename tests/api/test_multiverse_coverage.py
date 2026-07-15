"""Additional coverage for animetix.api.multiverse view module.

Complements tests/api/test_multiverse_api.py and test_multiverse_export.py by
exercising the uncovered branches: empty results, default/invalid query params,
incoming relations, and the description/cosmology/character/relation fallbacks.

The multiverse views resolve their Neo4j manager through the DI container via
``Provide[Container.persistence.graph_persistence_port]``; we override that
provider with an ``Object`` provider wrapping a MagicMock (same pattern as the
existing multiverse tests).
"""

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
    user = User.objects.create_user(username="mvuser", password="password")
    api_client.force_authenticate(user=user)
    return user


def _override(neo4j_mock):
    return container.persistence.graph_persistence_port.override(
        providers.Object(neo4j_mock)
    )


# --------------------------------------------------------------------------- #
# MultiverseGalleryView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_gallery_empty_results(api_client, authenticated_user):
    """No synthetic media -> empty nodes/links (success, empty graph)."""
    neo4j = MagicMock()
    neo4j.execute_query.return_value = []

    with _override(neo4j):
        response = api_client.get(reverse("api_multiverse_gallery"))

    assert response.status_code == 200
    body = response.json()
    assert body["nodes"] == []
    assert body["links"] == []


@pytest.mark.django_db
def test_gallery_skips_records_missing_media_or_genre(api_client, authenticated_user):
    """Records lacking media or genre are skipped (continue branch)."""
    genre = MagicMock()
    genre.get.side_effect = lambda k, d=None: {"name": "Seinen"}.get(k, d)

    neo4j = MagicMock()
    neo4j.execute_query.return_value = [
        {"m": None, "g": genre, "characters": []},  # missing media -> skipped
        {"m": MagicMock(), "g": None, "characters": []},  # missing genre -> skipped
    ]

    with _override(neo4j):
        response = api_client.get(reverse("api_multiverse_gallery"))

    assert response.status_code == 200
    body = response.json()
    assert body["nodes"] == []
    assert body["links"] == []


# --------------------------------------------------------------------------- #
# MultiverseCatalogView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_catalog_defaults_no_params(api_client, authenticated_user):
    """No query params -> defaults applied, empty data set still succeeds."""
    neo4j = MagicMock()
    neo4j.execute_query.side_effect = [
        [{"total": 0}],  # count
        [],  # data
        [],  # genres
    ]

    with _override(neo4j):
        response = api_client.get(reverse("api_multiverse_catalog"))

    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["page_size"] == 12
    assert body["pagination"]["total"] == 0
    assert body["pagination"]["total_pages"] == 1
    assert body["pagination"]["has_next"] is False
    assert body["pagination"]["has_previous"] is False
    assert body["filters"]["sort"] == "newest"
    assert body["available_genres"] == []


@pytest.mark.django_db
def test_catalog_invalid_page_params_fallback(api_client, authenticated_user):
    """Non-integer page/page_size fall back to defaults (except branches)."""
    neo4j = MagicMock()
    neo4j.execute_query.side_effect = [
        [{"total": 0}],
        [],
        [],
    ]

    with _override(neo4j):
        response = api_client.get(
            reverse("api_multiverse_catalog"),
            {"page": "abc", "page_size": "xyz", "sort": "unknown_sort"},
        )

    assert response.status_code == 200
    body = response.json()
    # invalid page/page_size -> defaults 1 / 12
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["page_size"] == 12
    # unknown sort still echoed in filters (mapped internally to default order)
    assert body["filters"]["sort"] == "unknown_sort"


@pytest.mark.django_db
def test_catalog_page_size_clamped_and_pagination_flags(api_client, authenticated_user):
    """page_size clamped to max 48; has_next/has_previous computed."""
    neo4j = MagicMock()
    neo4j.execute_query.side_effect = [
        [{"total": 100}],  # count -> multiple pages
        [
            {
                "media": {"title": "Fallback Title Universe"},  # name missing -> title
                "genre": {},  # genre name missing -> "Unknown"
                "characters": [],
                "char_count": 0,
            }
        ],
        [{"name": "Isekai", "count": 5}],
    ]

    with _override(neo4j):
        response = api_client.get(
            reverse("api_multiverse_catalog"),
            {"page": "2", "page_size": "999", "sort": "characters", "search": "x"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["page"] == 2
    assert body["pagination"]["page_size"] == 48  # clamped
    assert body["pagination"]["has_previous"] is True
    assert body["pagination"]["has_next"] is True
    # name/title + genre fallbacks
    result = body["results"][0]
    assert result["name"] == "Fallback Title Universe"
    assert result["genre"] == "Unknown"
    assert result["character_count"] == 0


@pytest.mark.django_db
def test_catalog_handles_empty_count_result(api_client, authenticated_user):
    """count_result empty list -> total defaults to 0 (ternary false branch)."""
    neo4j = MagicMock()
    neo4j.execute_query.side_effect = [
        [],  # count returns empty -> total = 0
        [],  # data
        None,  # genres None -> available_genres = []
    ]

    with _override(neo4j):
        response = api_client.get(reverse("api_multiverse_catalog"))

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 0
    assert body["available_genres"] == []


# --------------------------------------------------------------------------- #
# MultiverseExportPDFView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_export_pdf_fallbacks_no_chars_no_relations(api_client, authenticated_user):
    """Missing description/cosmology, no characters, no relations -> fallback text.

    Exercises the 'else' branches that print the placeholder messages and the
    incoming-relation handling is covered in a separate test below.
    """
    neo4j = MagicMock()
    neo4j.execute_query.side_effect = [
        # universe query: media without description/cosmology, no genre
        [{"media": {"name": "Bare Universe"}, "genre": None}],
        # characters query: empty
        [],
        # relations query: empty
        [],
    ]

    with _override(neo4j):
        response = api_client.get(
            reverse("api_multiverse_export_pdf", args=["Bare Universe"])
        )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    pdf = b"".join(response.streaming_content)
    assert pdf.startswith(b"%PDF")


@pytest.mark.django_db
def test_export_pdf_incoming_relation_and_title_fallback(
    api_client, authenticated_user
):
    """Incoming relation (is_outgoing False) + media uses 'title' fallback."""
    neo4j = MagicMock()
    neo4j.execute_query.side_effect = [
        # universe: 'title' instead of 'name', has genre
        [{"media": {"title": "Titled Universe"}, "genre": {"name": "Mecha"}}],
        # characters with one entry
        [{"character": {"name": "Pilot", "role": "Hero", "power_level": 42}}],
        # incoming relation: is_outgoing False, no labels -> "Entity"
        [
            {
                "rel_type": "INSPIRED_BY",
                "labels": [],
                "properties": {"title": "Some Concept"},
                "is_outgoing": False,
            },
            # relation without properties -> filtered out
            {"rel_type": "NOOP", "labels": ["X"], "properties": None},
        ],
    ]

    with _override(neo4j):
        response = api_client.get(
            reverse("api_multiverse_export_pdf", args=["Titled Universe"])
        )

    assert response.status_code == 200
    pdf = b"".join(response.streaming_content)
    assert pdf.startswith(b"%PDF")


@pytest.mark.django_db
def test_export_pdf_sanitizes_empty_filename(api_client, authenticated_user):
    """A universe name with only special chars -> filename falls back to default."""
    neo4j = MagicMock()
    neo4j.execute_query.side_effect = [
        [{"media": {"name": "***"}, "genre": {"name": "G"}}],
        [],
        [],
    ]

    with _override(neo4j):
        response = api_client.get(reverse("api_multiverse_export_pdf", args=["***"]))

    assert response.status_code == 200
    # safe_filename empty -> "multiverse_lore"
    assert "wiki_multiverse_lore.pdf" in response["Content-Disposition"]


def test_multiverse_service_methods():
    from core.domain.services.multiverse_service import MultiverseService

    neo4j = MagicMock()
    service = MultiverseService(neo4j)

    # test gallery
    service.get_gallery_raw_data()
    assert neo4j.execute_query.call_count == 1

    # test catalog
    neo4j.execute_query.side_effect = [[{"total": 1}], [{"media": {}}], [{"name": "G"}]]
    service.get_catalog_raw_data()
    assert neo4j.execute_query.call_count == 4  # 1 previous + 3 for catalog

    # test pdf raw data
    neo4j.execute_query.side_effect = [
        [{"media": {}}],
        [{"character": {}}],
        [{"properties": {}}],
    ]
    service.get_universe_pdf_raw_data("Test")
    assert neo4j.execute_query.call_count == 7


def test_multiverse_presenter_methods():
    from animetix.presenters import MultiversePresenter

    # test format gallery
    res_gallery = MultiversePresenter.format_gallery_data(
        [{"m": {"name": "M"}, "g": {"name": "G"}}]
    )
    assert len(res_gallery["nodes"]) == 2

    # test format catalog
    res_catalog = MultiversePresenter.format_catalog_data(
        results=[{"media": {"name": "M"}, "genre": {"name": "G"}}],
        total=1,
        page=1,
        page_size=10,
        search="",
        genre_filter="",
        sort_by="newest",
        genre_results=[{"name": "G", "count": 1}],
    )
    assert res_catalog["results"][0]["name"] == "M"

    # test generate PDF
    pdf_buffer = MultiversePresenter.generate_lore_pdf(
        "Test",
        {
            "media": {"name": "Test", "description": "Desc", "cosmology": "Cosmo"},
            "genre": {"name": "G"},
            "characters": [{"name": "Char", "role": "Role", "power_level": 100}],
            "relations": [
                {
                    "rel_type": "T",
                    "labels": ["L"],
                    "properties": {"name": "N"},
                    "is_outgoing": True,
                }
            ],
        },
    )
    assert pdf_buffer.getvalue().startswith(b"%PDF")
