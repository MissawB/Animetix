"""Behavior tests for the Celery pipeline orchestration tasks.

The tasks are registered via ``@register_task`` (which returns the *plain*
function unchanged), so each is callable directly with no broker.

Their bodies ``import`` pipeline submodules lazily (``from characters import
ingest_characters``, ``from mlops import graph_healer``, ``import neo4j_sync``…).
Those submodules live under sys.path-injected dirs that are unavailable/heavy in
the test env, so we inject fake modules into ``sys.modules`` before calling the
task. Each step is a MagicMock — we then assert the orchestration wired the
right calls in the right order, and that a failing step is caught (logged) and
does NOT abort the remaining steps (every section is wrapped in try/except).
"""

import sys
import types
from unittest.mock import MagicMock

import pytest
from animetix.tasks import pipeline_tasks as pt


def _fake_module(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


@pytest.fixture
def inject_modules(monkeypatch):
    """Register fake modules in sys.modules for the duration of a test."""

    created = {}

    def _inject(specs):
        # specs: {module_name: {attr: mock, ...}}
        for name, attrs in specs.items():
            mod = _fake_module(name, **attrs)
            monkeypatch.setitem(sys.modules, name, mod)
            created[name] = mod
        return created

    return _inject


# --- run_daily_ingestion_workflow ---------------------------------------


def _ingestion_specs():
    """Build mocks for every submodule the ingestion workflow imports."""
    specs = {
        "characters": {
            "ingest_characters": MagicMock(),
            "refine_characters": MagicMock(),
            "filter_characters": MagicMock(),
            "train_vibe_characters": MagicMock(),
            "vectorize_characters": MagicMock(),
            "combat_data": MagicMock(),
            "vectorize_combat": MagicMock(),
        },
        "actors": {
            "ingest_actors": MagicMock(),
            "filter_actors": MagicMock(),
            "vectorize_actors": MagicMock(),
            "cross_media_mapping": MagicMock(),
        },
        "games": {
            "ingest_games": MagicMock(),
            "filter_games": MagicMock(),
            "vectorize_games": MagicMock(),
        },
        "anime": {
            "ingest_anime": MagicMock(),
            "reconcile_drift": MagicMock(),
            "filter_anime": MagicMock(),
            "fetch_themes": MagicMock(),
            "train_vibe_anime": MagicMock(),
            "vectorize_anime": MagicMock(),
        },
        "manga": {
            "ingest_manga": MagicMock(),
            "filter_manga": MagicMock(),
            "fetch_covers": MagicMock(),
            "train_vibe_manga": MagicMock(),
            "vectorize_manga": MagicMock(),
        },
        "advanced_scrapers": {"run_tripartite_enrichment": MagicMock()},
        "enrich_db_scraper": {"run_enrichment": MagicMock()},
        "expert_scrapers": {"run_tripartite_enrichment": MagicMock()},
        "specialized_scrapers": {"run_tripartite_enrichment": MagicMock()},
        "neo4j_sync": {"run_sync_type_to_graph": MagicMock()},
    }
    return specs


def test_ingestion_workflow_wires_all_steps(inject_modules):
    specs = _ingestion_specs()
    mods = inject_modules(specs)

    result = pt.run_daily_ingestion_workflow()

    assert result == "SUCCESS"

    chars = mods["characters"]
    chars.ingest_characters.run_ingestion.assert_called_once()
    chars.refine_characters.run_refinement.assert_called_once()
    chars.filter_characters.run_filtering.assert_called_once()
    chars.train_vibe_characters.run_training.assert_called_once()
    chars.vectorize_characters.run_vectorization.assert_called_once()
    # Combat ingestion uses an explicit limit.
    chars.combat_data.run_combat_data_ingestion.assert_called_once_with(limit=20)
    chars.vectorize_combat.run_combat_vectorization.assert_called_once()

    mods["actors"].cross_media_mapping.run_mapping.assert_called_once()
    mods["games"].vectorize_games.run_vectorization.assert_called_once()
    mods["anime"].fetch_themes.run_fetching.assert_called_once_with(limit=100)
    mods["manga"].fetch_covers.run_fetching.assert_called_once_with(limit=100)

    # Enrichment scrapers with their explicit limits.
    mods["enrich_db_scraper"].run_enrichment.assert_called_once_with(limit=10)
    mods["specialized_scrapers"].run_tripartite_enrichment.assert_called_once_with(
        limit=5
    )

    # Neo4j sync issued once per media type, in order.
    sync = mods["neo4j_sync"].run_sync_type_to_graph
    assert [c.args[0] for c in sync.call_args_list] == [
        "Anime",
        "Manga",
        "Character",
        "Game",
    ]


def test_ingestion_workflow_continues_after_section_failure(inject_modules):
    specs = _ingestion_specs()
    # Make the very first character step blow up.
    specs["characters"]["ingest_characters"].run_ingestion.side_effect = RuntimeError(
        "char boom"
    )
    mods = inject_modules(specs)

    result = pt.run_daily_ingestion_workflow()

    # Section error is caught; later sections still run; task still SUCCESS.
    assert result == "SUCCESS"
    mods["actors"].ingest_actors.run_ingestion.assert_called_once()
    mods["neo4j_sync"].run_sync_type_to_graph.assert_called()


# --- run_daily_maintenance_workflow -------------------------------------


def _maintenance_specs():
    return {
        "mlops": {
            "graph_healer": MagicMock(),
            "continuous_pretraining": MagicMock(),
            "finetuning_dataset": MagicMock(),
            "train_expert_model": MagicMock(),
            "latent_space_viz": MagicMock(),
            "distillation": MagicMock(),
            "evaluation_metrics": MagicMock(),
            "rlhf_pipeline": MagicMock(),
        },
        "evaluation": {
            "regression_benchmark": MagicMock(),
            "drift_detection": MagicMock(),
        },
    }


def test_maintenance_workflow_wires_all_steps(inject_modules):
    mods = inject_modules(_maintenance_specs())

    assert pt.run_daily_maintenance_workflow() == "SUCCESS"

    mlops = mods["mlops"]
    mlops.graph_healer.run_graph_healer.assert_called_once()
    mlops.continuous_pretraining.run_cpt.assert_called_once()
    mlops.finetuning_dataset.run_generate_instruction_dataset.assert_called_once()
    mlops.train_expert_model.run_expert_training.assert_called_once()
    mlops.latent_space_viz.run_visualization.assert_called_once()
    mlops.distillation.run_distillation.assert_called_once()
    mlops.evaluation_metrics.ragas_performance_comparison.assert_called_once()
    mlops.evaluation_metrics.legacy_retrieval_metrics.assert_called_once()
    mods["evaluation"].regression_benchmark.run_regression_test.assert_called_once()


def test_maintenance_workflow_continues_after_failure(inject_modules):
    specs = _maintenance_specs()
    specs["mlops"]["graph_healer"].run_graph_healer.side_effect = RuntimeError("boom")
    mods = inject_modules(specs)

    assert pt.run_daily_maintenance_workflow() == "SUCCESS"
    # The CPT step (next section) still ran despite the healer failure.
    mods["mlops"].continuous_pretraining.run_cpt.assert_called_once()


# --- run_hourly_monitoring_workflow -------------------------------------


def _monitoring_specs():
    return {
        "mlops": {"rlhf_pipeline": MagicMock()},
        "evaluation": {
            "drift_detection": MagicMock(),
            "regression_benchmark": MagicMock(),
        },
    }


def test_monitoring_workflow_runs_alert_and_monitors(inject_modules, mocker):
    mods = inject_modules(_monitoring_specs())

    # Patch the container + Django user model used by the alert section.
    admin = MagicMock(id=42, username="root")
    user_model = MagicMock()
    user_model.objects.filter.return_value.first.return_value = admin
    mocker.patch("django.contrib.auth.get_user_model", return_value=user_model)
    container = MagicMock()
    alert_service = container.core.alert_service.return_value
    mocker.patch("animetix.containers.get_container", return_value=container)

    assert pt.run_hourly_monitoring_workflow() == "SUCCESS"

    # Alert sent to the discovered superuser.
    alert_service.check_and_alert.assert_called_once_with(admin_user_id=42)
    mods["mlops"].rlhf_pipeline.monitor_inference_health.assert_called_once()
    mods["evaluation"].drift_detection.run_drift_detection.assert_called_once()
    mods["evaluation"].regression_benchmark.run_regression_test.assert_called_once()


def test_monitoring_workflow_warns_when_no_superuser(inject_modules, mocker):
    mods = inject_modules(_monitoring_specs())
    user_model = MagicMock()
    user_model.objects.filter.return_value.first.return_value = None
    mocker.patch("django.contrib.auth.get_user_model", return_value=user_model)
    container = MagicMock()
    mocker.patch("animetix.containers.get_container", return_value=container)

    assert pt.run_hourly_monitoring_workflow() == "SUCCESS"
    # No admin -> no alert dispatched, but monitoring continues.
    container.core.alert_service.return_value.check_and_alert.assert_not_called()
    mods["mlops"].rlhf_pipeline.monitor_inference_health.assert_called_once()


def test_monitoring_workflow_survives_alert_exception(inject_modules, mocker):
    mods = inject_modules(_monitoring_specs())
    mocker.patch(
        "animetix.containers.get_container", side_effect=RuntimeError("no container")
    )

    assert pt.run_hourly_monitoring_workflow() == "SUCCESS"
    # Alert section blew up but later monitoring sections still ran.
    mods["mlops"].rlhf_pipeline.monitor_inference_health.assert_called_once()


# --- check_gold_dataset_sensor_task -------------------------------------


def test_gold_sensor_triggers_when_threshold_met(mocker):
    gold = MagicMock()
    gold.objects.filter.return_value.count.return_value = 150
    mocker.patch.dict(
        sys.modules,
        {"animetix.models": _fake_module("animetix.models", GoldDatasetEntry=gold)},
    )
    cache = mocker.patch("django.core.cache.cache")
    cache.get.return_value = 0  # last_count
    enqueue = mocker.patch.object(pt, "enqueue_task")

    assert pt.check_gold_dataset_sensor_task() == "TRIGGERED"
    # New count persisted and training enqueued.
    cache.set.assert_called_once_with("auto_lora_last_count", 150)
    enqueue.assert_called_once_with("run_star_training_cycle_task")


def test_gold_sensor_no_trigger_below_threshold(mocker):
    gold = MagicMock()
    gold.objects.filter.return_value.count.return_value = 50
    mocker.patch.dict(
        sys.modules,
        {"animetix.models": _fake_module("animetix.models", GoldDatasetEntry=gold)},
    )
    cache = mocker.patch("django.core.cache.cache")
    cache.get.return_value = 0
    enqueue = mocker.patch.object(pt, "enqueue_task")

    assert pt.check_gold_dataset_sensor_task() == "NO_TRIGGER"
    cache.set.assert_not_called()
    enqueue.assert_not_called()


def test_gold_sensor_swallows_enqueue_error(mocker):
    gold = MagicMock()
    gold.objects.filter.return_value.count.return_value = 200
    mocker.patch.dict(
        sys.modules,
        {"animetix.models": _fake_module("animetix.models", GoldDatasetEntry=gold)},
    )
    cache = mocker.patch("django.core.cache.cache")
    cache.get.return_value = 0
    mocker.patch.object(pt, "enqueue_task", side_effect=RuntimeError("queue down"))

    # Trigger still returned; enqueue error is caught.
    assert pt.check_gold_dataset_sensor_task() == "TRIGGERED"


# --- check_dpo_feedback_sensor_task -------------------------------------


def test_dpo_sensor_triggers_and_calls_trl(mocker):
    feedback = MagicMock()
    feedback.objects.count.return_value = 120
    mocker.patch.dict(
        sys.modules,
        {"animetix.models": _fake_module("animetix.models", AIFeedback=feedback)},
    )
    cache = mocker.patch("django.core.cache.cache")
    cache.get.return_value = 0

    trl_ready = MagicMock(return_value="/tmp/dataset")
    trigger = MagicMock()
    mocker.patch.dict(
        sys.modules,
        {
            "pipeline.mlops.trl_ops": _fake_module(
                "pipeline.mlops.trl_ops",
                trl_ready_dataset=trl_ready,
                trigger_lora_training=trigger,
            )
        },
    )

    assert pt.check_dpo_feedback_sensor_task() == "TRIGGERED"
    cache.set.assert_called_once_with("auto_dpo_last_count", 120)
    trl_ready.assert_called_once_with(config=None)
    trigger.assert_called_once_with(dataset_path="/tmp/dataset")


def test_dpo_sensor_no_trigger(mocker):
    feedback = MagicMock()
    feedback.objects.count.return_value = 10
    mocker.patch.dict(
        sys.modules,
        {"animetix.models": _fake_module("animetix.models", AIFeedback=feedback)},
    )
    cache = mocker.patch("django.core.cache.cache")
    cache.get.return_value = 0
    assert pt.check_dpo_feedback_sensor_task() == "NO_TRIGGER"
    cache.set.assert_not_called()


def test_dpo_sensor_handles_count_error(mocker):
    feedback = MagicMock()
    feedback.objects.count.side_effect = RuntimeError("db down")
    mocker.patch.dict(
        sys.modules,
        {"animetix.models": _fake_module("animetix.models", AIFeedback=feedback)},
    )
    cache = mocker.patch("django.core.cache.cache")
    cache.get.return_value = 0
    # count() fails -> total_feedbacks falls back to 0 -> NO_TRIGGER.
    assert pt.check_dpo_feedback_sensor_task() == "NO_TRIGGER"


def test_dpo_sensor_swallows_training_error(mocker):
    feedback = MagicMock()
    feedback.objects.count.return_value = 500
    mocker.patch.dict(
        sys.modules,
        {"animetix.models": _fake_module("animetix.models", AIFeedback=feedback)},
    )
    cache = mocker.patch("django.core.cache.cache")
    cache.get.return_value = 0
    mocker.patch.dict(
        sys.modules,
        {
            "pipeline.mlops.trl_ops": _fake_module(
                "pipeline.mlops.trl_ops",
                trl_ready_dataset=MagicMock(side_effect=RuntimeError("trl boom")),
                trigger_lora_training=MagicMock(),
            )
        },
    )
    # Training error caught; still reports TRIGGERED.
    assert pt.check_dpo_feedback_sensor_task() == "TRIGGERED"
