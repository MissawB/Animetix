from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from animetix.models import MediaItem
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_detail_serves_english_without_translation(api_client):
    """La fiche sert le synopsis anglais tel quel : aucune traduction à la volée
    (l'appel Gemini rendait la première ouverture lente et peu fiable)."""
    translator = MagicMock()
    container.core.synopsis_translator.override(translator)
    try:
        MediaItem.objects.create(
            external_id="38000",
            media_type="Anime",
            title="Kimetsu no Yaiba",
            description="It is the Taisho era.",
        )
        url = reverse(
            "api_media_detail", kwargs={"media_type": "Anime", "item_id": "38000"}
        )

        r = api_client.get(url)
        assert r.status_code == status.HTTP_200_OK
        assert r.data["description"] == "It is the Taisho era."
        # Aucun appel de traduction, et rien n'est écrit en base.
        translator.translate_to_fr.assert_not_called()
        assert MediaItem.objects.get(external_id="38000").synopsis_fr in (None, "")
    finally:
        container.core.synopsis_translator.reset_last_overriding()


@pytest.mark.django_db
def test_detail_prefers_existing_french_synopsis(api_client):
    """Les fiches déjà traduites en base restent affichées en FR (le serializer
    préfère synopsis_fr quand il est présent)."""
    MediaItem.objects.create(
        external_id="55",
        media_type="Anime",
        title="Show",
        description="English only.",
        synopsis_fr="Synopsis en français.",
    )
    url = reverse("api_media_detail", kwargs={"media_type": "Anime", "item_id": "55"})
    r = api_client.get(url)
    assert r.status_code == status.HTTP_200_OK
    assert r.data["description"] == "Synopsis en français."
