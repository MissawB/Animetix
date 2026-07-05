from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command

CMD = "generate_drift_baselines"
GC = "animetix.management.commands.generate_drift_baselines.get_container"


def _container(drift):
    container = MagicMock()
    container.core.drift_service.return_value = drift
    return container


@patch(GC)
def test_generates_baseline_for_all_collections(mock_gc):
    drift = MagicMock()
    drift.check_collection_drift.return_value = {
        "status": "healthy",
        "sample_size": 800,
    }
    mock_gc.return_value = _container(drift)

    out = StringIO()
    call_command(CMD, stdout=out)

    baselined = {c.args[0] for c in drift.generate_new_baseline.call_args_list}
    assert baselined == {"anime", "manga", "character"}
    assert "3 baseline(s) écrite(s)" in out.getvalue()


@patch(GC)
def test_limits_to_requested_collection(mock_gc):
    drift = MagicMock()
    drift.check_collection_drift.return_value = {"status": "healthy", "sample_size": 5}
    mock_gc.return_value = _container(drift)

    out = StringIO()
    call_command(CMD, "--collection", "anime", stdout=out)

    baselined = [c.args[0] for c in drift.generate_new_baseline.call_args_list]
    assert baselined == ["anime"]


@patch(GC)
def test_reports_empty_collection_without_writing(mock_gc):
    drift = MagicMock()
    # No embeddings → generate writes nothing, drift stays "unknown".
    drift.check_collection_drift.return_value = {"status": "unknown"}
    mock_gc.return_value = _container(drift)

    out = StringIO()
    call_command(CMD, "--collection", "manga", stdout=out)

    assert "aucun embedding" in out.getvalue()
    assert "0 baseline(s) écrite(s)" in out.getvalue()
