"""The World Boss quiz endpoints.

Two properties carry the whole game: the answer never leaves the server, and the
clock is the server's. Everything else is arithmetic.
"""

import importlib
import types
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from animetix.containers import container
from animetix.models import BossParticipation, GlobalBoss
from core.domain.services.world_boss.context import Question
from dependency_injector import providers
from django.contrib.auth.models import User
from django.db import IntegrityError, connection
from django.utils import timezone
from rest_framework.test import APIClient

_dedup_migration = importlib.import_module(
    "animetix.migrations.0053_bossparticipation_unique_user_boss"
)


@pytest.fixture(autouse=True)
def _wire():
    import animetix.api.games.world_boss as world_boss_mod

    container.wire(modules=[world_boss_mod])
    yield


@contextmanager
def _quiz(question):
    """Override the quiz service AND reset it — a leaked override poisons the session."""
    service = MagicMock()
    service.build_question.return_value = question
    container.core.world_boss_quiz_service.override(providers.Object(service))
    try:
        yield service
    finally:
        container.core.world_boss_quiz_service.reset_last_overriding()


QUESTION = Question(
    archetype="year",
    prompt="En quelle année est sortie « Cowboy Bebop » ?",
    options=["1996", "1998", "2001", "2004"],
    correct_index=1,
    subject="Cowboy Bebop",
)


@pytest.fixture
def boss(db):
    return GlobalBoss.objects.create(
        title="RAID OMEGA · S28",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=100000,
        end_date=timezone.now() + timezone.timedelta(days=7),
    )


@pytest.fixture
def client(db):
    api = APIClient()
    api.force_authenticate(User.objects.create_user("kenji"))
    return api


def _ask(client):
    return client.post("/api/v1/game/world-boss/question/", {}, format="json")


def _answer(client, index):
    return client.post(
        "/api/v1/game/world-boss/answer/", {"index": index}, format="json"
    )


@pytest.mark.django_db
def test_the_question_never_ships_its_answer(client, boss):
    with _quiz(QUESTION):
        response = _ask(client)

    assert response.status_code == 200
    body = response.json()
    assert body["options"] == QUESTION.options
    assert "correct_index" not in body
    assert "subject" not in body  # the reveal comes with the answer, not before it
    assert body["tier"] == 1
    assert body["timer"] == 20
    assert body["damage"] == 1


@pytest.mark.django_db
def test_a_right_answer_deals_its_tier_damage_and_climbs(client, boss):
    with _quiz(QUESTION):
        _ask(client)
        response = _answer(client, 1)

    body = response.json()
    assert body["correct"] is True
    assert body["damage_dealt"] == 1
    assert body["tier"] == 2  # the next question is one rung up
    assert body["run_damage"] == 1
    assert body["correct_label"] == "1998"
    boss.refresh_from_db()
    assert boss.current_hp == 99999
    assert BossParticipation.objects.get(user__username="kenji").best_tier == 1


@pytest.mark.django_db
def test_a_wrong_answer_drops_to_tier_one_and_keeps_the_damage_banked(client, boss):
    with _quiz(QUESTION):
        _ask(client)
        _answer(client, 1)  # tier 1 cleared -> tier 2
        _ask(client)
        response = _answer(client, 0)  # wrong

    body = response.json()
    assert body["correct"] is False
    assert body["damage_dealt"] == 0
    assert body["tier"] == 1
    assert body["correct_index"] == 1  # now it may be revealed
    boss.refresh_from_db()
    assert boss.current_hp == 99999  # the point already scored stays scored


@pytest.mark.django_db
def test_an_answer_that_arrives_after_the_clock_is_refused(client, boss, monkeypatch):
    import animetix.api.games.world_boss as world_boss_mod

    with _quiz(QUESTION):
        _ask(client)
        # 20 s timer + 2 s grace: 30 s later, the answer is late whatever the client says.
        monkeypatch.setattr(
            world_boss_mod, "_now", lambda: timezone.now().timestamp() + 30
        )
        response = _answer(client, 1)

    body = response.json()
    assert body["late"] is True
    assert body["correct"] is False
    assert body["damage_dealt"] == 0
    assert body["tier"] == 1


@pytest.mark.django_db
def test_the_same_answer_cannot_be_cashed_twice(client, boss):
    with _quiz(QUESTION):
        _ask(client)
        _answer(client, 1)
        replay = _answer(client, 1)

    assert replay.status_code == 400  # the question was consumed
    boss.refresh_from_db()
    assert boss.current_hp == 99999


@pytest.mark.django_db
def test_five_correct_answers_at_tier_twelve_open_the_limiter_break(client, boss):
    with _quiz(QUESTION):
        for _ in range(11):  # climb to tier 12
            _ask(client)
            _answer(client, 1)

        assert _ask(client).json()["tier"] == 12

        for _ in range(4):
            _answer(client, 1)
            body = _ask(client).json()
            assert body["limiter_break"] is False

        _answer(client, 1)  # the fifth at tier 12
        opened = _ask(client).json()

    assert opened["limiter_break"] is True
    assert opened["damage"] == 4096
    assert opened["timer"] == 6
    assert BossParticipation.objects.get(user__username="kenji").limiter_breaks == 1


@pytest.mark.django_db
def test_answering_requires_an_account(boss):
    anonymous = APIClient()
    assert anonymous.post(
        "/api/v1/game/world-boss/question/", {}, format="json"
    ).status_code in (401, 403)


@pytest.mark.django_db
def test_the_attack_endpoint_is_gone(client):
    assert (
        client.post("/api/v1/game/world-boss/attack/", {}, format="json").status_code
        == 404
    )


# --------------------------------------------------------------------------- #
# Reward distribution and phase broadcast used to be exercised through the now
# -deleted attack endpoint; the logic moved into WorldBossAnswerView verbatim, so
# the coverage moves with it.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_defeat_distributes_reward_to_all_participants(client):
    boss = GlobalBoss.objects.create(
        title="RAID FINAL",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=1,
        reward_xp=1000,
        end_date=timezone.now() + timezone.timedelta(days=1),
    )
    helper = User.objects.create_user("helper")
    BossParticipation.objects.create(user=helper, boss=boss, points_contributed=200)
    helper.profile.xp = 50
    helper.profile.save()

    with _quiz(QUESTION):
        _ask(client)
        response = _answer(client, 1)

    assert response.status_code == 200
    boss.refresh_from_db()
    assert boss.current_hp == 0
    assert boss.is_active is False
    assert boss.reward_distributed is True

    helper.profile.refresh_from_db()
    finisher = User.objects.get(username="kenji")
    assert helper.profile.xp == 50 + 1000
    assert finisher.profile.xp == 1000


@pytest.mark.django_db
def test_reward_already_distributed_is_not_distributed_twice(client):
    boss = GlobalBoss.objects.create(
        title="RAID CLOS",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=1,
        reward_xp=1000,
        reward_distributed=True,
        is_active=True,
        end_date=timezone.now() + timezone.timedelta(days=1),
    )
    finisher = User.objects.get(username="kenji")
    finisher.profile.xp = 0
    finisher.profile.save()

    with _quiz(QUESTION):
        _ask(client)
        _answer(client, 1)

    boss.refresh_from_db()
    finisher.profile.refresh_from_db()
    assert boss.current_hp == 0
    assert (
        finisher.profile.xp == 0
    )  # already claimed -- this hit does not pay out again


@pytest.mark.django_db
def test_a_phase_change_survives_a_channel_layer_outage(client):
    """The phase notification is best-effort: a channel layer outage (Redis down
    in prod) must not turn a correct answer into a 500."""
    GlobalBoss.objects.create(
        title="RAID OMEGA",
        secret_title="",
        media_type="Anime",
        total_hp=1000,
        current_hp=500,  # 500 -> 499 crosses the phase-2 threshold
        end_date=timezone.now() + timezone.timedelta(days=1),
    )
    with patch(
        "animetix.signals.get_channel_layer", side_effect=RuntimeError("redis down")
    ):
        with _quiz(QUESTION):
            _ask(client)
            response = _answer(client, 1)

    assert response.status_code == 200
    assert response.json()["boss"]["current_phase"] == 2


@pytest.mark.django_db
def test_a_phase_that_does_not_change_raises_no_global_alert(client, boss):
    """Le marqueur ``_phase_changed`` est la seule chose qui autorise l'alerte
    mondiale : sans lui, chaque coup porté spammerait toute la communauté."""
    with patch("animetix.signals.get_channel_layer") as layer:
        with _quiz(QUESTION):
            _ask(client)
            response = _answer(client, 1)  # 100000 -> 99999 : toujours phase 1

    assert response.status_code == 200
    assert response.json()["boss"]["current_phase"] == 1
    layer.assert_not_called()  # aucune alerte : la phase n'a pas bougé


@pytest.mark.django_db
def test_no_xp_is_distributed_while_the_boss_is_alive(client, boss):
    with _quiz(QUESTION):
        _ask(client)
        _answer(client, 1)

    boss.refresh_from_db()
    assert boss.current_hp == 99999
    assert boss.reward_distributed is False
    finisher = User.objects.get(username="kenji")
    finisher.profile.refresh_from_db()
    assert finisher.profile.xp == 0  # la récompense n'arrive qu'à la mise à mort


# --------------------------------------------------------------------------- #
# Security: the run state and the pending question live on BossParticipation, not
# in the session. Everything below is an attack the session-backed version lost.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_two_racing_answers_cash_the_question_only_once(client, boss):
    """The race the sequential replay test cannot see.

    Both requests read ``pending_index`` while it is still set (that is what makes
    it a race); the atomic conditional UPDATE decides who cashes it. We reproduce
    the interleaving deterministically by firing the second request from inside the
    first, at the exact point where it has already snapshotted the pending question
    but has not yet claimed it.
    """
    import animetix.api.games.world_boss as world_boss_mod

    with _quiz(QUESTION):
        _ask(client)

        real_now = world_boss_mod._now
        fired = []

        def _now_and_race():
            if not fired:
                fired.append(True)
                # The competing request runs to completion here — same session,
                # same participation row, same pending question.
                inner = _answer(client, 1)
                assert inner.json()["damage_dealt"] == 1
            return real_now()

        with patch.object(world_boss_mod, "_now", _now_and_race):
            outer = _answer(client, 1)

    assert fired, "the interleaving never happened — the test proves nothing"
    assert outer.status_code == 400  # the claim lost: no second payout
    boss.refresh_from_db()
    assert boss.current_hp == 99999  # ONE point of damage, not two
    participation = BossParticipation.objects.get(user__username="kenji", boss=boss)
    assert participation.points_contributed == 1


@pytest.mark.django_db
def test_the_pending_question_cannot_be_re_rolled(client, boss):
    other = Question(
        archetype="studio",
        prompt="Quel studio a produit « Akira » ?",
        options=["Madhouse", "Bones", "TMS", "Sunrise"],
        correct_index=2,
        subject="Akira",
    )
    with _quiz(QUESTION) as service:
        first = _ask(client).json()
        again = _ask(client).json()
        assert service.build_question.call_count == 1  # no second draw

    issued_at = BossParticipation.objects.get(user__username="kenji").issued_at

    # Even with a service that would happily hand out a different question, the
    # pending one is re-issued verbatim: asking again buys the player nothing.
    with _quiz(other):
        third = _ask(client).json()

    participation = BossParticipation.objects.get(user__username="kenji")
    assert again["prompt"] == first["prompt"]
    assert again["options"] == first["options"]  # same options, same ORDER
    assert third["prompt"] == QUESTION.prompt
    assert third["options"] == QUESTION.options
    assert participation.issued_at == issued_at  # the clock was NOT restamped


@pytest.mark.django_db
def test_an_abandoned_question_counts_as_a_miss(client, boss, monkeypatch):
    import animetix.api.games.world_boss as world_boss_mod

    with _quiz(QUESTION):
        _ask(client)
        _answer(client, 1)  # tier 1 cleared -> tier 2
        assert _ask(client).json()["tier"] == 2

        # The player closes the tab. 40 s later (20 s timer + 2 s grace), they come back.
        monkeypatch.setattr(
            world_boss_mod, "_now", lambda: timezone.now().timestamp() + 40
        )
        back = _ask(client).json()

    assert back["tier"] == 1  # the abandoned question is a miss, not a free pass
    assert back["run_damage"] == 0
    assert back["streak"] == 0
    participation = BossParticipation.objects.get(user__username="kenji")
    assert participation.tier == 1
    assert participation.pending_index is not None  # a fresh question was drawn


@pytest.mark.django_db
def test_a_question_drawn_for_a_dead_boss_cannot_hit_the_next_one(client, boss):
    with _quiz(QUESTION):
        _ask(client)  # question issued for THIS week's boss

    boss.is_active = False  # the weekly rollover
    boss.save()
    fresh = GlobalBoss.objects.create(
        title="RAID OMEGA · S29",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=100000,
        end_date=timezone.now() + timezone.timedelta(days=7),
    )

    with _quiz(QUESTION):
        held = _answer(client, 1)

    assert held.status_code == 400  # no question in progress on the new boss
    fresh.refresh_from_db()
    boss.refresh_from_db()
    assert fresh.current_hp == 100000
    assert boss.current_hp == 100000


@pytest.mark.django_db
def test_the_client_cannot_forge_its_own_tier_damage_or_clock(client, boss):
    with _quiz(QUESTION):
        _ask(client)
        response = client.post(
            "/api/v1/game/world-boss/answer/",
            {
                "index": 1,
                "tier": 12,
                "damage": 4096,
                "limiter_break": True,
                "issued_at": timezone.now().timestamp(),
                "run_damage": 99999,
            },
            format="json",
        )

    body = response.json()
    assert body["correct"] is True
    assert body["damage_dealt"] == 1  # tier 1, whatever the payload claimed
    assert body["tier"] == 2
    assert body["limiter_break"] is False
    assert body["run_damage"] == 1
    boss.refresh_from_db()
    assert boss.current_hp == 99999


@pytest.mark.django_db
def test_answering_anonymously_is_refused(boss):
    anonymous = APIClient()
    assert anonymous.post(
        "/api/v1/game/world-boss/answer/", {"index": 1}, format="json"
    ).status_code in (401, 403)


@pytest.mark.django_db
def test_overkill_does_not_inflate_the_leaderboard(client):
    """A boss with 1 HP left takes 1 point of damage, not 4096 — and the
    contributor is credited with what they actually dealt."""
    GlobalBoss.objects.create(
        title="RAID AGONIE",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=1,
        end_date=timezone.now() + timezone.timedelta(days=1),
    )
    participation_boss = GlobalBoss.objects.get(title="RAID AGONIE")
    BossParticipation.objects.create(
        user=User.objects.get(username="kenji"),
        boss=participation_boss,
        tier=12,
        limiter_break=True,
    )

    with _quiz(QUESTION):
        _ask(client)
        body = _answer(client, 1).json()

    assert body["damage_dealt"] == 1  # not 4096
    participation = BossParticipation.objects.get(user__username="kenji")
    assert participation.points_contributed == 1


@pytest.mark.django_db
def test_a_starved_catalogue_returns_503_not_500(client, boss):
    from core.domain.exceptions import GameLogicError

    service = MagicMock()
    service.build_question.side_effect = GameLogicError("no question available")
    container.core.world_boss_quiz_service.override(providers.Object(service))
    try:
        response = _ask(client)
    finally:
        container.core.world_boss_quiz_service.reset_last_overriding()

    assert response.status_code == 503


@pytest.mark.django_db
def test_the_leaderboard_ranks_by_the_deepest_climb(client, boss):
    grinder = User.objects.create_user("grinder")
    climber = User.objects.create_user("climber")
    BossParticipation.objects.create(
        user=grinder, boss=boss, points_contributed=300, best_tier=4
    )
    BossParticipation.objects.create(
        user=climber, boss=boss, points_contributed=120, best_tier=11
    )

    rows = APIClient().get("/api/v1/game/world-boss/leaderboard/").json()["leaderboard"]

    assert [r["username"] for r in rows] == ["climber", "grinder"]
    # The pending question now lives on this very row: the public leaderboard must
    # not serialise it, or it would hand out every player's answer.
    assert "pending_index" not in rows[0]
    assert "pending_label" not in rows[0]


# --------------------------------------------------------------------------- #
# The lock ("the rowcount is the lock") only holds if there is exactly ONE
# BossParticipation row per (user, boss). Two concurrent POST /question/ on a
# brand-new pair both missing the get() half of get_or_create used to leave two
# rows behind, and every later get_or_create() would raise MultipleObjectsReturned
# -- a 500 for that user, forever, for the rest of the week.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_a_second_participation_for_the_same_user_and_boss_is_rejected(boss):
    user = User.objects.create_user("dup")
    BossParticipation.objects.create(user=user, boss=boss)

    with pytest.raises(IntegrityError):
        BossParticipation.objects.create(user=user, boss=boss)


@contextmanager
def _unique_constraint_lifted():
    """Simulate the pre-migration world where the constraint did not yet exist.

    The dedup RunPython step runs *before* the AddConstraint operation, on a
    database that may already hold duplicates -- exactly the state this
    context manager recreates so the fold-and-delete logic can be exercised
    against real duplicate rows.

    On SQLite the constraint is baked into the table's CREATE TABLE statement
    (a ``sqlite_autoindex_*``, not a droppable named index), so
    ``schema_editor.remove_constraint()`` -- which rebuilds the table from
    ``model._meta.constraints`` -- has to see that list emptied first, or the
    rebuilt table just reinstates the same constraint. Rebuilding DDL is also
    something SQLite refuses mid-transaction, hence ``transaction=True`` on the
    two tests that use this.
    """
    original_constraints = BossParticipation._meta.constraints
    BossParticipation._meta.constraints = []
    with connection.schema_editor() as editor:
        editor._remake_table(BossParticipation)
    try:
        yield
    finally:
        BossParticipation._meta.constraints = original_constraints
        with connection.schema_editor() as editor:
            editor._remake_table(BossParticipation)


def _raid_boss():
    return GlobalBoss.objects.create(
        title="RAID OMEGA · S28",
        secret_title="",
        media_type="Anime",
        total_hp=100000,
        current_hp=100000,
        end_date=timezone.now() + timezone.timedelta(days=7),
    )


@pytest.mark.django_db(transaction=True)
def test_deduplication_folds_points_max_tier_and_summed_breaks():
    raid_boss = _raid_boss()
    user = User.objects.create_user("dup2")
    apps = types.SimpleNamespace(get_model=lambda app, model: BossParticipation)

    with _unique_constraint_lifted():
        loser = BossParticipation.objects.create(
            user=user,
            boss=raid_boss,
            points_contributed=50,
            best_tier=3,
            limiter_breaks=1,
        )
        keeper = BossParticipation.objects.create(
            user=user,
            boss=raid_boss,
            points_contributed=200,
            best_tier=9,
            limiter_breaks=2,
        )

        _dedup_migration.deduplicate_boss_participations(apps, None)

        remaining = list(BossParticipation.objects.filter(user=user, boss=raid_boss))
        assert len(remaining) == 1
        survivor = remaining[0]
        assert survivor.pk == keeper.pk  # highest points_contributed kept
        assert survivor.points_contributed == 250  # 200 + 50 folded in
        assert survivor.best_tier == 9  # max of the two
        assert survivor.limiter_breaks == 3  # summed
        assert not BossParticipation.objects.filter(pk=loser.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_deduplication_ties_break_on_the_lowest_pk():
    raid_boss = _raid_boss()
    user = User.objects.create_user("dup3")
    apps = types.SimpleNamespace(get_model=lambda app, model: BossParticipation)

    with _unique_constraint_lifted():
        first = BossParticipation.objects.create(
            user=user, boss=raid_boss, points_contributed=10, best_tier=1
        )
        second = BossParticipation.objects.create(
            user=user, boss=raid_boss, points_contributed=10, best_tier=2
        )

        _dedup_migration.deduplicate_boss_participations(apps, None)

        survivor = BossParticipation.objects.get(user=user, boss=raid_boss)
        assert survivor.pk == first.pk  # tie -> lowest pk wins
        assert survivor.points_contributed == 20
        assert survivor.best_tier == 2
        assert not BossParticipation.objects.filter(pk=second.pk).exists()


# --------------------------------------------------------------------------- #
# `_deadline()` does `participation.issued_at.timestamp()` unguarded. The
# /question/ path only reads a pending question when both `pending_index` and
# `issued_at` are set; /answer/ must refuse the same half-set row instead of
# crashing on it.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_answering_a_half_set_participation_is_refused_not_a_crash(client, boss):
    BossParticipation.objects.create(
        user=User.objects.get(username="kenji"),
        boss=boss,
        pending_index=1,  # issued_at intentionally left unset
    )

    response = _answer(client, 1)

    assert response.status_code == 400
