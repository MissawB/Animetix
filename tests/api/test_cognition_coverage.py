"""Coverage-focused tests for ``animetix.api.cognition`` DRF views.

Exercises success, validation (400) and error (500) paths of every endpoint
via the real URL routing + APIClient, with the constructor-injected services
mocked through real-container provider overrides and the throttle cache
forced to local memory (CI sets REDIS_URL which would otherwise make DRF
throttling hit a real redis).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from animetix.containers import get_container
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse

real_container = get_container()

LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cognition-coverage",
    }
}

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _locmem_cache():
    """Force LocMem cache so DRF throttling does not hit redis (CI sets REDIS_URL)."""
    with override_settings(CACHES=LOCMEM_CACHE):
        yield


@pytest.fixture
def user(db):
    return User.objects.create_user(username="cog_user", password="password")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def _patch_container():
    """Override the cognition providers on the real container with mocks.

    Returns a context manager plus a container-shaped MagicMock whose
    ``.core.X.return_value`` is the very service instance injected into the
    views — the historical call sites keep configuring their mocks the same
    way, but the wiring now goes through constructor injection.
    """
    fake = MagicMock()
    overrides = [
        (
            real_container.core.archetype_drift_service,
            fake.core.archetype_drift_service.return_value,
        ),
        (
            real_container.core.neuro_symbolic_user_profiler,
            fake.core.neuro_symbolic_user_profiler.return_value,
        ),
        (
            real_container.persistence.feedback_adapter,
            fake.persistence.feedback_adapter.return_value,
        ),
        (
            real_container.core.self_play_debate_service,
            fake.core.self_play_debate_service.return_value,
        ),
        (
            real_container.core.counterfactual_simulator,
            fake.core.counterfactual_simulator.return_value,
        ),
        (
            real_container.core.cove_oracle_service,
            fake.core.cove_oracle_service.return_value,
        ),
        (
            real_container.core.cfr_game_solver,
            fake.core.cfr_game_solver.return_value,
        ),
    ]

    @contextmanager
    def _cm():
        try:
            for provider, mock in overrides:
                provider.override(mock)
            yield
        finally:
            for provider, _ in overrides:
                provider.reset_last_overriding()

    return _cm(), fake


# --------------------------------------------------------------------------
# ArchetypeNexusView (GET)
# --------------------------------------------------------------------------
def test_archetype_nexus_get_success_creates_snapshot(auth_client, user):
    from animetix.models import ArchetypeDriftSnapshot

    cm, container = _patch_container()
    with cm:
        container.core.archetype_drift_service.return_value.calculate_drift.return_value = MagicMock(
            archetype_id="The Sage",
            primary_accent="blue",
            aura_type="calm",
            aura_intensity=0.8,
            font_vibe="serif",
        )
        container.core.neuro_symbolic_user_profiler.return_value.deduce_preference_rules.return_value = [
            "Likes action"
        ]
        container.persistence.feedback_adapter.return_value.get_user_feedback.return_value = [
            {"input_context": "ctx", "is_positive": True, "created_at": "now"}
        ]
        resp = auth_client.get(reverse("api_archetype_nexus"))

    assert resp.status_code == 200
    assert resp.data["archetype"]["id"] == "The Sage"
    assert resp.data["logical_rules"] == ["Likes action"]
    assert resp.data["cognitive_stats"]["memory_depth"] == 1
    assert len(resp.data["recent_signals"]) == 1
    # A snapshot row was written to the real ORM
    assert ArchetypeDriftSnapshot.objects.filter(user=user).count() == 1


def test_archetype_nexus_skips_snapshot_when_recent_exists(auth_client, user):
    """If a snapshot was created within the last hour, no new one is added."""
    from animetix.models import ArchetypeDriftSnapshot

    ArchetypeDriftSnapshot.objects.create(
        user=user,
        archetype_id="Existing",
        intensity=0.5,
        shonen_affinity=0.1,
        seinen_affinity=0.1,
        logic_consistency=0.9,
    )
    cm, container = _patch_container()
    with cm:
        container.core.archetype_drift_service.return_value.calculate_drift.return_value = MagicMock(
            archetype_id="The Sage",
            primary_accent="blue",
            aura_type="calm",
            aura_intensity=0.8,
            font_vibe="serif",
        )
        container.core.neuro_symbolic_user_profiler.return_value.deduce_preference_rules.return_value = []
        container.persistence.feedback_adapter.return_value.get_user_feedback.return_value = []
        resp = auth_client.get(reverse("api_archetype_nexus"))

    assert resp.status_code == 200
    # Still only the pre-existing snapshot; history is returned
    assert ArchetypeDriftSnapshot.objects.filter(user=user).count() == 1
    assert len(resp.data["drift_history"]) == 1


def test_archetype_nexus_unauthenticated(api_client):
    resp = api_client.get(reverse("api_archetype_nexus"))
    assert resp.status_code in (401, 403)


# --------------------------------------------------------------------------
# AIDebateArenaView (POST)
# --------------------------------------------------------------------------
def test_ai_debate_arena_success(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.self_play_debate_service.return_value.run_debate.return_value = {
            "status": "success",
            "debate": "Naruto vs Sasuke",
        }
        resp = auth_client.post(
            reverse("api_debate_arena"),
            {"media_title": "Naruto", "topic": "Best Ninja"},
            format="json",
        )
    assert resp.status_code == 200
    assert resp.data["debate"] == "Naruto vs Sasuke"


def test_ai_debate_arena_validation_error(auth_client):
    resp = auth_client.post(
        reverse("api_debate_arena"), {"topic": "no title"}, format="json"
    )
    assert resp.status_code == 400
    assert "media_title" in resp.data


def test_ai_debate_arena_service_exception(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.self_play_debate_service.return_value.run_debate.side_effect = (
            RuntimeError("boom")
        )
        resp = auth_client.post(
            reverse("api_debate_arena"),
            {"media_title": "Naruto", "topic": "X"},
            format="json",
        )
    assert resp.status_code == 500
    assert resp.data["error"] == "Internal server error"


# --------------------------------------------------------------------------
# NeuroMemoryManagementView (GET + POST actions)
# --------------------------------------------------------------------------
def test_neuro_memory_get(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.neuro_symbolic_user_profiler.return_value.deduce_preference_rules.return_value = [
            "Rule 1",
            "Rule 2",
        ]
        container.persistence.feedback_adapter.return_value.get_user_feedback.return_value = [
            {"id": 1},
            {"id": 2},
        ]
        resp = auth_client.get(reverse("api_neuro_memory"))
    assert resp.status_code == 200
    assert resp.data["total_signals"] == 2
    assert len(resp.data["deduced_rules"]) == 2


def test_neuro_memory_post_reset(auth_client, user):
    from animetix.models import AIFeedback

    fb = AIFeedback.objects.create(user=user, feedback_type="like", is_positive=True)
    resp = auth_client.post(
        reverse("api_neuro_memory"), {"action": "reset"}, format="json"
    )
    assert resp.status_code == 200
    fb.refresh_from_db()
    assert fb.is_ignored is True


def test_neuro_memory_post_revoke(auth_client, user):
    from animetix.models import AIFeedback

    fb = AIFeedback.objects.create(user=user, feedback_type="like", is_positive=True)
    resp = auth_client.post(
        reverse("api_neuro_memory"),
        {"action": "revoke", "feedback_id": fb.id},
        format="json",
    )
    assert resp.status_code == 200
    fb.refresh_from_db()
    assert fb.is_ignored is True


def test_neuro_memory_post_revoke_missing_id(auth_client):
    resp = auth_client.post(
        reverse("api_neuro_memory"), {"action": "revoke"}, format="json"
    )
    assert resp.status_code == 400
    assert "feedback_id" in resp.data["error"]


def test_neuro_memory_post_restore(auth_client, user):
    from animetix.models import AIFeedback

    fb = AIFeedback.objects.create(
        user=user, feedback_type="like", is_positive=True, is_ignored=True
    )
    resp = auth_client.post(
        reverse("api_neuro_memory"),
        {"action": "restore", "feedback_id": fb.id},
        format="json",
    )
    assert resp.status_code == 200
    fb.refresh_from_db()
    assert fb.is_ignored is False


def test_neuro_memory_post_restore_missing_id(auth_client):
    resp = auth_client.post(
        reverse("api_neuro_memory"), {"action": "restore"}, format="json"
    )
    assert resp.status_code == 400


def test_neuro_memory_post_update_weight(auth_client, user):
    from animetix.models import AIFeedback

    fb = AIFeedback.objects.create(user=user, feedback_type="like", is_positive=True)
    resp = auth_client.post(
        reverse("api_neuro_memory"),
        {"action": "update_weight", "feedback_id": fb.id, "weight": 2.5},
        format="json",
    )
    assert resp.status_code == 200
    fb.refresh_from_db()
    assert fb.weight == 2.5


def test_neuro_memory_post_update_weight_missing_params(auth_client):
    resp = auth_client.post(
        reverse("api_neuro_memory"), {"action": "update_weight"}, format="json"
    )
    assert resp.status_code == 400


def test_neuro_memory_post_invalid_action(auth_client):
    resp = auth_client.post(
        reverse("api_neuro_memory"), {"action": "nope"}, format="json"
    )
    assert resp.status_code == 400
    assert resp.data["error"] == "Invalid action"


# --------------------------------------------------------------------------
# CounterfactualSimulatorView (POST)
# --------------------------------------------------------------------------
def test_counterfactual_success(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.counterfactual_simulator.return_value.simulate_counterfactual_path.return_value = {
            "timeline": "alt"
        }
        resp = auth_client.post(
            reverse("api_counterfactual"),
            {
                "what_if": "What if X?",
                "actual_context": [{"speaker": "a", "text": "hi"}],
            },
            format="json",
        )
    assert resp.status_code == 200
    assert resp.data["timeline"] == "alt"


def test_counterfactual_validation_error(auth_client):
    resp = auth_client.post(reverse("api_counterfactual"), {}, format="json")
    assert resp.status_code == 400
    assert "what_if" in resp.data


def test_counterfactual_service_exception(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.counterfactual_simulator.return_value.simulate_counterfactual_path.side_effect = ValueError(
            "kaboom"
        )
        resp = auth_client.post(
            reverse("api_counterfactual"), {"what_if": "X"}, format="json"
        )
    assert resp.status_code == 500
    assert resp.data["error"] == "Internal server error"


# --------------------------------------------------------------------------
# CoveOracleView (POST)
# --------------------------------------------------------------------------
def test_cove_oracle_success(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.cove_oracle_service.return_value.trace_verification.return_value = {
            "verified": True
        }
        resp = auth_client.post(
            reverse("api_cove_oracle"),
            {"question": "Is X real?", "media_type": "manga"},
            format="json",
        )
    assert resp.status_code == 200
    assert resp.data["verified"] is True


def test_cove_oracle_validation_error(auth_client):
    resp = auth_client.post(reverse("api_cove_oracle"), {}, format="json")
    assert resp.status_code == 400
    assert "question" in resp.data


def test_cove_oracle_service_exception(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.cove_oracle_service.return_value.trace_verification.side_effect = RuntimeError(
            "cove down"
        )
        resp = auth_client.post(
            reverse("api_cove_oracle"), {"question": "Q?"}, format="json"
        )
    assert resp.status_code == 500
    assert resp.data["error"] == "Internal server error"


# --------------------------------------------------------------------------
# CFRStrategyLabView (POST)
# --------------------------------------------------------------------------
def test_cfr_strategy_success(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.cfr_game_solver.return_value.solve_with_history.return_value = {
            "converged": True
        }
        resp = auth_client.post(
            reverse("api_cfr_strategy_lab"),
            {"questions": ["q1", "q2"], "iterations": 50},
            format="json",
        )
    assert resp.status_code == 200
    assert resp.data["converged"] is True


def test_cfr_strategy_validation_error(auth_client):
    # iterations out of allowed range -> serializer invalid
    resp = auth_client.post(
        reverse("api_cfr_strategy_lab"), {"iterations": 99999}, format="json"
    )
    assert resp.status_code == 400
    assert "iterations" in resp.data


def test_cfr_strategy_service_exception(auth_client):
    cm, container = _patch_container()
    with cm:
        container.core.cfr_game_solver.return_value.solve_with_history.side_effect = (
            RuntimeError("cfr fail")
        )
        resp = auth_client.post(
            reverse("api_cfr_strategy_lab"), {"iterations": 10}, format="json"
        )
    assert resp.status_code == 500
    assert resp.data["error"] == "Internal server error"
