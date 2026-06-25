"""Unit + API tests for the ported Vertex AI Pipelines feature.

Ports the pipeline-slice tests from feature/vertex-pipelines, adapted to main:
client simulation, MlopsAdapter triggers, and the VertexPipelineView API
(auth + trigger/list via DI override). The sensor-task test is NOT ported —
main's pipeline_tasks sensor logic differs by design.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from adapters.infrastructure.vertex_pipelines_client import VertexPipelinesClient
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from pipeline.mlops.vertex_pipelines import dpo_retraining_pipeline


@pytest.fixture(autouse=True)
def _brain_api_url(monkeypatch):
    # For authenticated JSON responses, PersonalizationMiddleware builds the
    # inference chain (incl. BrainAPIAdapter, which now raises if BRAIN_API_URL
    # is unset). Set a dummy so construction succeeds; no real HTTP is performed.
    # Keeps these tests hermetic regardless of a local .env.
    monkeypatch.setenv("BRAIN_API_URL", "http://localhost:5000")


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


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="password"
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="user", password="password")


@pytest.fixture
def mock_mlops_port():
    port = MagicMock()
    port.trigger_dpo_pipeline.return_value = {
        "name": "projects/animetix/locations/europe-west1/pipelineJobs/mock-dpo",
        "display_name": "dpo-retraining",
        "state": "PIPELINE_STATE_RUNNING",
    }
    port.trigger_rag_pipeline.return_value = {
        "name": "projects/animetix/locations/europe-west1/pipelineJobs/mock-rag",
        "display_name": "rag-reindexing",
        "state": "PIPELINE_STATE_RUNNING",
    }
    port.list_pipeline_runs.return_value = [
        {
            "name": "projects/animetix/locations/europe-west1/pipelineJobs/mock-dpo",
            "display_name": "dpo-retraining",
            "state": "PIPELINE_STATE_SUCCEEDED",
        }
    ]
    return port


def test_vertex_pipelines_client_simulation():
    # Force simulation mode for testing
    with patch.dict(os.environ, {"VERTEX_AI_SIMULATION": "true"}):
        client = VertexPipelinesClient()
        assert client.simulation_mode is True

        run = client.submit_pipeline(
            pipeline_func=dpo_retraining_pipeline,
            pipeline_name="test-dpo-run",
            parameter_values={"min_samples": 50},
        )
        assert run["display_name"] == "test-dpo-run"
        assert run["state"] == "PIPELINE_STATE_RUNNING"
        assert run["parameter_values"] == {"min_samples": 50}

        run_status = client.get_pipeline_run(run["name"])
        assert run_status["name"] == run["name"]
        assert run_status["state"] == "PIPELINE_STATE_SUCCEEDED"

        runs = client.list_pipeline_runs(pipeline_name="test-dpo-run")
        assert len(runs) >= 1
        assert runs[0]["name"] == run["name"]


@pytest.mark.django_db
def test_mlops_adapter_triggers():
    with patch.dict(os.environ, {"VERTEX_AI_SIMULATION": "true"}):
        from adapters.mlops_adapter import MlopsAdapter

        adapter = MlopsAdapter()

        dpo_result = adapter.trigger_dpo_pipeline(min_samples=200)
        assert dpo_result["display_name"] == "dpo-retraining"
        assert dpo_result["parameter_values"] == {"min_samples": 200}

        rag_result = adapter.trigger_rag_pipeline()
        assert rag_result["display_name"] == "rag-reindexing"

        runs = adapter.list_pipeline_runs(limit=5)
        assert len(runs) >= 2


@pytest.mark.django_db
def test_vertex_pipeline_api_auth(client, regular_user):
    url = reverse("mlops-pipelines")

    # Unauthenticated
    response = client.post(url, {"pipeline_type": "dpo"})
    assert response.status_code in [401, 403]

    # Regular (non-admin) user forbidden to trigger
    client.force_login(regular_user)
    response = client.post(url, {"pipeline_type": "dpo"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_vertex_pipeline_api_trigger_and_list(client, admin_user, mock_mlops_port):
    client.force_login(admin_user)
    url = reverse("mlops-pipelines")

    with container.agentic.mlops_adapter_factory.override(
        providers.Object(mock_mlops_port)
    ):
        # POST DPO
        response = client.post(
            url,
            {"pipeline_type": "dpo", "min_samples": 150},
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["pipeline_run"]["display_name"] == "dpo-retraining"
        mock_mlops_port.trigger_dpo_pipeline.assert_called_once_with(min_samples=150)

        # POST RAG
        response = client.post(
            url, {"pipeline_type": "rag"}, content_type="application/json"
        )
        assert response.status_code == 201
        assert response.json()["pipeline_run"]["display_name"] == "rag-reindexing"
        mock_mlops_port.trigger_rag_pipeline.assert_called_once()

        # GET (list)
        response = client.get(url, {"pipeline_name": "dpo-retraining", "limit": 10})
        assert response.status_code == 200
        assert len(response.json()["runs"]) == 1
        assert response.json()["runs"][0]["state"] == "PIPELINE_STATE_SUCCEEDED"
        mock_mlops_port.list_pipeline_runs.assert_called_once_with(
            pipeline_name="dpo-retraining", limit=10
        )
