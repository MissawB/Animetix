import pytest
from animetix.models import MediaItem
from django.urls import reverse
from rest_framework import status


def _mk_media(title="Kimetsu no Yaiba", external_id="38000"):
    return MediaItem.objects.create(
        external_id=external_id, media_type="Anime", title=title
    )


def _mk_char(external_id, name, origin, popularity):
    return MediaItem.objects.create(
        external_id=external_id,
        media_type="Character",
        title=name,
        popularity=popularity,
        image_url=f"https://img.example/{external_id}.png",
        metadata={"origin": origin},
    )


@pytest.mark.django_db
def test_characters_returned_sorted_by_popularity(api_client):
    _mk_media()
    _mk_char("1", "Zenitsu", "Kimetsu no Yaiba", 50)
    _mk_char("2", "Tanjirou", "Kimetsu no Yaiba", 100)
    _mk_char("3", "Levi", "Shingeki no Kyojin", 999)

    url = reverse(
        "api_media_characters",
        kwargs={"media_type": "Anime", "item_id": "38000"},
    )
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    chars = response.data["characters"]
    assert [c["name"] for c in chars] == ["Tanjirou", "Zenitsu"]
    assert chars[0]["id"] == "2"
    assert chars[0]["image"].startswith("https://img.example/")


@pytest.mark.django_db
def test_characters_empty_when_no_match(api_client):
    _mk_media(title="Obscure Show", external_id="777")
    url = reverse(
        "api_media_characters",
        kwargs={"media_type": "Anime", "item_id": "777"},
    )
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["characters"] == []


@pytest.mark.django_db
def test_characters_404_for_unknown_media(api_client):
    url = reverse(
        "api_media_characters",
        kwargs={"media_type": "Anime", "item_id": "999999"},
    )
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_characters_capped_at_12(api_client):
    _mk_media()
    for i in range(15):
        _mk_char(str(100 + i), f"Char{i}", "Kimetsu no Yaiba", i)
    url = reverse(
        "api_media_characters",
        kwargs={"media_type": "Anime", "item_id": "38000"},
    )
    response = api_client.get(url)
    assert len(response.data["characters"]) == 12
