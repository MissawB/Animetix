from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from animetix.models import MediaItem
from django.urls import reverse
from rest_framework import status


@pytest.fixture
def mock_translator():
    m = MagicMock()
    m.translate_to_fr.return_value = "Synopsis en français."
    container.core.synopsis_translator.override(m)
    yield m
    container.core.synopsis_translator.reset_last_overriding()


@pytest.mark.django_db
def test_detail_translates_and_caches_on_first_view(api_client, mock_translator):
    MediaItem.objects.create(
        external_id="38000",
        media_type="Anime",
        title="Kimetsu no Yaiba",
        description="It is the Taisho era.",
    )
    url = reverse(
        "api_media_detail", kwargs={"media_type": "Anime", "item_id": "38000"}
    )

    r1 = api_client.get(url)
    assert r1.status_code == status.HTTP_200_OK
    assert r1.data["description"] == "Synopsis en français."
    mock_translator.translate_to_fr.assert_called_once_with(
        "Kimetsu no Yaiba", "It is the Taisho era."
    )
    # persisted
    assert (
        MediaItem.objects.get(external_id="38000").synopsis_fr
        == "Synopsis en français."
    )

    # second view: cache hit, no re-translation
    r2 = api_client.get(url)
    assert r2.data["description"] == "Synopsis en français."
    mock_translator.translate_to_fr.assert_called_once()  # still one call total


@pytest.mark.django_db
def test_detail_keeps_english_when_translation_fails(api_client):
    m = MagicMock()
    m.translate_to_fr.return_value = ""  # failure / no key
    container.core.synopsis_translator.override(m)
    try:
        MediaItem.objects.create(
            external_id="55",
            media_type="Anime",
            title="Show",
            description="English only.",
        )
        url = reverse(
            "api_media_detail", kwargs={"media_type": "Anime", "item_id": "55"}
        )
        r = api_client.get(url)
        assert r.data["description"] == "English only."
        assert MediaItem.objects.get(external_id="55").synopsis_fr in (None, "")
    finally:
        container.core.synopsis_translator.reset_last_overriding()
