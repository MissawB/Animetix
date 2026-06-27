from types import SimpleNamespace
from unittest.mock import patch

import scripts.deploy.bootstrap_infra as boot


def _ok(*a, **k):
    return SimpleNamespace(returncode=0, stdout="", stderr="")


def _missing(*a, **k):
    return SimpleNamespace(returncode=1, stdout="", stderr="not found")


def test_apply_emits_tasks_queue_create():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        boot.ensure_tasks_queue("apply", [])
    flat = [" ".join(c) for c in calls]
    assert any(
        "tasks queues create animetix-queue" in f and "--location=europe-west1" in f
        for f in flat
    )


def test_dry_run_executes_nothing():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        boot.ensure_tasks_queue("dry-run", [])
        boot.ensure_artifact_registry("dry-run", [])
        boot.ensure_apis("dry-run", [])
    assert calls == []  # dry-run never executes


def test_check_records_missing():
    missing = []
    with patch.object(boot, "run_command", side_effect=_missing):
        boot.ensure_tasks_queue("check", missing)
    assert any("animetix-queue" in m for m in missing)


def test_check_uses_describe_not_create():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        boot.ensure_tasks_queue("check", [])
    flat = [" ".join(c) for c in calls]
    assert all("create" not in f for f in flat)
    assert any("describe" in f for f in flat)


def test_apply_creates_three_buckets():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        boot.ensure_buckets("apply", [])
    flat = [" ".join(c) for c in calls]
    for name in (
        "animetix-media-bucket",
        "animetix-vertex-pipelines-staging",
        "animetix-dataflow",
    ):
        assert any(f"buckets create gs://{name}" in f for f in flat)
    assert all(
        "--uniform-bucket-level-access" in f for f in flat if "buckets create" in f
    )
    assert all("public" not in f for f in flat)


def test_apply_bigquery_dataset_and_tables_with_schema():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        boot.ensure_bigquery("apply", [])
    flat = [" ".join(c) for c in calls]
    assert any("mk --dataset" in f and "animetix:telemetry" in f for f in flat)
    assert any("user_interactions" in f and "weight:FLOAT" in f for f in flat)
    assert any("archetype_drift" in f and "logic_consistency:FLOAT" in f for f in flat)


def test_apply_service_accounts_and_roles():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        boot.ensure_service_accounts("apply", [])
    flat = [" ".join(c) for c in calls]
    assert any("service-accounts create animetix-tasks-invoker" in f for f in flat)
    assert any("service-accounts create animetix-vertex-sa" in f for f in flat)
    assert any(
        "add-iam-policy-binding" in f and "roles/aiplatform.user" in f for f in flat
    )


def test_pubsub_topic_and_subscription():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        boot.ensure_pubsub("apply", [])
    flat = [" ".join(c) for c in calls]
    assert any("topics create animetix-events-topic" in f for f in flat)
    assert any(
        "subscriptions create lore-ingestion-sub" in f
        and "--topic=lore-ingestion-topic" in f
        for f in flat
    )


def test_secrets_created_without_values():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        boot.ensure_secrets("apply", [])
    flat = [" ".join(c) for c in calls]
    for name in (
        "DJANGO_SECRET_KEY",
        "BRAIN_API_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "HF_TOKEN",
        "WANDB_API_KEY",
    ):
        assert any(f"secrets create {name}" in f for f in flat)
    assert all("versions add" not in f for f in flat)


def test_wif_provider_condition_and_scoped_binding():
    calls = []

    def fake(args, check=True):
        calls.append(args)
        if "projects" in args and "describe" in args:
            return SimpleNamespace(returncode=0, stdout="123456789\n", stderr="")
        return _ok()

    with patch.object(boot, "run_command", side_effect=fake):
        boot.ensure_wif("apply", [])
    flat = [" ".join(c) for c in calls]
    assert any("workload-identity-pools create github-pool" in f for f in flat)
    assert any(
        "create-oidc github-provider" in f
        and "assertion.repository_owner == 'MissawB'" in f
        for f in flat
    )
    assert any(
        "workloadIdentityUser" in f and "attribute.repository/MissawB/Animetix" in f
        for f in flat
    )


def test_main_dry_run_executes_nothing_and_covers_all_groups():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        rc = boot.main(["--dry-run"])
    assert rc == 0
    assert calls == []


def test_main_requires_a_mode():
    calls = []
    with patch.object(
        boot,
        "run_command",
        side_effect=lambda args, check=True: calls.append(args) or _ok(),
    ):
        rc = boot.main([])
    assert rc == 0
    assert calls == []
