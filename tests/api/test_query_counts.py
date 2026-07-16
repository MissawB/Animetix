"""N+1 regression locks for the list/social endpoints (2026-07-05 debt audit).

Each test captures the SQL query count on a small dataset, grows the dataset,
and asserts the count is unchanged: a fixed number of queries per request,
never a number that scales with the rows being serialized. This is the
property that ``select_related``/``prefetch_related`` must guarantee, without
pinning brittle absolute counts.
"""

import pytest
from animetix.models import AIFeedback, CreativeFusion, DiscoveryClub, VsBattle
from django.contrib.auth.models import User
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "query-counts",
    }
}

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _locmem_cache():
    """Force LocMem cache so DRF throttling does not hit redis (CI sets REDIS_URL)."""
    with override_settings(CACHES=LOCMEM_CACHE):
        yield


@pytest.fixture
def creator(db):
    return User.objects.create_user(username="alice", password="password")


def _make_fusion(creator, i):
    return CreativeFusion.objects.create(
        title_a=f"Titre A{i}",
        title_b=f"Titre B{i}",
        media_type_a="Anime",
        media_type_b="Manga",
        scenario_text="scenario",
        creator=creator,
    )


def _make_battle(creator, i):
    return VsBattle.objects.create(
        char_a_name=f"Goku {i}",
        char_b_name=f"Naruto {i}",
        char_a_data={},
        char_b_data={},
        winner="Goku",
        verdict_summary="verdict",
        debate_history=[],
        creator=creator,
        is_public=True,
    )


def _make_club(creator, i):
    return DiscoveryClub.objects.create(
        name=f"Club {i}",
        description="description",
        creator=creator,
        is_private=False,
    )


def _count_queries(client, url):
    # Warm-up: fills per-process caches (ContentType, prepared statements…) so
    # the two measured requests only differ by the size of the dataset.
    client.get(url)
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url)
    assert response.status_code == 200, response.content
    return len(ctx)


def test_profile_detail_fusion_queries_do_not_scale(api_client, creator):
    """ProfileDetailView serializes top/recent fusions: fixed query count."""
    for i in range(2):
        _make_fusion(creator, i)
    url = reverse("api_profile_detail", args=[creator.username])

    baseline = _count_queries(api_client, url)

    for i in range(2, 10):
        _make_fusion(creator, i)

    assert _count_queries(api_client, url) == baseline


def test_vs_battle_arena_queries_do_not_scale(api_client, creator):
    """The public arena list (creator_name + likes_count): fixed query count."""
    for i in range(2):
        _make_battle(creator, i)
    url = reverse("api_vs_battle_arena")

    baseline = _count_queries(api_client, url)

    for i in range(2, 10):
        _make_battle(creator, i)

    assert _count_queries(api_client, url) == baseline


def test_vs_battle_arena_authenticated_queries_do_not_scale(api_client, creator):
    """Authenticated arena adds is_liked per battle: still a fixed query count."""
    viewer = User.objects.create_user(username="bob", password="password")
    api_client.force_authenticate(user=viewer)
    for i in range(2):
        battle = _make_battle(creator, i)
        battle.likes.add(viewer)
    url = reverse("api_vs_battle_arena")

    baseline = _count_queries(api_client, url)

    for i in range(2, 10):
        _make_battle(creator, i)

    assert _count_queries(api_client, url) == baseline


def test_feedback_history_queries_do_not_scale(api_client, creator):
    """The AI feedback history (username per row): fixed query count."""
    api_client.force_authenticate(user=creator)
    for _ in range(2):
        AIFeedback.objects.create(user=creator, feedback_type="rag", is_positive=True)
    url = reverse("submit_ai_feedback")

    baseline = _count_queries(api_client, url)

    for _ in range(8):
        AIFeedback.objects.create(user=creator, feedback_type="rag", is_positive=True)

    assert _count_queries(api_client, url) == baseline


def test_club_list_queries_do_not_scale(api_client, creator):
    """The club list (members_count per club): fixed query count."""
    api_client.force_authenticate(user=creator)
    for i in range(2):
        club = _make_club(creator, i)
        club.members.add(creator)
    url = reverse("api-clubs")

    baseline = _count_queries(api_client, url)

    for i in range(2, 10):
        club = _make_club(creator, i)
        club.members.add(creator)

    assert _count_queries(api_client, url) == baseline
