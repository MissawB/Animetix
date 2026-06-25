"""Standalone unit tests for the ported Vertex AI Pipelines infrastructure.

Only the self-contained client/simulation tests are kept here. The end-to-end
integration tests from feature/vertex-pipelines (API routes, DI overrides,
sensor tasks) depend on the MlopsAdapter/container/URL wiring that is still
being re-integrated against main's current architecture — they will be restored
with that wiring batch.
"""

import os
from unittest.mock import patch

import pytest
from adapters.infrastructure.vertex_pipelines_client import VertexPipelinesClient
from pipeline.mlops.vertex_pipelines import dpo_retraining_pipeline


@pytest.fixture(autouse=True)
def cleanup_mock_runs():
    client = VertexPipelinesClient()
    mock_runs_path = client.mock_runs_path
    if os.path.exists(mock_runs_path):
        try:
            os.remove(mock_runs_path)
        except OSError:
            pass
    yield
    if os.path.exists(mock_runs_path):
        try:
            os.remove(mock_runs_path)
        except OSError:
            pass


def test_vertex_pipelines_client_simulation():
    # Force simulation mode for testing
    with patch.dict(os.environ, {"VERTEX_AI_SIMULATION": "true"}):
        client = VertexPipelinesClient()
        assert client.simulation_mode is True

        # Test submit_pipeline (compiles the real KFP pipeline, then mock-submits)
        run = client.submit_pipeline(
            pipeline_func=dpo_retraining_pipeline,
            pipeline_name="test-dpo-run",
            parameter_values={"min_samples": 50},
        )
        assert run["display_name"] == "test-dpo-run"
        assert run["state"] == "PIPELINE_STATE_RUNNING"
        assert run["parameter_values"] == {"min_samples": 50}

        # Test get_pipeline_run (transitions to completed state in mock)
        run_status = client.get_pipeline_run(run["name"])
        assert run_status["name"] == run["name"]
        assert run_status["state"] == "PIPELINE_STATE_SUCCEEDED"

        # Test list_pipeline_runs
        runs = client.list_pipeline_runs(pipeline_name="test-dpo-run")
        assert len(runs) >= 1
        assert runs[0]["name"] == run["name"]
