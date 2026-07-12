"""`sync_catalog` jetait les identifiants — et avec eux, cinq archétypes du World Boss.

`anime_themes.json` est indexé par id AniList, `anime_episodes.json` par id MAL. La
commande retirait `id`, `idMal` et `mal_id` des métadonnées : la base ne portait plus
que `external_id` (l'id MAL, ré-exposé sous `id`), et plus aucun opening ni épisode ne
se laissait retrouver. Les archétypes rendaient None, en silence.

Le piège de la correction : `_to_dict` fait `data.update(item.metadata)`. Remettre `id`
dans les métadonnées écraserait `data["id"] = item.external_id` et casserait
`id_to_full_data` (indexé sur `str(item["id"])`) — donc Akinetix, Quiz Who, Covertest et
le blind test avec. Les ids reviennent sous `idMal` et `anilist_id`, jamais sous `id`.
"""

import json

import pytest
from adapters.persistence.django_repository_adapter import DjangoRepositoryAdapter
from animetix.models import MediaItem
from django.core.management import call_command


@pytest.fixture
def synced(tmp_path, monkeypatch):
    from animetix.management.commands import sync_catalog

    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    (processed / "clean_root_animes.json").write_text(
        json.dumps(
            [
                {
                    "id": 101922,  # AniList — la clé des openings
                    "idMal": 38000,  # MAL — la clé des épisodes, et l'external_id
                    "title": "Kimetsu no Yaiba",
                    "popularity": 900000,
                    "genres": ["Action"],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sync_catalog.os.path, "abspath", lambda _p: str(tmp_path), raising=False
    )
    call_command("sync_catalog")
    return MediaItem.objects.get(media_type="Anime")


@pytest.mark.django_db
def test_sync_keeps_both_ids_in_the_metadata(synced):
    assert synced.external_id == "38000"
    assert synced.metadata["idMal"] == "38000"
    assert synced.metadata["anilist_id"] == "101922"
    # `id` ne doit PAS revenir dans les métadonnées : il écraserait `external_id`.
    assert "id" not in synced.metadata
    assert "mal_id" not in synced.metadata


@pytest.mark.django_db
def test_the_catalogue_dict_still_keys_on_the_external_id(synced):
    data = DjangoRepositoryAdapter()._to_dict(synced)

    # Le contrat que `id_to_full_data` et tous les autres jeux tiennent pour acquis.
    assert data["id"] == "38000"
    assert data["title"] == "Kimetsu no Yaiba"
    # Et, en plus, de quoi rejoindre openings et épisodes.
    assert data["idMal"] == "38000"
    assert data["anilist_id"] == "101922"
