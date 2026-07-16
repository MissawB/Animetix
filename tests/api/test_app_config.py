"""Tests du mode maintenance : endpoint /api/v1/config/ + middleware.

Le middleware bloque les requêtes /api/ en 503 quand le flag est ON, avec
exemptions (config, monitoring, staff). L'endpoint config est public, sans
throttle, et reflète le singleton SiteConfiguration.
"""

import pytest
from animetix.models import SiteConfiguration
from django.contrib.auth.models import User
from django.urls import reverse


def _set_maintenance(on: bool, message: str = "", until=None):
    config = SiteConfiguration.get_solo()
    config.maintenance_mode = on
    config.maintenance_message = message
    config.maintenance_until = until
    config.save()
    return config


# --------------------------------------------------------------------------- #
# GET /api/v1/config/
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_config_endpoint_defaults(api_client):
    resp = api_client.get(reverse("api_config"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["maintenance_mode"] is False
    assert data["maintenance_message"] == ""
    assert data["maintenance_until"] is None
    assert data["version"]


@pytest.mark.django_db
def test_config_endpoint_reflects_flag(api_client):
    _set_maintenance(True, message="Retour à 18h")
    data = api_client.get(reverse("api_config")).json()
    assert data["maintenance_mode"] is True
    assert data["maintenance_message"] == "Retour à 18h"


@pytest.mark.django_db
def test_config_singleton_single_row():
    SiteConfiguration.get_solo()
    other = SiteConfiguration(maintenance_mode=True)
    other.save()  # save() force pk=1 : pas de deuxième ligne
    assert SiteConfiguration.objects.count() == 1
    assert SiteConfiguration.get_solo().maintenance_mode is True


# --------------------------------------------------------------------------- #
# MaintenanceModeMiddleware
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_middleware_off_passthrough(api_client):
    _set_maintenance(False)
    resp = api_client.get(reverse("api_transparency"))
    assert resp.status_code != 503


@pytest.mark.django_db
def test_middleware_on_blocks_api(api_client):
    _set_maintenance(True)
    resp = api_client.get(reverse("api_transparency"))
    assert resp.status_code == 503
    data = resp.json()
    assert data["maintenance"] is True


@pytest.mark.django_db
def test_middleware_on_config_exempt(api_client):
    _set_maintenance(True)
    resp = api_client.get(reverse("api_config"))
    assert resp.status_code == 200
    assert resp.json()["maintenance_mode"] is True


@pytest.mark.django_db
def test_middleware_on_staff_session_bypass(api_client):
    _set_maintenance(True)
    staff = User.objects.create_user("cfgstaff", password="x", is_staff=True)
    api_client.force_login(staff)
    resp = api_client.get(reverse("api_transparency"))
    assert resp.status_code != 503


@pytest.mark.django_db
def test_middleware_on_non_staff_user_blocked(api_client):
    _set_maintenance(True)
    user = User.objects.create_user("cfguser", password="x")
    api_client.force_login(user)
    resp = api_client.get(reverse("api_transparency"))
    assert resp.status_code == 503


@pytest.mark.django_db
def test_middleware_ignores_non_api_paths(api_client):
    _set_maintenance(True)
    # Hors /api/ (SPA, statiques, admin) : jamais bloqué par le middleware.
    resp = api_client.get("/admin/login/")
    assert resp.status_code != 503


def test_middleware_fails_open_without_database():
    """Base indisponible (tests sans django_db, outage) → passthrough.

    Régression CI 2026-07-10 : le middleware interrogeait la base sur chaque
    requête /api/, faisant échouer en RuntimeError les tests d'endpoints qui
    n'ont pas besoin de la base (billing webhook, eventarc). La maintenance
    est un état déclaré, jamais l'effet de bord d'une panne.
    """
    from unittest.mock import MagicMock, patch

    from animetix.middleware import MaintenanceModeMiddleware
    from django.test import RequestFactory

    get_response = MagicMock(return_value="ok")
    middleware = MaintenanceModeMiddleware(get_response)
    request = RequestFactory().get("/api/v1/transparency/")

    with patch(
        "animetix.models.SiteConfiguration.get_solo",
        side_effect=RuntimeError("Database access not allowed"),
    ):
        result = middleware(request)

    assert result == "ok"
    get_response.assert_called_once_with(request)
