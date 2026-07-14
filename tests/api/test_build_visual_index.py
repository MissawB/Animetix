"""Le constructeur d'index doit être reprenable, et une image morte ne doit
jamais coûter le lot.

44 000 téléchargements sur une ligne domestique, ça casse. Une reprise doit
coûter ce qui reste — pas tout. (Le fetch Kitsu a mordu exactement là.)
"""

from unittest.mock import MagicMock, patch

import pytest
from animetix.models import MediaItem
from django.core.management import call_command


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
    svc.indexed_ids = set()
    return svc


def _run(target, service, downloads=None, **kwargs):
    downloads = downloads or {
        "http://img/a": b"A",
        "http://img/b": b"B",
        "http://img/c": b"C",
    }
    with patch("animetix.management.commands.build_visual_index._download") as dl:
        dl.side_effect = lambda url: downloads.get(url)
        with patch(
            "animetix.management.commands.build_visual_index._service",
            return_value=service,
        ):
            call_command("build_visual_index", target=target, **kwargs)
    return service


@pytest.mark.django_db
def test_it_only_indexes_the_media_types_of_its_target(catalogue, service):
    _run("work", service)
    indexed = [
        i["external_id"] for call in service.index.call_args_list for i in call[0][1]
    ]
    assert set(indexed) == {"38000", "1535"}  # le personnage n'est pas une œuvre


@pytest.mark.django_db
def test_a_dead_image_is_skipped_not_fatal(catalogue, service):
    _run("work", service, downloads={"http://img/b": b"B"})  # la première 404
    indexed = [
        i["external_id"] for call in service.index.call_args_list for i in call[0][1]
    ]
    assert indexed == ["1535"]


@pytest.mark.django_db
def test_a_rerun_does_not_re_encode_what_is_already_indexed(catalogue, service):
    service.indexed_ids = {"38000"}
    _run("work", service)
    indexed = [
        i["external_id"] for call in service.index.call_args_list for i in call[0][1]
    ]
    assert indexed == ["1535"]


@pytest.mark.django_db
def test_it_refuses_an_unknown_target(catalogue, service):
    with pytest.raises(Exception):
        _run("banana", service)
