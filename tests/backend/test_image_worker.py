from unittest.mock import MagicMock

import pytest
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from animetix.tasks import self_hosted_image_generation_task
from core.domain.services.health_dashboard_service import HealthDashboardService
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


def test_self_hosted_image_generation_task(mocker):
    # Mock container and diffusers_adapter
    mock_container = MagicMock()
    mock_adapter = MagicMock()
    mock_adapter.generate_image.return_value = "data:image/jpeg;base64,mocked"
    mock_container.inference.diffusers_adapter.return_value = mock_adapter

    mocker.patch("animetix.tasks.get_container", return_value=mock_container)

    # Set queue length initially
    cache.set("self_hosted_image_worker:queue_length", 1)

    res = self_hosted_image_generation_task("test prompt", style="Cyberpunk")

    assert res == "data:image/jpeg;base64,mocked"
    mock_adapter.generate_image.assert_called_once_with(
        "test prompt", style="Cyberpunk"
    )

    # Check cache cleanup
    assert cache.get("self_hosted_image_worker:active_task") is None
    assert cache.get("self_hosted_image_worker:queue_length") == 0
    assert cache.get("self_hosted_image_worker:status") == "idle"


def test_fallback_adapter_budget_exceeded(mocker):
    # Simuler budget dépassé
    cache.set("paid_api_budget_exceeded", True)

    # Mock enqueue_task
    task_id = "test-task-123"
    mocker.patch("animetix.tasks_client.enqueue_task", return_value=task_id)

    # Simuler le résultat de la tâche dans le cache
    cache.set(
        f"task_result:{task_id}",
        {
            "ready": True,
            "state": "SUCCESS",
            "result": "data:image/jpeg;base64,worker_success",
        },
    )

    fallback_adapter = FallbackInferenceAdapter(adapters=[], obs_service=None)

    res = fallback_adapter.generate_image("test prompt", style="Anime")

    assert res == "data:image/jpeg;base64,worker_success"
    # Because we mocked enqueue_task, the actual task execution did not run to decrement, so queue_length remains 1
    assert cache.get("self_hosted_image_worker:queue_length") == 1


def test_fallback_adapter_failover_on_error(mocker):
    # Budget non dépassé
    cache.set("paid_api_budget_exceeded", False)

    # Mock de _fallback_call pour lever une erreur sur paid API
    fallback_adapter = FallbackInferenceAdapter(adapters=[], obs_service=None)
    mocker.patch.object(
        fallback_adapter, "_fallback_call", side_effect=Exception("Paid API Timeout")
    )

    # Mock enqueue_task
    task_id = "test-task-456"
    mocker.patch("animetix.tasks_client.enqueue_task", return_value=task_id)

    # Simuler le résultat de la tâche dans le cache
    cache.set(
        f"task_result:{task_id}",
        {
            "ready": True,
            "state": "SUCCESS",
            "result": "data:image/jpeg;base64,worker_failover",
        },
    )

    res = fallback_adapter.generate_image("test prompt", style="Anime")

    assert res == "data:image/jpeg;base64,worker_failover"
    assert cache.get("paid_api_failover_active") is True


def test_health_dashboard_service_with_worker():
    # Setup cache
    cache.set("self_hosted_image_worker:status", "active")
    cache.set("self_hosted_image_worker:queue_length", 3)
    cache.set("self_hosted_image_worker:active_task", "generer un robot")
    cache.set("paid_api_budget_exceeded", True)

    usage_port = MagicMock()
    usage_port.get_total_cost.return_value = 100.0

    health_service = HealthDashboardService(usage_port=usage_port)

    # Mock sub-checks to avoid database/external calls in simple unit test
    health_service._check_gpu_cluster = MagicMock(
        return_value={"status": "online", "type": "gpu"}
    )
    health_service._check_inference_engine = MagicMock(
        return_value={"status": "online", "type": "inference"}
    )
    health_service._check_graph_database = MagicMock(
        return_value={"status": "online", "type": "graph_db"}
    )

    health_data = health_service.get_cluster_health()

    # Verify that the worker node is present and has the correct fields
    worker_nodes = [n for n in health_data["nodes"] if n["type"] == "worker"]
    assert len(worker_nodes) == 1
    worker_node = worker_nodes[0]

    assert worker_node["id"] == "self-hosted-image-worker"
    assert worker_node["status"] == "online"
    assert worker_node["details"]["worker_status"] == "active"
    assert worker_node["details"]["queue_length"] == 3
    assert worker_node["details"]["active_task"] == "generer un robot"
    assert worker_node["details"]["fallback_mode"] == "active"
