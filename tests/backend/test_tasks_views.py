import pytest
import json
from django.urls import reverse
from rest_framework import status
from django.core.cache import cache
from animetix.tasks_registry import register_task

@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()

@pytest.mark.django_db
def test_worker_run_task_endpoint_local(client, settings):
    settings.IS_PRODUCTION = False
    
    @register_task("endpoint_test_task")
    def sum_task(a, b):
        return a + b
        
    url = "/api/tasks/run/"
    payload = {
        "task_id": "test-task-123",
        "task_name": "endpoint_test_task",
        "args": [15, 25],
        "kwargs": {}
    }
    
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Check cache status
    cached = cache.get("task_result:test-task-123")
    assert cached["ready"] is True
    assert cached["result"] == 40
    assert cached["state"] == "SUCCESS"
