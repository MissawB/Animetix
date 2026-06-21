"""Coverage-focused tests for animetix.api.labs endpoints.

Complements the existing per-feature labs tests (test_audio_lab, test_video_lab,
test_manga_lab, test_spatial_lab, test_singularity_api, test_voice_cloning_api,
test_diagnostics_api, test_voice_profile_api) by exercising the endpoints that
were previously uncovered: latent-space / daily-challenge / transparency data
views, the remaining Singularity POST actions (compile / plasticity / quantum /
evolve_dynamic / swarm), the Liquid Neural Network lab, the Manga metadata +
Manga-Voice orchestration, Video-RAG index/search, Tree-of-Thoughts, and the
Singularity Command Center -- plus validation (400) and error (500) paths.

Pattern: views resolve services via ``get_container`` imported into the
``animetix.api.labs`` namespace, so it is patched there. Permission classes are
bypassed via ``as_view(permission_classes=[])`` (same trick used in the existing
audio/spatial tests) so we exercise the handler logic directly with a
``RequestFactory`` request.
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
    TransparencyDataView,
    TreeOfThoughtsLabView,
    VideoRAGIndexView,
    VideoRAGSearchView,
)
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from rest_framework.test import force_authenticate

factory = RequestFactory()


def _container_patch(mock_container):
    p = patch("animetix.api.labs.get_container")
    started = p.start()
    started.return_value = mock_container
    return p


# --------------------------------------------------------------------------- #
# LatentSpaceDataView
# --------------------------------------------------------------------------- #
def test_latent_space_data_view_404_when_missing(tmp_path):
    """No artifact files -> 404 with empty list body."""
    request = factory.get("/api/v1/latent-space/?media=anime&type=thematic")
    view = LatentSpaceDataView.as_view()
    with patch("animetix.api.labs.os.path.exists", return_value=False):
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
        patch("animetix.api.labs.os.path.exists", return_value=True),
        patch("animetix.api.labs.json.load", return_value=payload),
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
        patch("animetix.api.labs.os.path.exists", return_value=True),
        patch("builtins.open", side_effect=OSError("disk gone")),
    ):
        response = view(request)
    assert response.status_code == 500
    assert "disk gone" in response.data["error"]


# --------------------------------------------------------------------------- #
# DailyChallengeDataView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_daily_challenge_data_view_creates_and_returns():
    request = factory.get("/api/v1/daily-challenge/")
    view = DailyChallengeDataView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert response.data["media_type"] == "Anime"
    assert response.data["reward_xp"] == 500
    mode_ids = {m["id"] for m in response.data["modes"]}
    assert {"classic", "vision", "emoji"} <= mode_ids


# --------------------------------------------------------------------------- #
# TransparencyDataView
# --------------------------------------------------------------------------- #
def test_transparency_data_view_success():
    request = factory.get("/api/v1/transparency/")
    mock_container = MagicMock()
    mock_container.core.health_dashboard_service().get_global_health.return_value = {
        "status": "ok"
    }
    mock_container.core.graph_healer_service().audit_graph_quality.return_value = {
        "nodes": 10
    }
    p = _container_patch(mock_container)
    try:
        view = TransparencyDataView.as_view(permission_classes=[])
        response = view(request)
    finally:
        p.stop()
    assert response.status_code == 200
    assert response.data["status"] == "ok"
    assert response.data["knowledge_graph"] == {"nodes": 10}


def test_transparency_data_view_graph_unavailable():
    """Graph audit failure is swallowed; status stays 200 with 'unavailable'."""
    request = factory.get("/api/v1/transparency/")
    mock_container = MagicMock()
    mock_container.core.health_dashboard_service().get_global_health.return_value = {
        "status": "ok"
    }
    mock_container.core.graph_healer_service().audit_graph_quality.side_effect = (
        Exception("neo4j down")
    )
    p = _container_patch(mock_container)
    try:
        view = TransparencyDataView.as_view(permission_classes=[])
        response = view(request)
    finally:
        p.stop()
    assert response.status_code == 200
    assert response.data["knowledge_graph"] == {"status": "unavailable"}


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


def _run_singularity(payload, mock_container):
    request = _singularity_request(payload)
    p = _container_patch(mock_container)
    d = patch("animetix.api.labs.deduct_berrix")
    d.start()
    try:
        view = SingularityLabDataView.as_view(permission_classes=[])
        return view(request)
    finally:
        p.stop()
        d.stop()


def test_singularity_compile_success():
    mock_container = MagicMock()
    compiler = MagicMock()
    compiler.mode = "jit"
    compiler.analyze_and_optimize.return_value = lambda a, b: 1.0
    mock_container.core.self_evolving_compiler.return_value = compiler
    response = _run_singularity(
        {"action": "compile", "function_name": "cosine_similarity"}, mock_container
    )
    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["mode"] == "jit"


def test_singularity_compile_disallowed_function():
    response = _run_singularity(
        {"action": "compile", "function_name": "os.system"}, MagicMock()
    )
    assert response.status_code == 400
    assert "not allowed" in response.data["error"]


def test_singularity_compile_error():
    mock_container = MagicMock()
    mock_container.core.self_evolving_compiler.return_value.analyze_and_optimize.side_effect = Exception(
        "compile boom"
    )
    response = _run_singularity(
        {"action": "compile", "function_name": "vector_norm"}, mock_container
    )
    assert response.status_code == 500
    assert response.data["error"] == "compile boom"


def test_singularity_plasticity_success():
    mock_container = MagicMock()
    service = MagicMock()
    service.update_hebbian.return_value = np.zeros((10, 10))
    service.update_stdp.return_value = 0.01
    mock_container.core.synaptic_plasticity_simulator.return_value = service
    response = _run_singularity(
        {"action": "plasticity", "trigger_spikes": [0, 1], "learning_rate": 0.05},
        mock_container,
    )
    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["stdp_log"]  # STDP appended for >=2 indices
    assert "weights_mean" in response.data


def test_singularity_plasticity_error():
    mock_container = MagicMock()
    mock_container.core.synaptic_plasticity_simulator.return_value.trigger_spikes.side_effect = Exception(
        "spike fail"
    )
    response = _run_singularity({"action": "plasticity"}, mock_container)
    assert response.status_code == 500
    assert response.data["error"] == "spike fail"


def test_singularity_quantum_success():
    mock_container = MagicMock()
    model = MagicMock()
    model.measure_preference.return_value = (0.73, "shonen")
    model.state = [1, 0, 0, 0]
    mock_container.core.quantum_cognitive_model.return_value = model
    response = _run_singularity(
        {"action": "quantum", "theme": "Shonen"}, mock_container
    )
    assert response.status_code == 200
    assert response.data["theme"] == "shonen"
    assert response.data["probability"] == pytest.approx(0.73)
    assert response.data["outcome"] == "shonen"


def test_singularity_quantum_error():
    mock_container = MagicMock()
    mock_container.core.quantum_cognitive_model.return_value.measure_preference.side_effect = Exception(
        "decohere"
    )
    response = _run_singularity({"action": "quantum"}, mock_container)
    assert response.status_code == 500
    assert response.data["error"] == "decohere"


def test_singularity_evolve_dynamic_success():
    mock_container = MagicMock()
    compiler = MagicMock()
    fn = MagicMock(return_value=42)
    fn.__name__ = "dynamic_kernel"
    compiler.evolve_with_llm.return_value = fn
    mock_container.core.self_evolving_compiler.return_value = compiler
    mock_container.agentic.llm_service.return_value = MagicMock()
    response = _run_singularity(
        {"action": "evolve_dynamic", "task": "dot_product"}, mock_container
    )
    assert response.status_code == 200
    assert response.data["kernel_name"] == "dynamic_kernel"
    assert response.data["result"] == "42"


def test_singularity_evolve_dynamic_error():
    mock_container = MagicMock()
    mock_container.core.self_evolving_compiler.return_value.evolve_with_llm.side_effect = Exception(
        "llm down"
    )
    response = _run_singularity({"action": "evolve_dynamic"}, mock_container)
    assert response.status_code == 500
    assert response.data["error"] == "llm down"


def test_singularity_swarm_missing_fields():
    response = _run_singularity({"action": "swarm", "fact": "x"}, MagicMock())
    assert response.status_code == 400
    assert "fact and media" in response.data["error"]


def test_singularity_swarm_success():
    mock_container = MagicMock()
    orchestrator = MagicMock()
    orchestrator.get_paxos_diagnostics.return_value = {"consensus": True, "round": 3}
    mock_container.core.swarm_consensus_orchestrator.return_value = orchestrator
    response = _run_singularity(
        {"action": "swarm", "fact": "Luffy is captain", "media": "One Piece"},
        mock_container,
    )
    assert response.status_code == 200
    assert response.data["consensus"] is True


def test_singularity_swarm_error():
    mock_container = MagicMock()
    mock_container.core.swarm_consensus_orchestrator.return_value.get_paxos_diagnostics.side_effect = Exception(
        "no quorum"
    )
    response = _run_singularity(
        {"action": "swarm", "fact": "a", "media": "b"}, mock_container
    )
    assert response.status_code == 500
    assert response.data["error"] == "no quorum"


# --------------------------------------------------------------------------- #
# LiquidNeuralNetworkLabView
# --------------------------------------------------------------------------- #
def test_liquid_nn_success():
    request = factory.post(
        "/api/v1/labs/liquid-nn/",
        json.dumps({"signal": [[0.5, 0.2]], "dt": 0.1}),
        content_type="application/json",
    )
    mock_container = MagicMock()
    lnn = MagicMock()
    lnn.process_continuous_signal.return_value = [[0.1, 0.2]]
    lnn.state = np.array([0.1, 0.2])
    mock_container.core.liquid_neural_network.return_value = lnn
    p = _container_patch(mock_container)
    try:
        view = LiquidNeuralNetworkLabView.as_view(permission_classes=[])
        response = view(request)
    finally:
        p.stop()
    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["final_state"] == [0.1, 0.2]


def test_liquid_nn_error():
    request = factory.post(
        "/api/v1/labs/liquid-nn/",
        json.dumps({"signal": [[0.5, 0.2]]}),
        content_type="application/json",
    )
    mock_container = MagicMock()
    mock_container.core.liquid_neural_network.return_value.process_continuous_signal.side_effect = Exception(
        "diverged"
    )
    p = _container_patch(mock_container)
    try:
        view = LiquidNeuralNetworkLabView.as_view(permission_classes=[])
        response = view(request)
    finally:
        p.stop()
    assert response.status_code == 500
    assert response.data["error"] == "diverged"


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
        patch("animetix.api.labs.deduct_berrix"),
        patch("django.core.cache.cache.set") as mock_cache_set,
        patch("animetix.api.labs.settings") as mock_settings,
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
        patch("animetix.api.labs.deduct_berrix"),
        patch("django.core.cache.cache.set"),
        patch("animetix.api.labs.settings") as mock_settings,
        patch("animetix.api.labs.GCPWorkflowsClient") as mock_client_cls,
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
        patch("animetix.api.labs.deduct_berrix"),
        patch("django.core.cache.cache.set"),
        patch("animetix.api.labs.settings") as mock_settings,
        patch("animetix.api.labs.GCPWorkflowsClient") as mock_client_cls,
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
    mock_container = MagicMock()
    mock_container.agentic.video_rag_service.return_value.index_video.return_value = 7
    p = _container_patch(mock_container)
    try:
        view = VideoRAGIndexView.as_view(permission_classes=[])
        response = view(request)
    finally:
        p.stop()
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
    mock_container = MagicMock()
    mock_container.agentic.video_rag_service.return_value.index_video.side_effect = (
        Exception("index fail")
    )
    p = _container_patch(mock_container)
    try:
        view = VideoRAGIndexView.as_view(permission_classes=[])
        response = view(request)
    finally:
        p.stop()
    assert response.status_code == 500
    assert response.data["error"] == "index fail"


# --------------------------------------------------------------------------- #
# VideoRAGSearchView
# --------------------------------------------------------------------------- #
def test_video_rag_search_missing_query():
    request = factory.get("/api/v1/labs/video/search/")
    view = VideoRAGSearchView.as_view()
    response = view(request)
    assert response.status_code == 400
    assert "query q is required" in response.data["error"]


def test_video_rag_search_success():
    request = factory.get("/api/v1/labs/video/search/?q=fight")
    mock_container = MagicMock()
    mock_container.agentic.video_rag_service.return_value.search_video_segment.return_value = [
        {"ts": 12, "score": 0.9}
    ]
    p = _container_patch(mock_container)
    try:
        view = VideoRAGSearchView.as_view()
        response = view(request)
    finally:
        p.stop()
    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["results"][0]["ts"] == 12


def test_video_rag_search_error():
    request = factory.get("/api/v1/labs/video/search/?q=fight")
    mock_container = MagicMock()
    mock_container.agentic.video_rag_service.return_value.search_video_segment.side_effect = Exception(
        "search down"
    )
    p = _container_patch(mock_container)
    try:
        view = VideoRAGSearchView.as_view()
        response = view(request)
    finally:
        p.stop()
    assert response.status_code == 500
    assert response.data["error"] == "search down"


# --------------------------------------------------------------------------- #
# TreeOfThoughtsLabView
# --------------------------------------------------------------------------- #
def test_tree_of_thoughts_missing_query():
    request = factory.post(
        "/api/v1/labs/tot/", json.dumps({}), content_type="application/json"
    )
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
    view = TreeOfThoughtsLabView.as_view()
    # The injected service is an attribute on the instantiated view; patch it.
    with patch.object(
        TreeOfThoughtsLabView,
        "solve",
        create=True,
    ):
        instance_service = MagicMock()
        instance_service.solve_with_tree_of_thoughts.return_value = {"answer": "42"}
        with patch.object(
            TreeOfThoughtsLabView,
            "__init__",
            lambda self, **kw: setattr(self, "tot_service", instance_service)
            or super(TreeOfThoughtsLabView, self).__init__(),
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
    view = TreeOfThoughtsLabView.as_view()
    instance_service = MagicMock()
    instance_service.solve_with_tree_of_thoughts.side_effect = Exception("tot boom")
    with patch.object(
        TreeOfThoughtsLabView,
        "__init__",
        lambda self, **kw: setattr(self, "tot_service", instance_service)
        or super(TreeOfThoughtsLabView, self).__init__(),
    ):
        response = view(request)
    assert response.status_code == 500
    assert response.data["error"] == "tot boom"


# --------------------------------------------------------------------------- #
# SingularityCommandCenterView
# --------------------------------------------------------------------------- #
def test_singularity_command_center():
    request = factory.get("/api/v1/singularity-lab/command-center/")
    mock_container = MagicMock()
    p = _container_patch(mock_container)
    try:
        view = SingularityCommandCenterView.as_view(permission_classes=[])
        response = view(request)
    finally:
        p.stop()
    assert response.status_code == 200
    assert response.data["status"] == "operational"
    service_ids = {s["id"] for s in response.data["services"]}
    assert {"quantum", "plasticity", "swarm", "lnn"} <= service_ids
    assert len(response.data["events"]) == 3
