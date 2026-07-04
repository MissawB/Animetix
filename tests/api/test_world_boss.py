from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from animetix.containers import container
from animetix.models import BossParticipation, GlobalBoss
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.fixture
def active_boss(db):
    return GlobalBoss.objects.create(
        title="Test Boss",
        secret_title="One Piece",
        media_type="anime",
        total_hp=1000,
        current_hp=1000,
        end_date=timezone.now() + timedelta(days=1),
        is_active=True,
    )


@pytest.mark.django_db
def test_active_boss_view(api_client, active_boss):
    url = reverse("api_world_boss_active")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data["title"] == "Test Boss"


@pytest.mark.django_db
def test_boss_attack_correct(api_client, user, active_boss):
    api_client.force_authenticate(user=user)
    url = reverse("api_world_boss_attack")
    data = {"boss_id": active_boss.id, "guess": "One Piece"}
    response = api_client.post(url, data)
    assert response.status_code == 200
    assert response.data["is_correct"] is True
    assert response.data["damage_dealt"] == 100

    active_boss.refresh_from_db()
    assert active_boss.current_hp == 900


@pytest.mark.django_db
def test_boss_attack_incorrect(api_client, user, active_boss):
    api_client.force_authenticate(user=user)
    url = reverse("api_world_boss_attack")
    data = {"boss_id": active_boss.id, "guess": "Naruto"}
    response = api_client.post(url, data)
    assert response.status_code == 200
    assert response.data["is_correct"] is False
    assert response.data["damage_dealt"] == 0


# --------------------------------------------------------------------------- #
# Spawn automatique hebdomadaire (le mode ne "marchait" jamais : aucun
# mécanisme ne créait de boss, l'endpoint /active/ renvoyait toujours 404).
# --------------------------------------------------------------------------- #
_CATALOG = {
    "db": [
        {
            "title": "One Piece",
            "genres": ["Action", "Adventure"],
            "year": 1999,
            "studios": ["Toei Animation"],
        },
        {
            "title": "Naruto",
            "genres": ["Action"],
            "year": 2002,
            "studios": ["Pierrot"],
        },
    ]
}


def _catalog_override():
    cat = MagicMock()
    cat.load_data.return_value = _CATALOG
    return container.core.catalog_service.override(providers.Object(cat))


@pytest.mark.django_db
def test_active_view_spawns_weekly_boss_when_none(api_client):
    with _catalog_override():
        response = api_client.get(reverse("api_world_boss_active"))
    assert response.status_code == 200
    assert GlobalBoss.objects.count() == 1
    boss = GlobalBoss.objects.get()
    # La solution ne doit jamais fuiter : ni dans la réponse, ni via le titre
    # affiché (nom de code).
    assert "secret_title" not in response.data
    assert boss.title != boss.secret_title
    assert boss.secret_title in {"One Piece", "Naruto"}
    assert boss.current_hp == boss.total_hp
    assert boss.community_hints
    assert boss.end_date > timezone.now()


@pytest.mark.django_db
def test_active_view_does_not_duplicate_boss(api_client):
    with _catalog_override():
        api_client.get(reverse("api_world_boss_active"))
        response = api_client.get(reverse("api_world_boss_active"))
    assert response.status_code == 200
    assert GlobalBoss.objects.count() == 1


@pytest.mark.django_db
def test_defeated_boss_not_respawned_before_expiry(api_client):
    """Un boss vaincu (désactivé) reste 'la semaine en cours' : pas de respawn
    du même boss — sinon la communauté connaît déjà la réponse."""
    GlobalBoss.objects.create(
        title="RAID VAINCU",
        secret_title="One Piece",
        media_type="Anime",
        total_hp=1000,
        current_hp=0,
        is_active=False,
        end_date=timezone.now() + timedelta(days=3),
    )
    with _catalog_override():
        response = api_client.get(reverse("api_world_boss_active"))
    assert response.status_code == 404
    assert GlobalBoss.objects.count() == 1


@pytest.mark.django_db
def test_attack_deactivates_boss_at_zero_hp(api_client, user):
    boss = GlobalBoss.objects.create(
        title="RAID FINAL",
        secret_title="One Piece",
        media_type="Anime",
        total_hp=1000,
        current_hp=100,
        end_date=timezone.now() + timedelta(days=1),
    )
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("api_world_boss_attack"),
        {"boss_id": boss.id, "guess": "One Piece"},
    )
    assert response.status_code == 200
    boss.refresh_from_db()
    assert boss.current_hp == 0
    assert boss.is_active is False


@pytest.mark.django_db
def test_attack_survives_channel_layer_outage(api_client, user):
    """La notification de phase est best-effort : un channel layer indisponible
    (Redis down en prod) ne doit pas transformer une attaque en 500."""
    boss = GlobalBoss.objects.create(
        title="RAID OMEGA",
        secret_title="One Piece",
        media_type="Anime",
        total_hp=1000,
        current_hp=550,  # 550 -> 450 : passage en phase 2, broadcast tenté
        end_date=timezone.now() + timedelta(days=1),
    )
    api_client.force_authenticate(user=user)
    with patch(
        "animetix.signals.get_channel_layer",
        side_effect=RuntimeError("redis down"),
    ):
        response = api_client.post(
            reverse("api_world_boss_attack"),
            {"boss_id": boss.id, "guess": "One Piece"},
        )
    assert response.status_code == 200
    assert response.data["current_phase"] == 2


@pytest.mark.django_db
def test_phase_broadcast_only_on_phase_change(api_client, user, active_boss):
    """1000 -> 900 HP reste en phase 1 : pas d'alerte globale à chaque coup."""
    api_client.force_authenticate(user=user)
    with patch("animetix.signals.get_channel_layer") as get_layer:
        response = api_client.post(
            reverse("api_world_boss_attack"),
            {"boss_id": active_boss.id, "guess": "One Piece"},
        )
    assert response.status_code == 200
    get_layer.assert_not_called()


# --------------------------------------------------------------------------- #
# Distribution de la récompense XP à la défaite du boss.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_defeat_distributes_reward_to_all_participants(api_client):
    finisher = User.objects.create_user(username="finisher", password="x")
    helper = User.objects.create_user(username="helper", password="x")
    finisher.profile.xp = 0
    finisher.profile.save()
    helper.profile.xp = 50
    helper.profile.save()

    boss = GlobalBoss.objects.create(
        title="RAID FINAL",
        secret_title="One Piece",
        media_type="Anime",
        total_hp=1000,
        current_hp=100,  # Un seul coup correct suffit à le vaincre.
        reward_xp=1000,
        end_date=timezone.now() + timedelta(days=1),
    )
    # Le helper a déjà contribué sans porter le coup fatal.
    BossParticipation.objects.create(user=helper, boss=boss, points_contributed=200)

    api_client.force_authenticate(user=finisher)
    resp = api_client.post(
        reverse("api_world_boss_attack"),
        {"boss_id": boss.id, "guess": "One Piece"},
    )
    assert resp.status_code == 200

    boss.refresh_from_db()
    assert boss.current_hp == 0
    assert boss.is_active is False
    assert boss.reward_distributed is True

    finisher.profile.refresh_from_db()
    helper.profile.refresh_from_db()
    # Tous les participants (dont le finisher, inscrit par ce coup) touchent la
    # récompense complète.
    assert finisher.profile.xp == 1000
    assert helper.profile.xp == 50 + 1000


@pytest.mark.django_db
def test_non_defeating_attack_does_not_distribute_reward(api_client, user, active_boss):
    active_boss.reward_xp = 1000
    active_boss.save()
    user.profile.xp = 0
    user.profile.save()

    api_client.force_authenticate(user=user)
    resp = api_client.post(
        reverse("api_world_boss_attack"),
        {"boss_id": active_boss.id, "guess": "One Piece"},
    )
    assert resp.status_code == 200

    active_boss.refresh_from_db()
    assert active_boss.current_hp == 900
    assert active_boss.reward_distributed is False
    user.profile.refresh_from_db()
    # Seuls les dégâts sont comptés, aucune XP de raid tant qu'il vit.
    assert user.profile.xp == 0


@pytest.mark.django_db
def test_reward_distributed_at_most_once(api_client, user):
    """Un boss déjà récompensé ne redistribue pas si l'état est rejoué."""
    boss = GlobalBoss.objects.create(
        title="RAID CLOS",
        secret_title="One Piece",
        media_type="Anime",
        total_hp=1000,
        current_hp=100,
        reward_xp=1000,
        reward_distributed=True,  # Déjà distribué.
        is_active=True,
        end_date=timezone.now() + timedelta(days=1),
    )
    user.profile.xp = 0
    user.profile.save()

    api_client.force_authenticate(user=user)
    resp = api_client.post(
        reverse("api_world_boss_attack"),
        {"boss_id": boss.id, "guess": "One Piece"},
    )
    assert resp.status_code == 200
    user.profile.refresh_from_db()
    assert user.profile.xp == 0


# --------------------------------------------------------------------------- #
# Classement des contributeurs.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_leaderboard_returns_top_contributors_sorted(api_client, active_boss):
    top = User.objects.create_user(username="top", password="x")
    mid = User.objects.create_user(username="mid", password="x")
    BossParticipation.objects.create(user=mid, boss=active_boss, points_contributed=300)
    BossParticipation.objects.create(user=top, boss=active_boss, points_contributed=900)

    resp = api_client.get(reverse("api_world_boss_leaderboard"))
    assert resp.status_code == 200
    assert resp.data["boss_id"] == active_boss.id
    board = resp.data["leaderboard"]
    assert [row["username"] for row in board] == ["top", "mid"]
    assert board[0]["points_contributed"] == 900
    # La solution ne fuite jamais via le classement.
    assert "secret_title" not in board[0]


@pytest.mark.django_db
def test_leaderboard_empty_when_no_boss(api_client):
    resp = api_client.get(reverse("api_world_boss_leaderboard"))
    assert resp.status_code == 200
    assert resp.data["boss_id"] is None
    assert resp.data["leaderboard"] == []
