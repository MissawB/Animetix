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
