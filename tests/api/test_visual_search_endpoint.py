"""Le garde-fou anti-facturation devient « par cible ».

Ça permet de livrer en deux temps : l'index des œuvres part en production sans
celui des personnages, et chercher un personnage répond honnêtement « index non
construit » au lieu de facturer une liste vide.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from rest_framework.test import APIClient

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
    b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
    b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)


@contextmanager
def _visual(available: dict):
    service = MagicMock()
    service.is_available.side_effect = lambda target: available.get(target, False)
    service.encode_image.return_value = [0.1] * 512
    service.search.return_value = []
    container.core.visual_index_service.override(providers.Object(service))
    try:
        yield service
    finally:
        container.core.visual_index_service.reset_last_overriding()


@pytest.fixture
def api(db):
    client = APIClient()
    client.force_authenticate(User.objects.create_user("kenji"))
    return client


def _post(api, target):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return api.post(
        "/api/v1/media/search/",
        {"image": SimpleUploadedFile("a.png", PNG, "image/png"), "target": target},
        format="multipart",
    )


@pytest.mark.django_db
def test_an_empty_target_index_is_a_503_and_charges_nothing(api):
    with patch("animetix.api.core.media.deduct_berrix") as deduct:
        with _visual({"work": True, "character": False}):
            response = _post(api, "character")

    assert response.status_code == 503
    deduct.assert_not_called()


@pytest.mark.django_db
def test_a_built_target_index_charges_once_and_searches_its_own_collection(api):
    with patch("animetix.api.core.media.deduct_berrix") as deduct:
        with _visual({"work": True, "character": False}) as service:
            response = _post(api, "work")

    assert response.status_code == 200
    deduct.assert_called_once()
    service.encode_image.assert_called_once()
    assert service.search.call_args[0][0] == "work"


@pytest.mark.django_db
def test_an_unknown_target_is_a_400_and_charges_nothing(api):
    with patch("animetix.api.core.media.deduct_berrix") as deduct:
        with _visual({"work": True}):
            response = _post(api, "banana")

    assert response.status_code == 400
    deduct.assert_not_called()
