"""Le constructeur d'index doit être reprenable, et une image morte ne doit
jamais coûter le lot.

44 000 téléchargements sur une ligne domestique, ça casse. Une reprise doit
coûter ce qui reste — pas tout. (Le fetch Kitsu a mordu exactement là.)

Trois choses que ces tests tiennent, et qu'aucun ne tenait avant :

1. La clé d'un vecteur est `media_type:external_id`. `external_id` n'est unique
   que PAR type de média (`MediaItem.Meta.unique_together`), et la cible `work`
   verse Anime + Manga + Movie + Game dans UNE collection : l'anime n°1 (MAL) et
   le film n°1 (TMDB) s'écrasaient l'un l'autre — vecteur ET métadonnées.
2. Une écriture qui échoue n'a pas le droit d'être verte. Le dépôt journalise et
   rend la main : sans écriture stricte, la commande annonçait des vecteurs qui
   n'existent pas.
3. La reprise passe par la VRAIE table `VectorRecord`, jamais par un attribut de
   doublure que la production ne porte pas.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from animetix.models import MediaItem, VectorRecord
from core.ports.inference_port import InferencePort
from django.core.management import call_command
from django.core.management.base import CommandError

COLLECTION = "unified_clip_space"


@pytest.fixture
def catalogue(db):
    MediaItem.objects.create(
        external_id="38000",
        media_type="Anime",
        title="Kimetsu",
        image_url="http://img/a",
    )
    MediaItem.objects.create(
        external_id="1535",
        media_type="Anime",
        title="Death Note",
        image_url="http://img/b",
    )
    MediaItem.objects.create(
        external_id="99", media_type="Character", title="Levi", image_url="http://img/c"
    )


@pytest.fixture
def service():
    svc = MagicMock()
    svc.index.return_value = 2
    return svc


def _run(target, service, downloads=None, **kwargs):
    downloads = downloads or {
        "http://img/a": b"A",
        "http://img/b": b"B",
        "http://img/c": b"C",
    }
    fetch = downloads if callable(downloads) else lambda url: downloads.get(url)
    with patch("animetix.management.commands.build_visual_index._download") as dl:
        dl.side_effect = fetch
        with patch(
            "animetix.management.commands.build_visual_index._service",
            return_value=service,
        ):
            call_command("build_visual_index", target=target, **kwargs)
    return service


def _indexed(service):
    """Les external_id (nus) des items réellement remis au service."""
    return [
        i["external_id"] for call in service.index.call_args_list for i in call[0][1]
    ]


@pytest.mark.django_db
def test_it_only_indexes_the_media_types_of_its_target(catalogue, service):
    _run("work", service)
    # le personnage n'est pas une œuvre
    assert set(_indexed(service)) == {"38000", "1535"}


@pytest.mark.django_db
def test_a_dead_image_is_skipped_not_fatal(catalogue, service):
    _run("work", service, downloads={"http://img/b": b"B"})  # la première 404
    assert _indexed(service) == ["1535"]


@pytest.mark.django_db
def test_a_download_that_raises_is_skipped_not_fatal(catalogue, service):
    """Un timeout LÈVE, il ne rend pas `None`. Le lot doit y survivre aussi."""

    def fetch(url):
        if url == "http://img/a":
            raise httpx.ConnectTimeout("la ligne a lâché")
        return {"http://img/b": b"B"}.get(url)

    _run("work", service, downloads=fetch)
    assert _indexed(service) == ["1535"]


@pytest.mark.django_db
def test_the_metadata_written_is_what_the_user_will_see(catalogue, service):
    """Le lecteur rend ce lot tel quel au sérialiseur : on l'épingle."""
    _run("work", service, downloads={"http://img/a": b"A"})
    item = service.index.call_args[0][1][0]
    assert item["external_id"] == "38000"
    assert item["media_type"] == "Anime"
    assert item["title"] == "Kimetsu"
    assert item["image"] == "http://img/a"
    assert item["image_bytes"] == b"A"


@pytest.mark.django_db
def test_each_batch_is_written_as_it_fills(catalogue, service):
    """Une interruption ne doit coûter qu'un lot — encore faut-il qu'il y en ait
    plusieurs. Avec le lot par défaut (100) et trois lignes, la branche de vidage
    en cours de boucle n'était jamais exécutée par un test."""
    MediaItem.objects.create(
        external_id="5114", media_type="Anime", title="FMA", image_url="http://img/d"
    )
    _run(
        "work",
        service,
        downloads={"http://img/a": b"A", "http://img/b": b"B", "http://img/d": b"D"},
        batch_size=2,
    )
    sizes = [len(call[0][1]) for call in service.index.call_args_list]
    assert sizes == [2, 1]  # vidé dès qu'il est plein, puis le reste


# --------------------------------------------------------------------------
# La reprise — contre la VRAIE table, jamais contre un attribut de doublure.
# --------------------------------------------------------------------------


def _already_indexed(item_id, collection=COLLECTION):
    VectorRecord.objects.create(
        collection_name=collection, item_id=item_id, embedding=[0.1, 0.2], metadata={}
    )


@pytest.mark.django_db
def test_a_rerun_does_not_re_encode_what_is_already_indexed(catalogue, service):
    _already_indexed("Anime:38000")
    _run("work", service)
    assert _indexed(service) == ["1535"]


@pytest.mark.django_db
def test_a_bare_external_id_does_not_count_as_indexed(catalogue, service):
    """La collection est clavetée en `media_type:external_id` : un « 38000 » nu
    n'y est jamais. Le prendre pour une reprise sauterait une œuvre qui n'a
    aucun vecteur."""
    _already_indexed("38000")
    _run("work", service)
    assert set(_indexed(service)) == {"38000", "1535"}


@pytest.mark.django_db
def test_another_collection_does_not_count_as_indexed(catalogue, service):
    """La reprise est bornée à la collection de la cible. Sans ce filtre, un
    vecteur de personnage ferait sauter une œuvre."""
    _already_indexed("Anime:38000", collection="character_ccip_space")
    _run("work", service)
    assert set(_indexed(service)) == {"38000", "1535"}


# --------------------------------------------------------------------------
# La clé composite, de bout en bout : on écrit, PUIS on relit par le chemin du
# lecteur. Deux items de types différents partagent l'external_id « 1 ».
# --------------------------------------------------------------------------


class _FakeVectorSpace:
    """Un seul stockage, deux rôles : l'écrivain (`upsert_items`, RepositoryPort)
    et le lecteur (`search_by_vector`, VectorStorePort). Le jour où les deux ne
    construisent plus la clé au même endroit, ce test le voit."""

    def __init__(self):
        self.rows = {}  # (collection, id) -> (vecteur, métadonnées)

    def upsert_items(
        self, collection_name, ids, embeddings, metadatas, documents=None, strict=False
    ):
        for i, item_id in enumerate(ids):
            self.rows[(collection_name, item_id)] = (embeddings[i], metadatas[i])

    def search_by_vector(self, collection_name, query_vector, limit=10):
        def distance(vector):
            return sum((a - b) ** 2 for a, b in zip(vector, query_vector))

        found = sorted(
            (
                (distance(vector), item_id, metadata)
                for (coll, item_id), (vector, metadata) in self.rows.items()
                if coll == collection_name
            ),
            key=lambda row: row[0],
        )
        return [dict(metadata, id=item_id) for _, item_id, metadata in found[:limit]]


@pytest.fixture
def collision(db):
    """Anime n°1 (MAL) et Film n°1 (TMDB) : deux espaces d'identifiants
    indépendants, un même entier, UNE seule collection."""
    MediaItem.objects.create(
        external_id="1",
        media_type="Anime",
        title="Cowboy Bebop",
        image_url="http://img/anime",
    )
    MediaItem.objects.create(
        external_id="1",
        media_type="Movie",
        title="Toy Story",
        image_url="http://img/movie",
    )


@pytest.mark.django_db
def test_the_item_indexed_is_the_item_the_reader_finds(collision):
    from core.domain.services.visual_index import VisualIndexService

    space = _FakeVectorSpace()
    engine = MagicMock(spec=InferencePort)
    engine.get_image_embedding.side_effect = lambda data, model_id=None: {
        b"ANIME": [1.0, 0.0],
        b"MOVIE": [0.0, 1.0],
    }[data]
    real = VisualIndexService(
        inference_engine=engine, repository=space, vector_store=space
    )

    _run(
        "work",
        real,
        downloads={"http://img/anime": b"ANIME", "http://img/movie": b"MOVIE"},
    )

    # Les deux vecteurs coexistent : aucun n'a écrasé l'autre. La clé est une
    # concaténation pure -- `media_type` garde la casse que `MediaItem` lui
    # donne ("Anime", "Movie"), jamais forcée en minuscules.
    assert set(space.rows) == {(COLLECTION, "Anime:1"), (COLLECTION, "Movie:1")}

    # Le chemin du lecteur : on cherche avec le vecteur de l'anime, on doit
    # retrouver l'ANIME — pas le film qui porte le même external_id nu.
    found = real.search("work", [1.0, 0.0], limit=1)[0]
    assert found["id"] == "Anime:1"
    assert found["title"] == "Cowboy Bebop"
    assert found["media_type"] == "Anime"
    assert found["external_id"] == "1"  # l'utilisateur voit toujours l'id nu
    assert found["image"] == "http://img/anime"

    # Le lecteur ne connait que les métadonnées qu'il vient de lire -- il doit
    # retrouver le MÊME id en rebâtissant la clé avec `vector_key`, jamais en
    # la reconstruisant à la main (un `f"{media_type}:{external_id}"` avec la
    # mauvaise casse ne lèverait rien : la recherche ne rendrait juste plus
    # rien).
    from core.domain.services.visual_index import vector_key

    assert found["id"] == vector_key(found["media_type"], found["external_id"])


# --------------------------------------------------------------------------
# Une écriture qui échoue n'a pas le droit d'être verte.
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_failed_write_is_never_announced_as_a_success(catalogue, service, capsys):
    service.index.side_effect = RuntimeError("dimension mismatch")

    with pytest.raises(CommandError):
        _run("work", service)

    assert "vecteurs écrits" not in capsys.readouterr().out


@pytest.mark.django_db
def test_it_refuses_an_unknown_target(catalogue, service):
    """Le garde-fou de `handle()` lui-même : `choices=` d'argparse n'est qu'une
    porte, la commande peut être appelée par programme."""
    from animetix.management.commands.build_visual_index import Command

    with pytest.raises(CommandError):
        Command().handle(target="banana", limit=None, batch_size=100)


@pytest.mark.django_db
def test_argparse_also_refuses_an_unknown_target(catalogue, service):
    with pytest.raises(CommandError):
        _run("banana", service)
