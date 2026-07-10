from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from animetix.api.cognition import (
    AIDebateArenaView,
    ArchetypeNexusView,
    NeuroMemoryManagementView,
)
from animetix.containers import get_container
from django.test import RequestFactory

container = get_container()


@contextmanager
def _override(**services):
    """Override core/persistence providers by name, reset on exit (provider-level)."""
    providers_map = {
        "drift_service": container.core.archetype_drift_service,
        "profiler": container.core.neuro_symbolic_user_profiler,
        "feedback_port": container.persistence.feedback_adapter,
        "debate_service": container.core.self_play_debate_service,
    }
    touched = []
    try:
        for name, mock in services.items():
            provider = providers_map[name]
            provider.override(mock)
            touched.append(provider)
        yield
    finally:
        for provider in touched:
            provider.reset_last_overriding()


def test_archetype_nexus_view_unauthenticated():
    factory = RequestFactory()
    request = factory.get("/api/v1/cognition/archetype-nexus/")
    with _override(
        drift_service=MagicMock(), profiler=MagicMock(), feedback_port=MagicMock()
    ):
        view = ArchetypeNexusView.as_view()
        response = view(request)
    assert response.status_code in [401, 403]


def test_archetype_nexus_view_authenticated():
    factory = RequestFactory()
    request = factory.get("/api/v1/cognition/archetype-nexus/")
    user = MagicMock()
    user.id = 1
    user.is_authenticated = True
    request.user = user

    drift_service = MagicMock()
    drift_service.calculate_drift.return_value = MagicMock(
        archetype_id="The Sage",
        primary_accent="blue",
        aura_type="calm",
        aura_intensity=0.8,
        font_vibe="serif",
    )
    profiler = MagicMock()
    profiler.deduce_preference_rules.return_value = ["Likes action"]
    feedback_port = MagicMock()
    feedback_port.get_user_feedback.return_value = [
        {"input_context": "test", "is_positive": True}
    ]

    with (
        patch("animetix.api.cognition.ArchetypeDriftSnapshot.objects.filter"),
        patch("animetix.api.cognition.ArchetypeDriftSnapshot.objects.create"),
        _override(
            drift_service=drift_service,
            profiler=profiler,
            feedback_port=feedback_port,
        ),
    ):
        with patch.object(ArchetypeNexusView, "permission_classes", []):
            from rest_framework.test import force_authenticate  # noqa: E402

            view = ArchetypeNexusView.as_view()
            force_authenticate(request, user=user)
            response = view(request)

            assert response.status_code == 200
            assert response.data["archetype"]["id"] == "The Sage"
            assert response.data["logical_rules"] == ["Likes action"]
            assert len(response.data["recent_signals"]) == 1


def test_ai_debate_arena_view():
    factory = RequestFactory()
    request = factory.post(
        "/api/v1/cognition/debate-arena/",
        {"media_title": "Naruto", "topic": "Best Ninja"},
        content_type="application/json",
    )
    user = MagicMock()
    user.is_authenticated = True
    request.user = user

    debate_service = MagicMock()
    debate_service.run_debate.return_value = {
        "status": "success",
        "debate": "Naruto vs Sasuke",
    }

    with (
        _override(debate_service=debate_service),
        patch("animetix.api.cognition.deduct_berrix"),
    ):
        with patch.object(AIDebateArenaView, "permission_classes", []):
            from rest_framework.test import force_authenticate  # noqa: E402

            view = AIDebateArenaView.as_view()
            force_authenticate(request, user=user)
            response = view(request)

            assert response.status_code == 200
            assert response.data["status"] == "success"
            assert response.data["debate"] == "Naruto vs Sasuke"


def test_neuro_memory_management_view_get():
    factory = RequestFactory()
    request = factory.get("/api/v1/cognition/neuro-memory/")
    user = MagicMock()
    user.id = 1
    user.is_authenticated = True
    request.user = user

    profiler = MagicMock()
    profiler.deduce_preference_rules.return_value = ["Rule 1", "Rule 2"]
    feedback_port = MagicMock()
    feedback_port.get_user_feedback.return_value = [{}, {}]

    with _override(profiler=profiler, feedback_port=feedback_port):
        with patch.object(NeuroMemoryManagementView, "permission_classes", []):
            from rest_framework.test import force_authenticate  # noqa: E402

            view = NeuroMemoryManagementView.as_view()
            force_authenticate(request, user=user)
            response = view(request)

            assert response.status_code == 200
            assert response.data["status"] == "success"
            assert len(response.data["deduced_rules"]) == 2
            assert response.data["total_signals"] == 2


def test_neuro_memory_management_view_post():
    factory = RequestFactory()
    request = factory.post(
        "/api/v1/cognition/neuro-memory/",
        {"action": "reset"},
        content_type="application/json",
    )
    user = MagicMock()
    user.is_authenticated = True
    request.user = user

    with (
        _override(profiler=MagicMock(), feedback_port=MagicMock()),
        patch.object(NeuroMemoryManagementView, "permission_classes", []),
        patch("animetix.api.cognition.AIFeedback"),
    ):
        from rest_framework.test import force_authenticate  # noqa: E402

        view = NeuroMemoryManagementView.as_view()
        force_authenticate(request, user=user)
        response = view(request)

        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["message"] == "Neuro-Symbolic profile reset."
