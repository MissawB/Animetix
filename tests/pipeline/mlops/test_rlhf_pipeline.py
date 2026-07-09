import os
import subprocess
from unittest.mock import MagicMock

import pipeline.mlops.rlhf_pipeline as rlhf
import pytest

# ---------------------------------------------------------------------------
# Unit tests (no integration marker): every external boundary mocked in the
# rlhf_pipeline module namespace. Real return values / branch outcomes asserted.
# ---------------------------------------------------------------------------


def _http_resp(status_code):
    r = MagicMock()
    r.status_code = status_code
    return r


# --- monitor_inference_health -------------------------------------------


def test_monitor_health_warns_when_url_unset(monkeypatch):
    monkeypatch.delenv("BRAIN_API_URL", raising=False)
    assert rlhf.monitor_inference_health() == "⚠️ BRAIN_API_URL non configuré."


def test_monitor_health_online_appends_generate_and_reports_latency(
    monkeypatch, mocker
):
    monkeypatch.setenv("BRAIN_API_URL", "http://brain.local")
    spy = mocker.patch.object(rlhf, "safe_http_request", return_value=_http_resp(200))

    result = rlhf.monitor_inference_health()

    assert result["status"] == "🟢 Online"
    assert isinstance(result["latency"], float) and result["latency"] >= 0
    # URL must get /generate suffix appended.
    assert spy.call_args.args[1] == "http://brain.local/generate"


def test_monitor_health_keeps_generate_suffix_when_present(monkeypatch, mocker):
    monkeypatch.setenv("BRAIN_API_URL", "http://brain.local/generate")
    spy = mocker.patch.object(rlhf, "safe_http_request", return_value=_http_resp(200))

    rlhf.monitor_inference_health()

    assert spy.call_args.args[1] == "http://brain.local/generate"


def test_monitor_health_reports_error_status_on_non_200(monkeypatch, mocker):
    monkeypatch.setenv("BRAIN_API_URL", "http://brain.local")
    mocker.patch.object(rlhf, "safe_http_request", return_value=_http_resp(503))

    result = rlhf.monitor_inference_health()

    assert result["status"] == "🔴 Error 503"
    assert "latency" in result


def test_monitor_health_offline_on_exception(monkeypatch, mocker):
    monkeypatch.setenv("BRAIN_API_URL", "http://brain.local")
    mocker.patch.object(
        rlhf, "safe_http_request", side_effect=RuntimeError("conn refused")
    )

    result = rlhf.monitor_inference_health()

    assert result == {"status": "🔴 Offline", "error": "conn refused"}


# --- exported_user_feedback ---------------------------------------------


def test_exported_user_feedback_returns_paths_on_success(mocker):
    run = mocker.patch("subprocess.run", return_value=MagicMock())

    result = rlhf.exported_user_feedback()

    run.assert_called_once()
    assert result["feedback"].endswith(os.path.join("datasets", "ai_feedback.jsonl"))
    assert result["sessions"].endswith(
        os.path.join("datasets", "gameplay_sessions.jsonl")
    )


def test_exported_user_feedback_returns_none_on_subprocess_error(mocker):
    mocker.patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "manage.py"),
    )

    assert rlhf.exported_user_feedback() is None


# --- run_sql_quality_checks ---------------------------------------------


def test_run_sql_quality_checks_returns_true_on_success(mocker):
    run = mocker.patch("subprocess.run", return_value=MagicMock())

    assert rlhf.run_sql_quality_checks() is True
    run.assert_called_once()


def test_run_sql_quality_checks_offline_mode_excludes_bigquery(monkeypatch, mocker):
    monkeypatch.setenv("MLOPS_OFFLINE_MODE", "true")
    run = mocker.patch("subprocess.run", return_value=MagicMock())

    rlhf.run_sql_quality_checks()

    cmd = run.call_args.args[0]
    assert "--exclude-bigquery" in cmd


def test_run_sql_quality_checks_default_keeps_bigquery(monkeypatch, mocker):
    monkeypatch.setenv("MLOPS_OFFLINE_MODE", "false")
    run = mocker.patch("subprocess.run", return_value=MagicMock())

    rlhf.run_sql_quality_checks()

    cmd = run.call_args.args[0]
    assert "--exclude-bigquery" not in cmd


def test_run_sql_quality_checks_raises_runtime_error_on_failure(mocker):
    err = subprocess.CalledProcessError(1, "manage.py")
    err.stderr = "dbt assertion failed"
    err.stdout = ""
    mocker.patch("subprocess.run", side_effect=err)

    with pytest.raises(RuntimeError, match="data quality violations"):
        rlhf.run_sql_quality_checks()


# --- validated_dpo_dataset ----------------------------------------------


def test_validated_dpo_dataset_returns_none_on_empty_input():
    assert rlhf.validated_dpo_dataset(None) is None
    assert rlhf.validated_dpo_dataset({}) is None


def test_validated_dpo_dataset_runs_checks_then_compiles(mocker):
    checks = mocker.patch.object(rlhf, "run_sql_quality_checks")
    loop_cls = mocker.patch.object(rlhf, "DPOFeedbackLoop")
    loop_cls.return_value.process_and_export.return_value = 7

    result = rlhf.validated_dpo_dataset(
        {"feedback": "/tmp/fb.jsonl", "sessions": "/tmp/s.jsonl"}
    )

    checks.assert_called_once()
    assert result["count"] == 7
    assert result["path"].endswith(
        os.path.join("datasets", "dpo_train_validated.jsonl")
    )
    # The feedback path is forwarded verbatim to the loop.
    assert loop_cls.return_value.process_and_export.call_args.args[0] == "/tmp/fb.jsonl"


def test_validated_dpo_dataset_propagates_quality_failure(mocker):
    mocker.patch.object(
        rlhf, "run_sql_quality_checks", side_effect=RuntimeError("aborted")
    )
    loop_cls = mocker.patch.object(rlhf, "DPOFeedbackLoop")

    with pytest.raises(RuntimeError, match="aborted"):
        rlhf.validated_dpo_dataset({"feedback": "/tmp/fb.jsonl"})

    # Compilation must NOT happen if quality checks raised.
    loop_cls.return_value.process_and_export.assert_not_called()


# --- periodic_rag_evaluation --------------------------------------------


def test_periodic_rag_evaluation_returns_report(mocker):
    import sys
    import types

    fake_mod = types.ModuleType("scripts.mlops_rag_eval")
    fake_mod.run_mlops_eval = lambda: {"avg_faithfulness": 0.92}
    mocker.patch.dict(sys.modules, {"scripts.mlops_rag_eval": fake_mod})

    assert rlhf.periodic_rag_evaluation() == {"avg_faithfulness": 0.92}


# --- trigger_model_retraining -------------------------------------------


def test_trigger_retraining_on_sufficient_volume():
    result = rlhf.trigger_model_retraining({"count": 150}, {"avg_faithfulness": 0.99})
    assert result == "Retraining started."


def test_trigger_retraining_urgent_on_faithfulness_drop():
    result = rlhf.trigger_model_retraining({"count": 5}, {"avg_faithfulness": 0.5})
    assert result == "Urgent retraining started."


def test_trigger_retraining_preventative_on_drift():
    result = rlhf.trigger_model_retraining(
        {"count": 5}, {"avg_faithfulness": 0.99}, knowledge_drift_check=True
    )
    assert result == "Preventative retraining started."


def test_trigger_retraining_not_necessary():
    result = rlhf.trigger_model_retraining({"count": 5}, {"avg_faithfulness": 0.99})
    assert result == "Retraining not necessary yet."


def test_trigger_retraining_volume_takes_priority_over_drop():
    # count >= 100 must short-circuit before the faithfulness branch.
    result = rlhf.trigger_model_retraining(
        {"count": 100}, {"avg_faithfulness": 0.1}, knowledge_drift_check=True
    )
    assert result == "Retraining started."


def test_trigger_retraining_defaults_when_keys_absent():
    # Missing count -> 0, missing avg_faithfulness -> 1.0 (no trigger).
    result = rlhf.trigger_model_retraining({}, {})
    assert result == "Retraining not necessary yet."
