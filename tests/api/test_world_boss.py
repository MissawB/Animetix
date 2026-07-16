from datetime import timedelta

import pytest
from animetix.models import BossParticipation, GlobalBoss
from core.domain.services.world_boss import rules
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.fixture
def active_boss(db):
    return GlobalBoss.objects.create(
        title="Test Boss",
        secret_title="",
        media_type="anime",
        total_hp=100000,
        current_hp=100000,
        end_date=timezone.now() + timedelta(days=1),
        is_active=True,
    )


@pytest.mark.django_db
def test_active_boss_view(api_client, active_boss):
    url = reverse("api_world_boss_active")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data["title"] == "Test Boss"


# --------------------------------------------------------------------------- #
# Spawn automatique hebdomadaire (le mode ne "marchait" jamais : aucun
# mécanisme ne créait de boss, l'endpoint /active/ renvoyait toujours 404).
#
# Depuis le passage au quiz (task 12), le spawn n'a plus besoin du catalogue :
# le boss n'est plus une devinette de titre, donc plus de secret_title/hints à
# tirer d'un pool d'œuvres.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_active_view_spawns_weekly_boss_when_none(api_client):
    response = api_client.get(reverse("api_world_boss_active"))
    assert response.status_code == 200
    assert GlobalBoss.objects.count() == 1
    boss = GlobalBoss.objects.get()
    # La solution ne doit jamais fuiter : ni dans la réponse, ni via le titre
    # affiché (nom de code).
    assert "secret_title" not in response.data
    assert boss.total_hp == rules.BOSS_TOTAL_HP
    assert boss.current_hp == boss.total_hp
    assert boss.end_date > timezone.now()


@pytest.mark.django_db
def test_active_view_does_not_duplicate_boss(api_client):
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
        secret_title="",
        media_type="Anime",
        total_hp=rules.BOSS_TOTAL_HP,
        current_hp=0,
        is_active=False,
        end_date=timezone.now() + timedelta(days=3),
    )
    response = api_client.get(reverse("api_world_boss_active"))
    assert response.status_code == 404
    assert GlobalBoss.objects.count() == 1


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


# --------------------------------------------------------------------------- #
# Le spawn hebdomadaire etait un read-then-create sans verrou ni unicite : deux
# requetes concurrentes dans la fenetre vide (celle que la migration 0051 CREE au
# deploiement, en expirant le boss legacy) invoquaient chacune leur raid de
# 100 000 PV. Les participations sont liees au boss par FK : degats, classement et
# XP se seraient scindes entre deux raids qui ne pouvaient plus mourir.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_two_spawns_in_the_same_week_yield_a_single_boss():
    from animetix.api.games.world_boss import _spawn_weekly_boss

    first = _spawn_weekly_boss()
    second = _spawn_weekly_boss()

    assert GlobalBoss.objects.count() == 1
    assert first.id == second.id


@pytest.mark.django_db
def test_the_weekly_boss_is_keyed_by_its_iso_week():
    from animetix.api.games.world_boss import _spawn_weekly_boss, _week_key

    boss = _spawn_weekly_boss()

    assert boss.week_key == _week_key()
    assert boss.week_key == "{}-W{:02d}".format(*timezone.now().isocalendar()[:2])


@pytest.mark.django_db
def test_the_empty_window_after_the_legacy_raid_expires_spawns_exactly_one_boss(
    api_client,
):
    """La fenetre vide du deploiement : la banniere d'accueil, la page et
    POST /question/ frappent toutes en meme temps. Une seule doit invoquer."""
    from animetix.api.games.world_boss import _active_boss

    legacy = GlobalBoss.objects.create(
        title="RAID LEGACY",
        secret_title="Bleach",
        media_type="Anime",
        total_hp=10000,
        current_hp=10000,
        is_active=False,
        end_date=timezone.now(),  # expire par la migration 0051
    )

    bosses = {_active_boss().id, _active_boss().id, _active_boss().id}
    api_client.get(reverse("api_world_boss_active"))

    assert len(bosses) == 1
    assert GlobalBoss.objects.exclude(id=legacy.id).count() == 1
