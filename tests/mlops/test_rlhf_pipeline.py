# -*- coding: utf-8 -*-
"""Tests hermétiques de pipeline/mlops/rlhf_pipeline.py (32 % → reliquat audit
2026-07-19). Pas de réseau ni de subprocess réels : safe_http_request et
subprocess.run sont substitués.
"""

import os
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from pipeline.mlops import rlhf_pipeline  # noqa: E402

# --- monitor_inference_health -------------------------------------------------


def test_health_warns_when_brain_url_missing(monkeypatch):
    monkeypatch.delenv("BRAIN_API_URL", raising=False)
    assert "BRAIN_API_URL" in rlhf_pipeline.monitor_inference_health()


def test_health_online_appends_generate_and_reports_latency(monkeypatch):
    monkeypatch.setenv("BRAIN_API_URL", "http://brain.local")
    fake = MagicMock(return_value=MagicMock(status_code=200))
    monkeypatch.setattr(rlhf_pipeline, "safe_http_request", fake)

    out = rlhf_pipeline.monitor_inference_health()

    assert out["status"] == "🟢 Online"
    assert out["latency"] >= 0
    assert fake.call_args[0][1] == "http://brain.local/generate"


def test_health_error_status_and_offline(monkeypatch):
    monkeypatch.setenv("BRAIN_API_URL", "http://brain.local/generate")
    fake = MagicMock(return_value=MagicMock(status_code=503))
    monkeypatch.setattr(rlhf_pipeline, "safe_http_request", fake)
    out = rlhf_pipeline.monitor_inference_health()
    assert out["status"] == "🔴 Error 503"
    # L'URL déjà suffixée /generate ne doit pas être doublée.
    assert fake.call_args[0][1] == "http://brain.local/generate"

    monkeypatch.setattr(
        rlhf_pipeline,
        "safe_http_request",
        MagicMock(side_effect=ConnectionError("refused")),
    )
    out = rlhf_pipeline.monitor_inference_health()
    assert out["status"] == "🔴 Offline"
    assert "refused" in out["error"]


# --- exported_user_feedback ----------------------------------------------------


def test_export_returns_dataset_paths_on_success(monkeypatch):
    run = MagicMock()
    monkeypatch.setattr(subprocess, "run", run)

    out = rlhf_pipeline.exported_user_feedback()

    assert out["feedback"].endswith("ai_feedback.jsonl")
    assert out["sessions"].endswith("gameplay_sessions.jsonl")
    assert "export_rlhf_data" in run.call_args[0][0]


def test_export_returns_none_when_django_command_fails(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        MagicMock(side_effect=subprocess.CalledProcessError(1, "manage.py")),
    )
    assert rlhf_pipeline.exported_user_feedback() is None


# --- run_sql_quality_checks -----------------------------------------------------


def test_sql_checks_pass_and_offline_mode_excludes_bigquery(monkeypatch):
    run = MagicMock()
    monkeypatch.setattr(subprocess, "run", run)

    monkeypatch.setenv("MLOPS_OFFLINE_MODE", "false")
    assert rlhf_pipeline.run_sql_quality_checks() is True
    assert "--exclude-bigquery" not in run.call_args[0][0]

    monkeypatch.setenv("MLOPS_OFFLINE_MODE", "true")
    assert rlhf_pipeline.run_sql_quality_checks() is True
    assert "--exclude-bigquery" in run.call_args[0][0]


def test_sql_checks_failure_aborts_training(monkeypatch):
    err = subprocess.CalledProcessError(1, "dbt", stderr="not_null violated")
    monkeypatch.setattr(subprocess, "run", MagicMock(side_effect=err))

    with pytest.raises(RuntimeError, match="data quality"):
        rlhf_pipeline.run_sql_quality_checks()


# --- validated_dpo_dataset --------------------------------------------------------


def test_validated_dataset_none_passthrough():
    assert rlhf_pipeline.validated_dpo_dataset(None) is None


def test_validated_dataset_runs_checks_then_compiles(monkeypatch, tmp_path):
    checks = MagicMock(return_value=True)
    monkeypatch.setattr(rlhf_pipeline, "run_sql_quality_checks", checks)
    loop = MagicMock()
    loop.return_value.process_and_export.return_value = 42
    monkeypatch.setattr(rlhf_pipeline, "DPOFeedbackLoop", loop)

    out = rlhf_pipeline.validated_dpo_dataset({"feedback": str(tmp_path / "f.jsonl")})

    checks.assert_called_once()
    assert out["count"] == 42
    assert out["path"].endswith("dpo_train_validated.jsonl")


# --- trigger_model_retraining -------------------------------------------------------


@pytest.mark.parametrize(
    "count, faithfulness, drift, expected",
    [
        (150, 1.0, False, "Retraining started."),
        (10, 0.5, False, "Urgent retraining started."),
        (10, 0.9, True, "Preventative retraining started."),
        (10, 0.9, False, "Retraining not necessary yet."),
    ],
)
def test_retraining_trigger_criteria(count, faithfulness, drift, expected):
    out = rlhf_pipeline.trigger_model_retraining(
        {"count": count},
        {"avg_faithfulness": faithfulness},
        knowledge_drift_check=drift,
    )
    assert out == expected
