"""Coverage for animetix.api.mlops view module.

Exercises the MLOps admin endpoints:
  - AIREvaluationViewSet (stats / failures)         [DI: eval_adapter]
  - LatentSpaceAPIView (found / not found)          [DI: repository]
  - AIFeedbackAPIView (get history / post feedback)  [DI: feedback_adapter]
  - GoldDatasetViewSet (sync / validate ok+404)      [DI: gold_dataset_adapter]
  - DPOCurationViewSet (list / create ok+invalid)    [DI: dpo_feedback_loop]
  - DSPyOptimizerView (success / missing / error)    [DI: dspy_prompt_optimizer]
  - SOTABenchmarkListView                            [DI: sota_benchmark_service]
  - DPOFeedbackLoopView (get / export / optimize)    [DI: dpo_feedback_loop]
  - AdaptersView (get / set_primary / set_model)     [DI: inference_engine + unified]

Every view is DI-injected; collaborators are overridden through the global
``container`` providers. All collaborators are mocked; ORM uses the sqlite
test DB.
"""

from unittest.mock import MagicMock

import pytest
from animetix.api import mlops as mlops_mod
from animetix.containers import container
from animetix.models import AIFeedback, AIREvalResult, GoldDatasetEntry
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", password="password", email="a@b.c"
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(username="plain", password="password")


# --------------------------------------------------------------------------- #
# AIREvaluationViewSet
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_evaluation_stats(admin_client):
    eval_mock = MagicMock()
    eval_mock.get_evaluation_stats.return_value = {"avg_faithfulness": 0.9, "count": 3}

    with container.persistence.eval_adapter.override(providers.Object(eval_mock)):
        response = admin_client.get(reverse("admin_ai_eval_data"))

    assert response.status_code == 200
    assert response.json()["avg_faithfulness"] == 0.9


@pytest.mark.django_db
def test_evaluation_failures(admin_client):
    AIREvalResult.objects.create(
        input_context="q", output_text="a", hallucination_detected=True
    )
    AIREvalResult.objects.create(input_context="q2", output_text="a2", faithfulness=0.2)
    AIREvalResult.objects.create(
        input_context="ok", output_text="good", faithfulness=0.9, relevancy=0.9
    )

    eval_mock = MagicMock()
    with container.persistence.eval_adapter.override(providers.Object(eval_mock)):
        response = admin_client.get(reverse("mlops_eval_failures"))

    assert response.status_code == 200
    # Only the two failing rows are returned.
    assert len(response.json()) == 2


# --------------------------------------------------------------------------- #
# LatentSpaceAPIView
#
# NOTE: the ``api_latent_space`` URL is served by labs.LatentSpaceDataView,
# which shadows this mlops view, so the mlops view is unreachable via reverse().
# We therefore drive it directly with an APIRequestFactory request, injecting the
# mocked repository explicitly (the @inject default would otherwise resolve the
# real singleton).
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_latent_space_found():
    from rest_framework.test import APIRequestFactory

    repo = MagicMock()
    repo.load_latent_space.return_value = {"points": [[0.1, 0.2]]}

    view = mlops_mod.LatentSpaceAPIView(repository=repo)
    request = APIRequestFactory().get("/", {"media": "Anime", "type": "Thematic"})
    response = view.get(request)

    assert response.status_code == 200
    assert response.data["points"] == [[0.1, 0.2]]
    # query params are lowercased before hitting the repo
    repo.load_latent_space.assert_called_once_with("anime", "thematic")


@pytest.mark.django_db
def test_latent_space_not_found():
    from rest_framework.test import APIRequestFactory

    repo = MagicMock()
    repo.load_latent_space.return_value = None

    view = mlops_mod.LatentSpaceAPIView(repository=repo)
    request = APIRequestFactory().get("/")
    response = view.get(request)

    assert response.status_code == 404
    assert response.data["error"] == "Data not found"


# --------------------------------------------------------------------------- #
# AIFeedbackAPIView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_feedback_get_history(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)
    AIFeedback.objects.create(
        user=normal_user, input_context="ctx", output_text="out", is_positive=True
    )
    feedback_mock = MagicMock()
    with container.persistence.feedback_adapter.override(
        providers.Object(feedback_mock)
    ):
        response = api_client.get(reverse("submit_ai_feedback"))

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_feedback_post_valid(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)
    feedback_mock = MagicMock()
    with container.persistence.feedback_adapter.override(
        providers.Object(feedback_mock)
    ):
        response = api_client.post(
            reverse("submit_ai_feedback"),
            {
                "is_positive": True,
                "type": "rag",
                "input_context": "Who is X?",
                "output_text": "X is Y.",
            },
            format="json",
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    feedback_mock.save_feedback.assert_called_once()


@pytest.mark.django_db
def test_feedback_post_invalid(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)
    feedback_mock = MagicMock()
    with container.persistence.feedback_adapter.override(
        providers.Object(feedback_mock)
    ):
        # is_positive missing -> serializer invalid -> 400
        response = api_client.post(
            reverse("submit_ai_feedback"), {"type": "rag"}, format="json"
        )

    assert response.status_code == 400


# --------------------------------------------------------------------------- #
# GoldDatasetViewSet
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_gold_sync_positive_feedback(admin_client):
    gold_mock = MagicMock()
    gold_mock.sync_positive_feedback.return_value = 7

    with container.persistence.gold_dataset_adapter.override(
        providers.Object(gold_mock)
    ):
        response = admin_client.post(reverse("mlops_gold_dataset_sync"))

    assert response.status_code == 200
    assert response.json()["synced_count"] == 7


@pytest.mark.django_db
def test_gold_validate_success(admin_client):
    entry = GoldDatasetEntry.objects.create(instruction="i", context="c", response="r")
    gold_mock = MagicMock()
    gold_mock.validate_entry.return_value = True

    with container.persistence.gold_dataset_adapter.override(
        providers.Object(gold_mock)
    ):
        response = admin_client.post(
            reverse("mlops_gold_dataset_validate", args=[entry.id])
        )

    assert response.status_code == 200
    assert response.json()["status"] == "validated"


@pytest.mark.django_db
def test_gold_validate_not_found(admin_client):
    entry = GoldDatasetEntry.objects.create(instruction="i", context="c", response="r")
    gold_mock = MagicMock()
    gold_mock.validate_entry.return_value = False

    with container.persistence.gold_dataset_adapter.override(
        providers.Object(gold_mock)
    ):
        response = admin_client.post(
            reverse("mlops_gold_dataset_validate", args=[entry.id])
        )

    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# DPOCurationViewSet
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_dpo_curation_list(admin_client):
    dpo_loop = MagicMock()
    dpo_loop.get_rejected_for_curation.return_value = [{"id": 1, "text": "x"}]
    with container.core.dpo_feedback_loop.override(providers.Object(dpo_loop)):
        response = admin_client.get(reverse("api_dpo_curation"), {"limit": "10"})

    assert response.status_code == 200
    assert response.json()[0]["id"] == 1
    dpo_loop.get_rejected_for_curation.assert_called_once_with(limit=10)


@pytest.mark.django_db
def test_dpo_curation_create_success(admin_client):
    dpo_loop = MagicMock()
    dpo_loop.curate_feedback.return_value = True
    with container.core.dpo_feedback_loop.override(providers.Object(dpo_loop)):
        response = admin_client.post(
            reverse("api_dpo_curation"),
            {"feedback_id": 5, "chosen_text": "better answer"},
            format="json",
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.django_db
def test_dpo_curation_create_invalid(admin_client):
    with container.core.dpo_feedback_loop.override(providers.Object(MagicMock())):
        response = admin_client.post(
            reverse("api_dpo_curation"), {"chosen_text": "x"}, format="json"
        )
    assert response.status_code == 400


@pytest.mark.django_db
def test_dpo_curation_create_failure(admin_client):
    dpo_loop = MagicMock()
    dpo_loop.curate_feedback.return_value = False
    with container.core.dpo_feedback_loop.override(providers.Object(dpo_loop)):
        response = admin_client.post(
            reverse("api_dpo_curation"),
            {"feedback_id": 5, "chosen_text": "x"},
            format="json",
        )
    assert response.status_code == 500


# --------------------------------------------------------------------------- #
# DSPyOptimizerView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_dspy_optimizer_missing_template(admin_client):
    optimizer = MagicMock()
    with container.core.dspy_prompt_optimizer.override(providers.Object(optimizer)):
        response = admin_client.post(reverse("api_dspy_optimizer"), {}, format="json")
    assert response.status_code == 400
    assert response.json()["error"] == "template is required"


@pytest.mark.django_db
def test_dspy_optimizer_success_with_default_dataset(admin_client):
    optimizer = MagicMock()
    optimizer.evaluate_and_select_best.return_value = ("BEST", 0.95)
    optimizer.mutate_template.return_value = ["m1", "m2", "m3"]

    with container.core.dspy_prompt_optimizer.override(providers.Object(optimizer)):
        # no dataset -> the view supplies a fallback dataset
        response = admin_client.post(
            reverse("api_dspy_optimizer"), {"template": "T"}, format="json"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["best_template"] == "BEST"
    assert body["best_score"] == 0.95
    assert body["all_mutations"] == ["m1", "m2", "m3"]


@pytest.mark.django_db
def test_dspy_optimizer_exception(admin_client):
    optimizer = MagicMock()
    optimizer.evaluate_and_select_best.side_effect = ValueError("bad template")

    with container.core.dspy_prompt_optimizer.override(providers.Object(optimizer)):
        response = admin_client.post(
            reverse("api_dspy_optimizer"),
            {"template": "T", "dataset": [{"query": "q", "expected": "e"}]},
            format="json",
        )

    assert response.status_code == 500
    assert response.json()["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# SOTABenchmarkListView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_sota_benchmarks(api_client):
    service = MagicMock()
    service.get_all_benchmarks.return_value = [{"model": "X"}]
    service.get_best_model.return_value = {"model": "X", "elo": 1500}
    service.get_open_source_best.return_value = [{"model": "OS"}]
    with container.core.sota_benchmark_service.override(providers.Object(service)):
        # AllowAny -> no auth required
        response = api_client.get(reverse("api_sota_benchmarks"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["top_model"]["model"] == "X"
    assert body["best_open_source"]["model"] == "OS"


@pytest.mark.django_db
def test_sota_benchmarks_no_open_source(api_client):
    service = MagicMock()
    service.get_all_benchmarks.return_value = []
    service.get_best_model.return_value = None
    service.get_open_source_best.return_value = []
    with container.core.sota_benchmark_service.override(providers.Object(service)):
        response = api_client.get(reverse("api_sota_benchmarks"))

    assert response.status_code == 200
    assert response.json()["best_open_source"] is None


# --------------------------------------------------------------------------- #
# DPOFeedbackLoopView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_dpo_feedback_loop_get(admin_client):
    dpo_loop = MagicMock()
    dpo_loop.analyze_feedback_trends.return_value = {"trend": "up"}
    with container.core.dpo_feedback_loop.override(providers.Object(dpo_loop)):
        response = admin_client.get(reverse("api_dpo_feedback_loop"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["metrics"]["trend"] == "up"


@pytest.mark.django_db
def test_dpo_feedback_loop_export(admin_client):
    dpo_loop = MagicMock()
    with container.core.dpo_feedback_loop.override(providers.Object(dpo_loop)):
        response = admin_client.post(
            reverse("api_dpo_feedback_loop"), {"action": "export"}, format="json"
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    dpo_loop.export_preference_dataset.assert_called_once()


@pytest.mark.django_db
def test_dpo_feedback_loop_optimize_success(admin_client):
    dpo_loop = MagicMock()
    dpo_loop.optimize_prompt_from_feedback.return_value = "NEW PROMPT"
    with container.core.dpo_feedback_loop.override(providers.Object(dpo_loop)):
        response = admin_client.post(
            reverse("api_dpo_feedback_loop"),
            {"action": "optimize", "prompt_key": "rag_response"},
            format="json",
        )

    assert response.status_code == 200
    assert response.json()["new_system_prompt"] == "NEW PROMPT"


@pytest.mark.django_db
def test_dpo_feedback_loop_optimize_failure(admin_client):
    dpo_loop = MagicMock()
    dpo_loop.optimize_prompt_from_feedback.return_value = None
    with container.core.dpo_feedback_loop.override(providers.Object(dpo_loop)):
        response = admin_client.post(
            reverse("api_dpo_feedback_loop"), {"action": "optimize"}, format="json"
        )

    assert response.status_code == 400


@pytest.mark.django_db
def test_dpo_feedback_loop_invalid_action(admin_client):
    dpo_loop = MagicMock()
    with container.core.dpo_feedback_loop.override(providers.Object(dpo_loop)):
        response = admin_client.post(
            reverse("api_dpo_feedback_loop"), {"action": "bogus"}, format="json"
        )

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid action"


# --------------------------------------------------------------------------- #
# AdaptersView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_adapters_get_health(admin_client):
    engine = MagicMock()
    engine.health_check.return_value = {"ok": True}
    with (
        container.inference.inference_engine.override(providers.Object(engine)),
        container.inference.unified_inference_adapter.override(
            providers.Object(MagicMock())
        ),
    ):
        response = admin_client.get(reverse("api_mlops_adapters"))

    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "FallbackInferenceAdapter"
    assert body["health"] == {"ok": True}


@pytest.mark.django_db
def test_adapters_set_primary_success(admin_client):
    engine = MagicMock()
    engine.set_primary_adapter.return_value = True
    with (
        container.inference.inference_engine.override(providers.Object(engine)),
        container.inference.unified_inference_adapter.override(
            providers.Object(MagicMock())
        ),
    ):
        response = admin_client.post(
            reverse("api_mlops_adapters"),
            {"action": "set_primary", "index": 1},
            format="json",
        )

    assert response.status_code == 200
    assert "primary" in response.json()["message"]


@pytest.mark.django_db
def test_adapters_set_primary_invalid_index(admin_client):
    engine = MagicMock()
    engine.set_primary_adapter.return_value = False
    with (
        container.inference.inference_engine.override(providers.Object(engine)),
        container.inference.unified_inference_adapter.override(
            providers.Object(MagicMock())
        ),
    ):
        response = admin_client.post(
            reverse("api_mlops_adapters"),
            {"action": "set_primary", "index": 99},
            format="json",
        )

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid index"


@pytest.mark.django_db
def test_adapters_set_model_success(admin_client):
    engine = MagicMock()
    unified = MagicMock()
    with (
        container.inference.inference_engine.override(providers.Object(engine)),
        container.inference.unified_inference_adapter.override(
            providers.Object(unified)
        ),
    ):
        response = admin_client.post(
            reverse("api_mlops_adapters"),
            {"action": "set_model", "model_name": "llama3"},
            format="json",
        )

    assert response.status_code == 200
    unified.set_model_name.assert_called_once_with("llama3")


@pytest.mark.django_db
def test_adapters_set_model_missing_name(admin_client):
    engine = MagicMock()
    with (
        container.inference.inference_engine.override(providers.Object(engine)),
        container.inference.unified_inference_adapter.override(
            providers.Object(MagicMock())
        ),
    ):
        response = admin_client.post(
            reverse("api_mlops_adapters"),
            {"action": "set_model"},
            format="json",
        )

    assert response.status_code == 400
    assert response.json()["error"] == "model_name required"


@pytest.mark.django_db
def test_adapters_invalid_action(admin_client):
    engine = MagicMock()
    with (
        container.inference.inference_engine.override(providers.Object(engine)),
        container.inference.unified_inference_adapter.override(
            providers.Object(MagicMock())
        ),
    ):
        response = admin_client.post(
            reverse("api_mlops_adapters"), {"action": "nope"}, format="json"
        )

    assert response.status_code == 400
