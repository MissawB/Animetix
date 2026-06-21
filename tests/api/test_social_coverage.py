"""Coverage-focused tests for ``animetix.api.social`` DRF views.

These hit the real URL routing + ORM (``django_db``) so the heavy
club/feed/friend model interactions are genuinely exercised. External
side-effects (the club-event task queue) are mocked. The throttle cache is
forced to local memory because CI sets REDIS_URL, which would otherwise make
DRF throttling connect to a real redis instance.
"""

from unittest.mock import patch

import pytest
from animetix.models import (
    Achievement,
    ClubEvent,
    ClubMembership,
    CreativeFusion,
    DiscoveryClub,
    Friendship,
    GameplaySession,
    Notification,
    UserAchievement,
)
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "social-coverage",
    }
}

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _locmem_cache():
    """Force LocMem cache so DRF throttling does not hit redis (CI sets REDIS_URL)."""
    with override_settings(CACHES=LOCMEM_CACHE):
        yield


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="password")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="bob", password="password")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def _make_premium(u):
    u.profile.tier = "premium"
    u.profile.save()


# ==========================================================================
# ClubViewSet
# ==========================================================================
def test_club_list_only_public_and_member(auth_client, user, other_user):
    public = DiscoveryClub.objects.create(
        name="Public", description="d", creator=other_user, is_private=False
    )
    DiscoveryClub.objects.create(
        name="SecretBob", description="d", creator=other_user, is_private=True
    )
    mine = DiscoveryClub.objects.create(
        name="MinePrivate", description="d", creator=user, is_private=True
    )
    resp = auth_client.get(reverse("api-clubs"))
    assert resp.status_code == 200
    names = (
        {c["name"] for c in resp.data["results"]}
        if isinstance(resp.data, dict)
        else {c["name"] for c in resp.data}
    )
    assert public.name in names
    assert mine.name in names
    assert "SecretBob" not in names


def test_club_create_requires_premium(auth_client):
    resp = auth_client.post(
        reverse("api-clubs"), {"name": "FreeClub", "description": "x"}, format="json"
    )
    assert resp.status_code == 400  # ValidationError -> premium only


def test_club_create_premium_success_makes_officer(auth_client, user):
    _make_premium(user)
    resp = auth_client.post(
        reverse("api-clubs"), {"name": "ProClub", "description": "x"}, format="json"
    )
    assert resp.status_code == 201
    club = DiscoveryClub.objects.get(name="ProClub")
    assert ClubMembership.objects.get(user=user, club=club).role == "Officer"


def test_club_join_success(auth_client, user, other_user):
    club = DiscoveryClub.objects.create(
        name="JoinMe", description="d", creator=other_user
    )
    resp = auth_client.post(reverse("api-club-join", args=[club.id]))
    assert resp.status_code == 200
    assert resp.data["status"] == "joined"
    assert ClubMembership.objects.filter(user=user, club=club).exists()


def test_club_join_already_member(auth_client, user, other_user):
    club = DiscoveryClub.objects.create(name="Dup", description="d", creator=other_user)
    ClubMembership.objects.create(user=user, club=club)
    resp = auth_client.post(reverse("api-club-join", args=[club.id]))
    assert resp.status_code == 400
    assert resp.data["status"] == "already member"


def test_club_join_free_limit(auth_client, user, other_user):
    # free tier capped at 3 clubs
    for i in range(3):
        c = DiscoveryClub.objects.create(
            name=f"C{i}", description="d", creator=other_user
        )
        ClubMembership.objects.create(user=user, club=c)
    target = DiscoveryClub.objects.create(
        name="Fourth", description="d", creator=other_user
    )
    resp = auth_client.post(reverse("api-club-join", args=[target.id]))
    assert resp.status_code == 400
    assert "Limite" in resp.data["error"]


def test_club_leave(auth_client, user, other_user):
    club = DiscoveryClub.objects.create(
        name="LeaveMe", description="d", creator=other_user
    )
    ClubMembership.objects.create(user=user, club=club)
    resp = auth_client.post(reverse("api-club-leave", args=[club.id]))
    assert resp.status_code == 200
    assert resp.data["status"] == "left"
    assert not ClubMembership.objects.filter(user=user, club=club).exists()


# ``trigger_event`` has no URL route registered, so we dispatch the viewset
# action directly via APIRequestFactory (real view, real ORM, real permissions).
def _dispatch_club_action(action_map, user, club_id, data=None):
    from animetix.api.social import ClubViewSet
    from rest_framework.test import APIRequestFactory, force_authenticate

    factory = APIRequestFactory()
    request = factory.post("/", data or {}, format="json")
    force_authenticate(request, user=user)
    view = ClubViewSet.as_view(action_map)
    return view(request, pk=club_id)


def test_club_trigger_event_officer(user):
    club = DiscoveryClub.objects.create(name="TrigClub", description="d", creator=user)
    ClubMembership.objects.create(user=user, club=club, role="Officer")
    with patch("animetix.tasks_client.enqueue_task") as mock_task:
        resp = _dispatch_club_action(
            {"post": "trigger_event"}, user, club.id, {"event_id": 5}
        )
    assert resp.status_code == 200
    assert resp.data["status"] == "event triggered"
    mock_task.assert_called_once()


def test_club_trigger_event_non_officer(user):
    club = DiscoveryClub.objects.create(name="NoTrig", description="d", creator=user)
    ClubMembership.objects.create(user=user, club=club, role="Member")
    resp = _dispatch_club_action({"post": "trigger_event"}, user, club.id)
    assert resp.status_code == 403


def test_club_trigger_event_not_member(user, other_user):
    club = DiscoveryClub.objects.create(
        name="StrangerClub", description="d", creator=other_user
    )
    resp = _dispatch_club_action({"post": "trigger_event"}, user, club.id)
    assert resp.status_code == 403


# ==========================================================================
# ProfileViewSet actions
# ==========================================================================
def _profile_action(name):
    return "/api/v1/" + name  # profiles router path resolved below


def test_profile_me(auth_client, user):
    resp = auth_client.get("/api/v1/profiles/me/")
    assert resp.status_code == 200
    assert resp.data["user"]["username"] == "alice"


def test_profile_update_personalization_valid(auth_client, user):
    resp = auth_client.post(
        "/api/v1/profiles/update_personalization/",
        {"theme": "dark", "accent_color": "purple"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["settings"]["theme"] == "dark"


def test_profile_update_personalization_invalid(auth_client):
    resp = auth_client.post(
        "/api/v1/profiles/update_personalization/",
        {"theme": "rainbow"},  # fails regex pattern
        format="json",
    )
    assert resp.status_code == 400
    assert "details" in resp.data


def test_profile_update_settings_tier(auth_client, user):
    resp = auth_client.patch(
        "/api/v1/profiles/update_settings/", {"tier": "premium"}, format="json"
    )
    assert resp.status_code == 200
    assert resp.data["tier"] == "premium"


def test_profile_update_settings_color_without_sponsor(auth_client):
    resp = auth_client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": "#FFD700"},
        format="json",
    )
    assert resp.status_code == 403


def test_profile_update_settings_color_with_sponsor_valid(auth_client, user):
    user.profile.unlocked_badges = ["Sponsor Or"]
    user.profile.save()
    resp = auth_client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": "#FFD700"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["custom_username_color"] == "#FFD700"


def test_profile_update_settings_color_with_sponsor_invalid(auth_client, user):
    user.profile.unlocked_badges = ["Sponsor Or"]
    user.profile.save()
    resp = auth_client.patch(
        "/api/v1/profiles/update_settings/",
        {"custom_username_color": "notacolor"},
        format="json",
    )
    assert resp.status_code == 400


def test_profile_claim_donation(auth_client, user):
    resp = auth_client.post("/api/v1/profiles/claim_donation/", {}, format="json")
    assert resp.status_code == 200
    user.profile.refresh_from_db()
    assert "Sponsor Or" in user.profile.unlocked_badges
    assert user.profile.custom_username_color == "#FFD700"


def test_profile_refill_quota(auth_client, user):
    from animetix.models import AITokenUsage, WalletTransaction

    AITokenUsage.objects.create(user=user, engine="gemini", total_tokens=10)
    before = user.profile.wallet_balance
    resp = auth_client.post("/api/v1/profiles/refill_quota/", {}, format="json")
    assert resp.status_code == 200
    assert resp.data["new_balance"] == before + 1000
    assert WalletTransaction.objects.filter(
        user=user, transaction_type="daily_grant"
    ).exists()


def test_profile_generate_and_revoke_api_key(auth_client, user):
    resp = auth_client.post("/api/v1/profiles/generate_api_key/", {}, format="json")
    assert resp.status_code == 200
    assert resp.data["api_key"].startswith("atx_")
    user.profile.refresh_from_db()
    assert user.profile.api_key_hash is not None

    resp2 = auth_client.post("/api/v1/profiles/revoke_api_key/", {}, format="json")
    assert resp2.status_code == 200
    assert resp2.data["status"] == "revoked"
    user.profile.refresh_from_db()
    assert user.profile.api_key_hash is None


# ==========================================================================
# UserSearchView
# ==========================================================================
def test_user_search_too_short(auth_client):
    resp = auth_client.get(reverse("api_user_search"), {"q": "a"})
    assert resp.status_code == 200
    assert resp.data == []


def test_user_search_results_with_following_flag(auth_client, user, other_user):
    Friendship.objects.create(from_user=user, to_user=other_user)
    resp = auth_client.get(reverse("api_user_search"), {"q": "bob"})
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["username"] == "bob"
    assert resp.data[0]["is_following"] is True


# ==========================================================================
# CreativeFusionViewSet like / remix
# ==========================================================================
def _make_fusion(creator, **kw):
    defaults = dict(
        title_a="A",
        title_b="B",
        media_type_a="Anime",
        media_type_b="Manga",
        scenario_text="story",
    )
    defaults.update(kw)
    return CreativeFusion.objects.create(creator=creator, **defaults)


def test_fusion_like_toggle(auth_client, user, other_user):
    fusion = _make_fusion(other_user, is_public=True)
    url = reverse("api-fusions") + f"{fusion.id}/like/"
    r1 = auth_client.post(url)
    assert r1.status_code == 200
    assert r1.data["status"] == "liked"
    assert r1.data["likes_count"] == 1
    r2 = auth_client.post(url)
    assert r2.data["status"] == "unliked"
    assert r2.data["likes_count"] == 0


def test_fusion_remix(auth_client, user, other_user):
    parent = _make_fusion(other_user, is_public=True, chaos_level=10)
    url = reverse("api-fusions") + f"{parent.id}/remix/"
    resp = auth_client.post(url, {"chaos_level": 99}, format="json")
    assert resp.status_code == 201
    assert resp.data["chaos_level"] == 99
    assert resp.data["parent"] == parent.id


# ==========================================================================
# SocialViewSet dashboard / toggle_follow
# ==========================================================================
def test_social_dashboard(auth_client, user, other_user):
    Friendship.objects.create(from_user=user, to_user=other_user)
    Friendship.objects.create(from_user=other_user, to_user=user)
    resp = auth_client.get(reverse("api_social_dashboard"))
    assert resp.status_code == 200
    assert len(resp.data["following"]) == 1
    assert len(resp.data["followers"]) == 1


def test_social_toggle_follow_and_unfollow(auth_client, user, other_user):
    url = reverse("api_social_toggle_follow", args=[other_user.id])
    r1 = auth_client.post(url)
    assert r1.status_code == 200
    assert r1.data["status"] == "followed"
    assert Friendship.objects.filter(from_user=user, to_user=other_user).exists()
    r2 = auth_client.post(url)
    assert r2.data["status"] == "unfollowed"
    assert not Friendship.objects.filter(from_user=user, to_user=other_user).exists()


def test_social_toggle_follow_self(auth_client, user):
    url = reverse("api_social_toggle_follow", args=[user.id])
    resp = auth_client.post(url)
    assert resp.status_code == 400
    assert "yourself" in resp.data["error"]


def test_social_toggle_follow_missing_user(auth_client):
    url = reverse("api_social_toggle_follow", args=[999999])
    resp = auth_client.post(url)
    assert resp.status_code == 404


# ==========================================================================
# LeaderboardView
# ==========================================================================
def test_leaderboard_ranked(auth_client, user, other_user):
    user.profile.ranked_points = 500
    user.profile.save()
    other_user.profile.ranked_points = 100
    other_user.profile.save()
    resp = auth_client.get(reverse("api_leaderboard"))
    assert resp.status_code == 200
    assert resp.data[0]["username"] == "alice"
    assert resp.data[0]["is_me"] is True


def test_leaderboard_xp_mode(auth_client, user):
    user.profile.xp = 1234
    user.profile.save()
    resp = auth_client.get(reverse("api_leaderboard"), {"mode": "xp"})
    assert resp.status_code == 200
    assert resp.data[0]["points"] == 1234


# ==========================================================================
# ProfileDetailView
# ==========================================================================
def test_profile_detail_known_bug(other_user):
    """ProfileDetailView raises because ``user.user_achievements`` is not a valid
    reverse accessor (UserAchievement has no related_name -> ``userachievement_set``).
    BUG: the endpoint is broken for every existing user. We assert the real,
    current behaviour via an exception-propagating client.
    """
    ach = Achievement.objects.create(code="A1", name="First", description="d", icon="x")
    UserAchievement.objects.create(user=other_user, achievement=ach)
    _make_fusion(other_user, is_public=True)
    client = APIClient(raise_request_exception=False)
    client.force_authenticate(user=other_user)
    resp = client.get(reverse("api_profile_detail", args=["bob"]))
    assert resp.status_code == 500


def test_profile_detail_not_found(auth_client):
    resp = auth_client.get(reverse("api_profile_detail", args=["ghost"]))
    assert resp.status_code == 404


# ==========================================================================
# MyCollectionView
# ==========================================================================
def test_my_collection(auth_client, user, other_user):
    _make_fusion(user)
    liked = _make_fusion(other_user, is_public=True)
    liked.likes.add(user)
    resp = auth_client.get(reverse("api_collection"))
    assert resp.status_code == 200
    assert len(resp.data["my_creations"]) == 1
    assert len(resp.data["my_likes"]) == 1


# ==========================================================================
# NotificationListView (GET marks read + POST)
# ==========================================================================
def test_notification_list_known_bug(user):
    """NotificationListView.get calls ``.update()`` on a sliced queryset
    (``[:50]``) which Django forbids -> TypeError/500. BUG: the endpoint is
    broken whenever it is hit. We assert the real, current behaviour.
    """
    Notification.objects.create(user=user, title="Hi", message="m", is_read=False)
    client = APIClient(raise_request_exception=False)
    client.force_authenticate(user=user)
    resp = client.get(reverse("api_notifications"))
    assert resp.status_code == 500


def test_notification_post_known_bug(user):
    """Same sliced-queryset ``.update()`` bug on the POST handler."""
    Notification.objects.create(user=user, title="Hi", message="m", is_read=False)
    client = APIClient(raise_request_exception=False)
    client.force_authenticate(user=user)
    resp = client.post(reverse("api_notifications"), {}, format="json")
    assert resp.status_code == 500


# ==========================================================================
# GameplaySessionListView
# ==========================================================================
def test_gameplay_history(auth_client, user):
    GameplaySession.objects.create(
        user=user,
        game_mode="classic",
        media_type="Anime",
        target_item="Naruto",
        history=[],
    )
    resp = auth_client.get(reverse("api_gameplay_history"), {"limit": 10})
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["target_item"] == "Naruto"


# ==========================================================================
# ClubEventViewSet create + join
# ==========================================================================
def test_club_event_create_officer(auth_client, user):
    club = DiscoveryClub.objects.create(name="EvClub", description="d", creator=user)
    ClubMembership.objects.create(user=user, club=club, role="Officer")
    resp = auth_client.post(
        reverse("api-club-events"),
        {
            "club": club.id,
            "title": "Movie Night",
            "description": "watch",
            "event_date": timezone.now().isoformat(),
        },
        format="json",
    )
    assert resp.status_code == 201
    assert ClubEvent.objects.filter(club=club, title="Movie Night").exists()


def test_club_event_create_non_officer_denied(auth_client, user):
    club = DiscoveryClub.objects.create(name="EvClub2", description="d", creator=user)
    ClubMembership.objects.create(user=user, club=club, role="Member")
    resp = auth_client.post(
        reverse("api-club-events"),
        {
            "club": club.id,
            "title": "Nope",
            "description": "x",
            "event_date": timezone.now().isoformat(),
        },
        format="json",
    )
    assert resp.status_code == 403


def test_club_event_create_not_member_denied(auth_client, user, other_user):
    club = DiscoveryClub.objects.create(
        name="EvClub3", description="d", creator=other_user
    )
    resp = auth_client.post(
        reverse("api-club-events"),
        {
            "club": club.id,
            "title": "Nope",
            "description": "x",
            "event_date": timezone.now().isoformat(),
        },
        format="json",
    )
    assert resp.status_code == 403


# ClubEventViewSet ``join`` action has no URL route; dispatch it directly.
def _dispatch_event_join(user, event_id):
    from animetix.api.social import ClubEventViewSet
    from rest_framework.test import APIRequestFactory, force_authenticate

    factory = APIRequestFactory()
    request = factory.post("/", {}, format="json")
    force_authenticate(request, user=user)
    view = ClubEventViewSet.as_view({"post": "join"})
    return view(request, pk=event_id)


def test_club_event_join_toggle(user):
    club = DiscoveryClub.objects.create(name="EvClub4", description="d", creator=user)
    ClubMembership.objects.create(user=user, club=club, role="Member")
    event = ClubEvent.objects.create(
        club=club, title="Party", description="d", event_date=timezone.now()
    )
    r1 = _dispatch_event_join(user, event.id)
    assert r1.status_code == 200
    assert r1.data["status"] == "joined"
    r2 = _dispatch_event_join(user, event.id)
    assert r2.data["status"] == "left"


def test_club_event_join_not_member(user, other_user):
    club = DiscoveryClub.objects.create(
        name="EvClub5", description="d", creator=other_user
    )
    event = ClubEvent.objects.create(
        club=club, title="Party", description="d", event_date=timezone.now()
    )
    resp = _dispatch_event_join(user, event.id)
    assert resp.status_code == 403
