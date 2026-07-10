"""Coverage-focused tests for animetix.api.labs endpoints.

Complements the existing per-feature labs tests (test_audio_lab, test_video_lab,
test_manga_lab, test_spatial_lab, test_singularity_api, test_voice_cloning_api,
test_diagnostics_api, test_voice_profile_api) by exercising the endpoints that
were previously uncovered: latent-space / daily-challenge / transparency data
views, the remaining Singularity POST actions (compile / plasticity / quantum /
evolve_dynamic / swarm), the Liquid Neural Network lab, the Manga metadata +
Manga-Voice orchestration, Video-RAG index/search, Tree-of-Thoughts, and the
Singularity Command Center -- plus validation (400) and error (500) paths.

Pattern: views receive their services via ``@inject``/``Provide[...]`` from the
real DI container, so tests override the concrete providers
(``container.<sub>.<service>.override(mock)``) and reset them afterwards with
``reset_override()`` on the provider (never on the container). Permission
classes are bypassed via ``as_view(permission_classes=[])`` (same trick used in
the existing audio/spatial tests) so we exercise the handler logic directly
with a ``RequestFactory`` request.
"""

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from animetix.api.labs import (
    DailyChallengeDataView,
    LatentSpaceDataView,
    LiquidNeuralNetworkLabView,
    MangaLabDataView,
    MangaVoiceLabView,
    SingularityCommandCenterView,
    SingularityLabDataView,
    TreeOfThoughtsLabView,
    VideoRAGIndexView,
    VideoRAGSearchView,
)
from animetix.containers import get_container
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from rest_framework.test import force_authenticate

factory = RequestFactory()


# --------------------------------------------------------------------------- #
# LatentSpaceDataView
# --------------------------------------------------------------------------- #
def test_latent_space_data_view_404_when_missing(tmp_path):
    """No artifact files -> 404 with empty list body."""
    request = factory.get("/api/v1/latent-space/?media=anime&type=thematic")
    view = LatentSpaceDataView.as_view()
    with patch("animetix.api.labs.dashboards.os.path.exists", return_value=False):
        response = view(request)
    assert response.status_code == 404
    assert response.data == []


def test_latent_space_data_view_success(tmp_path):
    """Existing artifact file is read and returned verbatim."""
    payload = [{"x": 1, "y": 2, "z": 3, "label": "Naruto"}]
    request = factory.get("/api/v1/latent-space/?media=manga&type=visual")
    view = LatentSpaceDataView.as_view()

    m = MagicMock()
    m.read.return_value = json.dumps(payload)
    with (
        patch("animetix.api.labs.dashboards.os.path.exists", return_value=True),
        patch("animetix.api.labs.dashboards.json.load", return_value=payload),
        patch("builtins.open", MagicMock()),
    ):
        response = view(request)
    assert response.status_code == 200
    assert response.data == payload


def test_latent_space_data_view_read_error():
    """Exception while reading the file -> 500 with error message."""
    request = factory.get("/api/v1/latent-space/")
    view = LatentSpaceDataView.as_view()
    with (
        patch("animetix.api.labs.dashboards.os.path.exists", return_value=True),
        patch("builtins.open", side_effect=OSError("disk gone")),
    ):
        response = view(request)
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# DailyChallengeDataView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_daily_challenge_data_view_creates_and_returns():
    request = factory.get("/api/v1/daily-challenge/")
    view = DailyChallengeDataView.as_view()
    response = view(request)
    assert response.status_code == 200
    # Redesigned: one challenge per universe (anime / manga / character) with
    # date navigation, instead of a single top-level media_type + reward_xp.
    assert response.data["is_today"] is True
    assert "date" in response.data
    mode_ids = {m["id"] for m in response.data["modes"]}
    assert mode_ids == {"anime", "manga", "character"}
    assert response.data["modes"][0]["media_type"] == "Anime"


@pytest.mark.django_db
def test_daily_challenge_data_view_authenticated_scores():
    """Regression: the authenticated branch does ``from ...models import
    DailyResult`` — in the old monolithic ``labs.py`` (package ``animetix.api``)
    the 3-dot relative import climbed beyond the top-level package and raised
    ImportError on every authenticated request. The move into the
    ``animetix.api.labs`` package makes it resolve to ``animetix.models``.
    """
    import datetime

    from animetix.models import DailyResult

    user = User.objects.create_user(username="daily_auth")
    DailyResult.objects.create(
        user=user,
        media_type="Anime",
        date=datetime.date.today(),
        score=42,
        attempts=3,
    )
    request = factory.get("/api/v1/daily-challenge/")
    force_authenticate(request, user=user)
    view = DailyChallengeDataView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert response.data["total_score"] == 42
    anime_mode = next(m for m in response.data["modes"] if m["id"] == "anime")
    assert anime_mode["completed"] is True
    assert anime_mode["score"] == 42


# --------------------------------------------------------------------------- #
# SingularityLabDataView POST actions
# --------------------------------------------------------------------------- #
def _singularity_request(payload):
    request = factory.post(
        "/api/v1/singularity-lab/", json.dumps(payload), content_type="application/json"
    )
    # force_authenticate bypasses SessionAuthentication's CSRF enforcement that
    # would otherwise 403 a POST coming from RequestFactory.
    force_authenticate(request, user=MagicMock(id=1))
    return request


def _run_singularity(payload, overrides=()):
    """Run SingularityLabDataView with the given (provider, mock) overrides.

    ``overrides`` is an iterable of ``(provider, mock)`` tuples; each provider
    is overridden before the request and reset (per provider — never
    ``container.reset_override()``) afterwards.
    """
    request = _singularity_request(payload)
    # The view injects every singularity service in __init__: stub out the ones
    # the test does not care about so no real (heavy) service is constructed.
    container = get_container()
    default_providers = [
        container.core.synaptic_plasticity_simulator,
        container.core.archetype_drift_service,
        container.core.self_evolving_compiler,
        container.core.quantum_cognitive_model,
        container.core.swarm_consensus_orchestrator,
        container.core.autonomous_domain_synthesizer,
        container.agentic.llm_service,
    ]
    overridden_providers = [provider for provider, _ in overrides]
    explicit_ids = {id(provider) for provider in overridden_providers}
    for provider in default_providers:
        if id(provider) not in explicit_ids:
            provider.override(MagicMock())
            overridden_providers.append(provider)
    for provider, mock in overrides:
        provider.override(mock)
    d = patch("animetix.api.labs.singularity.deduct_berrix")
    d.start()
    try:
        view = SingularityLabDataView.as_view(permission_classes=[])
        return view(request)
    finally:
        for provider in overridden_providers:
            provider.reset_override()
        d.stop()


def test_singularity_compile_success():
    compiler = MagicMock()
    compiler.mode = "jit"
    compiler.analyze_and_optimize.return_value = lambda a, b: 1.0
    container = get_container()
    response = _run_singularity(
        {"action": "compile", "function_name": "cosine_similarity"},
        [(container.core.self_evolving_compiler, compiler)],
    )
    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["mode"] == "jit"


def test_singularity_compile_disallowed_function():
    response = _run_singularity({"action": "compile", "function_name": "os.system"})
    assert response.status_code == 400
    assert "not allowed" in response.data["error"]


def test_singularity_compile_error():
    compiler = MagicMock()
    compiler.analyze_and_optimize.side_effect = Exception("compile boom")
    container = get_container()
    response = _run_singularity(
        {"action": "compile", "function_name": "vector_norm"},
        [(container.core.self_evolving_compiler, compiler)],
    )
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


def test_singularity_plasticity_success():
    service = MagicMock()
    service.update_hebbian.return_value = np.zeros((10, 10))
    service.update_stdp.return_value = 0.01
    container = get_container()
    response = _run_singularity(
        {"action": "plasticity", "trigger_spikes": [0, 1], "learning_rate": 0.05},
        [(container.core.synaptic_plasticity_simulator, service)],
    )
    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["stdp_log"]  # STDP appended for >=2 indices
    assert "weights_mean" in response.data


def test_singularity_plasticity_error():
    service = MagicMock()
    service.trigger_spikes.side_effect = Exception("spike fail")
    container = get_container()
    response = _run_singularity(
        {"action": "plasticity"},
        [(container.core.synaptic_plasticity_simulator, service)],
    )
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


def test_singularity_quantum_success():
    model = MagicMock()
    model.measure_preference.return_value = (0.73, "shonen")
    model.state = [1, 0, 0, 0]
    container = get_container()
    response = _run_singularity(
        {"action": "quantum", "theme": "Shonen"},
        [(container.core.quantum_cognitive_model, model)],
    )
    assert response.status_code == 200
    assert response.data["theme"] == "shonen"
    assert response.data["probability"] == pytest.approx(0.73)
    assert response.data["outcome"] == "shonen"


def test_singularity_quantum_error():
    model = MagicMock()
    model.measure_preference.side_effect = Exception("decohere")
    container = get_container()
    response = _run_singularity(
        {"action": "quantum"},
        [(container.core.quantum_cognitive_model, model)],
    )
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


def test_singularity_evolve_dynamic_success():
    compiler = MagicMock()
    fn = MagicMock(return_value=42)
    fn.__name__ = "dynamic_kernel"
    compiler.evolve_with_llm.return_value = fn
    container = get_container()
    response = _run_singularity(
        {"action": "evolve_dynamic", "task": "dot_product"},
        [
            (container.core.self_evolving_compiler, compiler),
            (container.agentic.llm_service, MagicMock()),
        ],
    )
    assert response.status_code == 200
    assert response.data["kernel_name"] == "dynamic_kernel"
    assert response.data["result"] == "42"


def test_singularity_evolve_dynamic_error():
    compiler = MagicMock()
    compiler.evolve_with_llm.side_effect = Exception("llm down")
    container = get_container()
    response = _run_singularity(
        {"action": "evolve_dynamic"},
        [(container.core.self_evolving_compiler, compiler)],
    )
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


def test_singularity_swarm_missing_fields():
    response = _run_singularity({"action": "swarm", "fact": "x"})
    assert response.status_code == 400
    assert "fact and media" in response.data["error"]


def test_singularity_swarm_success():
    orchestrator = MagicMock()
    orchestrator.get_paxos_diagnostics.return_value = {"consensus": True, "round": 3}
    container = get_container()
    response = _run_singularity(
        {"action": "swarm", "fact": "Luffy is captain", "media": "One Piece"},
        [(container.core.swarm_consensus_orchestrator, orchestrator)],
    )
    assert response.status_code == 200
    assert response.data["consensus"] is True


def test_singularity_swarm_error():
    orchestrator = MagicMock()
    orchestrator.get_paxos_diagnostics.side_effect = Exception("no quorum")
    container = get_container()
    response = _run_singularity(
        {"action": "swarm", "fact": "a", "media": "b"},
        [(container.core.swarm_consensus_orchestrator, orchestrator)],
    )
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# LiquidNeuralNetworkLabView
# --------------------------------------------------------------------------- #
def test_liquid_nn_success():
    request = factory.post(
        "/api/v1/labs/liquid-nn/",
        json.dumps({"signal": [[0.5, 0.2]], "dt": 0.1}),
        content_type="application/json",
    )
    lnn = MagicMock()
    lnn.process_continuous_signal.return_value = [[0.1, 0.2]]
    lnn.state = np.array([0.1, 0.2])
    container = get_container()
    container.core.liquid_neural_network.override(lnn)
    try:
        view = LiquidNeuralNetworkLabView.as_view(permission_classes=[])
        response = view(request)
    finally:
        container.core.liquid_neural_network.reset_override()
    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["final_state"] == [0.1, 0.2]


def test_liquid_nn_error():
    request = factory.post(
        "/api/v1/labs/liquid-nn/",
        json.dumps({"signal": [[0.5, 0.2]]}),
        content_type="application/json",
    )
    lnn = MagicMock()
    lnn.process_continuous_signal.side_effect = Exception("diverged")
    container = get_container()
    container.core.liquid_neural_network.override(lnn)
    try:
        view = LiquidNeuralNetworkLabView.as_view(permission_classes=[])
        response = view(request)
    finally:
        container.core.liquid_neural_network.reset_override()
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# MangaLabDataView
# --------------------------------------------------------------------------- #
def test_manga_lab_data_view():
    request = factory.get("/api/v1/labs/manga-lab/")
    view = MangaLabDataView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert response.data["status"] == "active"
    ids = {t["id"] for t in response.data["tools"]}
    assert {"clean", "translate", "voice"} <= ids


# --------------------------------------------------------------------------- #
# MangaVoiceLabView
# --------------------------------------------------------------------------- #
def test_manga_voice_missing_payload():
    request = factory.post(
        "/api/v1/labs/manga-voice/",
        json.dumps({"image": "x"}),
        content_type="application/json",
    )
    force_authenticate(request, user=MagicMock(id=1))
    view = MangaVoiceLabView.as_view(permission_classes=[])
    response = view(request)
    assert response.status_code == 400
    assert "Missing image or reference_audio" in response.data["error"]


def test_manga_voice_local_fallback():
    """Non-production path returns 202 with a task_id and seeds the cache."""
    request = factory.post(
        "/api/v1/labs/manga-voice/",
        json.dumps(
            {"image": "img-b64", "reference_audio": "aud-b64", "target_lang": "English"}
        ),
        content_type="application/json",
    )
    force_authenticate(request, user=MagicMock(id=1))
    with (
        patch("animetix.api.labs.manga.deduct_berrix"),
        patch("django.core.cache.cache.set") as mock_cache_set,
        patch("animetix.api.labs.manga.settings") as mock_settings,
    ):
        mock_settings.IS_PRODUCTION = False
        view = MangaVoiceLabView.as_view(permission_classes=[])
        response = view(request)
    assert response.status_code == 202
    assert "task_id" in response.data
    # cache seeded at least once (pending init + success result on the local path)
    assert mock_cache_set.called


def test_manga_voice_production_success():
    request = factory.post(
        "/api/v1/labs/manga-voice/",
        json.dumps({"image": "img", "reference_audio": "aud"}),
        content_type="application/json",
    )
    force_authenticate(request, user=MagicMock(id=1))
    with (
        patch("animetix.api.labs.manga.deduct_berrix"),
        patch("django.core.cache.cache.set"),
        patch("animetix.api.labs.manga.settings") as mock_settings,
        patch("animetix.api.labs.manga.GCPWorkflowsClient") as mock_client_cls,
    ):
        mock_settings.IS_PRODUCTION = True
        client = mock_client_cls.return_value
        client.trigger_pipeline.return_value = "exec-123"
        view = MangaVoiceLabView.as_view(permission_classes=[])
        response = view(request)
    assert response.status_code == 202
    assert "task_id" in response.data
    client.trigger_pipeline.assert_called_once()
    client.enqueue_polling_task.assert_called_once()


def test_manga_voice_production_error():
    request = factory.post(
        "/api/v1/labs/manga-voice/",
        json.dumps({"image": "img", "reference_audio": "aud"}),
        content_type="application/json",
    )
    force_authenticate(request, user=MagicMock(id=1))
    with (
        patch("animetix.api.labs.manga.deduct_berrix"),
        patch("django.core.cache.cache.set"),
        patch("animetix.api.labs.manga.settings") as mock_settings,
        patch("animetix.api.labs.manga.GCPWorkflowsClient") as mock_client_cls,
    ):
        mock_settings.IS_PRODUCTION = True
        mock_client_cls.return_value.trigger_pipeline.side_effect = Exception(
            "gcp boom"
        )
        view = MangaVoiceLabView.as_view(permission_classes=[])
        response = view(request)
    assert response.status_code == 500
    assert "Failed to start workflow" in response.data["error"]


# --------------------------------------------------------------------------- #
# VideoRAGIndexView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_video_rag_index_missing_fields():
    user = User.objects.create_user(username="ragindex_missing")
    request = factory.post("/api/v1/labs/video/index/", {})
    force_authenticate(request, user=user)
    view = VideoRAGIndexView.as_view(permission_classes=[])
    response = view(request)
    assert response.status_code == 400
    assert "video and video_id" in response.data["error"]


@pytest.mark.django_db
def test_video_rag_index_success():
    user = User.objects.create_user(username="ragindex_ok")
    video = SimpleUploadedFile("v.mp4", b"vid", content_type="video/mp4")
    request = factory.post(
        "/api/v1/labs/video/index/", {"video": video, "video_id": "ep1"}
    )
    force_authenticate(request, user=user)
    mock_service = MagicMock()
    mock_service.index_video.return_value = 7
    container = get_container()
    container.agentic.video_rag_service.override(mock_service)
    try:
        view = VideoRAGIndexView.as_view(permission_classes=[])
        response = view(request)
    finally:
        container.agentic.video_rag_service.reset_override()
    assert response.status_code == 200
    assert response.data["indexed_segments"] == 7


@pytest.mark.django_db
def test_video_rag_index_error():
    user = User.objects.create_user(username="ragindex_err")
    video = SimpleUploadedFile("v.mp4", b"vid", content_type="video/mp4")
    request = factory.post(
        "/api/v1/labs/video/index/", {"video": video, "video_id": "ep1"}
    )
    force_authenticate(request, user=user)
    mock_service = MagicMock()
    mock_service.index_video.side_effect = Exception("index fail")
    container = get_container()
    container.agentic.video_rag_service.override(mock_service)
    try:
        view = VideoRAGIndexView.as_view(permission_classes=[])
        response = view(request)
    finally:
        container.agentic.video_rag_service.reset_override()
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# VideoRAGSearchView
# --------------------------------------------------------------------------- #
def test_video_rag_search_missing_query():
    request = factory.get("/api/v1/labs/video/search/")
    force_authenticate(request, user=MagicMock(id=1))
    view = VideoRAGSearchView.as_view(permission_classes=[])
    response = view(request)
    assert response.status_code == 400
    assert "query q is required" in response.data["error"]


def test_video_rag_search_success():
    request = factory.get("/api/v1/labs/video/search/?q=fight")
    force_authenticate(request, user=MagicMock(id=1))
    mock_service = MagicMock()
    mock_service.search_video_segment.return_value = [{"ts": 12, "score": 0.9}]
    mock_usage = MagicMock()
    mock_usage.check_quota.return_value = True
    container = get_container()
    container.agentic.video_rag_service.override(mock_service)
    container.infrastructure.usage_port.override(mock_usage)
    d = patch("animetix.api.labs.video.deduct_berrix")
    d.start()
    try:
        view = VideoRAGSearchView.as_view(permission_classes=[])
        response = view(request)
    finally:
        container.agentic.video_rag_service.reset_override()
        container.infrastructure.usage_port.reset_override()
        d.stop()
    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["results"][0]["ts"] == 12


def test_video_rag_search_error():
    request = factory.get("/api/v1/labs/video/search/?q=fight")
    force_authenticate(request, user=MagicMock(id=1))
    mock_service = MagicMock()
    mock_service.search_video_segment.side_effect = Exception("search down")
    mock_usage = MagicMock()
    mock_usage.check_quota.return_value = True
    container = get_container()
    container.agentic.video_rag_service.override(mock_service)
    container.infrastructure.usage_port.override(mock_usage)
    d = patch("animetix.api.labs.video.deduct_berrix")
    d.start()
    try:
        view = VideoRAGSearchView.as_view(permission_classes=[])
        response = view(request)
    finally:
        container.agentic.video_rag_service.reset_override()
        container.infrastructure.usage_port.reset_override()
        d.stop()
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# TreeOfThoughtsLabView
# --------------------------------------------------------------------------- #
def test_tree_of_thoughts_missing_query():
    request = factory.post(
        "/api/v1/labs/tot/", json.dumps({}), content_type="application/json"
    )
    # GPU feature → login required (the "Query required" 400 is returned before
    # the Berrix charge, so no need to mock deduct_berrix here).
    force_authenticate(request, user=MagicMock(id=1))
    view = TreeOfThoughtsLabView.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data["error"] == "Query required"


def test_tree_of_thoughts_success():
    request = factory.post(
        "/api/v1/labs/tot/",
        json.dumps({"query": "Solve X"}),
        content_type="application/json",
    )
    force_authenticate(request, user=MagicMock(id=1))
    view = TreeOfThoughtsLabView.as_view()
    # The injected service is an attribute on the instantiated view; patch it.
    with patch.object(
        TreeOfThoughtsLabView,
        "solve",
        create=True,
    ):
        instance_service = MagicMock()
        instance_service.solve_with_tree_of_thoughts.return_value = {"answer": "42"}
        with (
            patch.object(
                TreeOfThoughtsLabView,
                "__init__",
                lambda self, **kw: setattr(self, "tot_service", instance_service)
                or super(TreeOfThoughtsLabView, self).__init__(),
            ),
            patch("animetix.api.labs.singularity.deduct_berrix"),
        ):
            response = view(request)
    assert response.status_code == 200
    assert response.data["answer"] == "42"


def test_tree_of_thoughts_error():
    request = factory.post(
        "/api/v1/labs/tot/",
        json.dumps({"query": "Solve X"}),
        content_type="application/json",
    )
    force_authenticate(request, user=MagicMock(id=1))
    view = TreeOfThoughtsLabView.as_view()
    instance_service = MagicMock()
    instance_service.solve_with_tree_of_thoughts.side_effect = Exception("tot boom")
    with (
        patch.object(
            TreeOfThoughtsLabView,
            "__init__",
            lambda self, **kw: setattr(self, "tot_service", instance_service)
            or super(TreeOfThoughtsLabView, self).__init__(),
        ),
        patch("animetix.api.labs.singularity.deduct_berrix"),
    ):
        response = view(request)
    assert response.status_code == 500
    assert response.data["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# SingularityCommandCenterView
# --------------------------------------------------------------------------- #
def test_singularity_command_center():
    request = factory.get("/api/v1/singularity-lab/command-center/")
    view = SingularityCommandCenterView.as_view(permission_classes=[])
    response = view(request)
    assert response.status_code == 200
    assert response.data["status"] == "operational"
    service_ids = {s["id"] for s in response.data["services"]}
    assert {"quantum", "plasticity", "swarm", "lnn"} <= service_ids
    assert len(response.data["events"]) == 3
