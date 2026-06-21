"""Coverage for animetix.tasks_views — Cloud Tasks / Workflow / Eventarc endpoints.

These are plain ``csrf_exempt`` Django views (not DRF). They are exercised
through the Django test ``Client`` via ``reverse()``. Every external collaborator
is mocked:

  * ``run_task_view``        -> registered task funcs (via tasks_registry), cache
  * ``poll_workflow_view``   -> GCPWorkflowsClient, cache
  * ``eventarc_gcs_upload_view`` -> enqueue_task, cache

Production-only OIDC branches are reached with ``override_settings`` flipping
``IS_PRODUCTION`` and the relevant audience URLs, while
``google.oauth2.id_token.verify_oauth2_token`` is patched to accept/reject.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from animetix import tasks_views as tv
from django.core.cache import cache
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def rf():
    return RequestFactory()


def _post_run_task(rf, payload=None, raw=None, **extra):
    """Drive ``run_task_view`` directly.

    The project routes ``/api/tasks/run/`` to a RedirectView *before* the real
    view in ``urls.py``, so dispatching through the URL resolver yields a 302.
    We therefore call the view function directly with a RequestFactory request.
    """
    body = raw if raw is not None else json.dumps(payload or {})
    request = rf.post(
        "/api/tasks/run/", data=body, content_type="application/json", **extra
    )
    return tv.run_task_view(request)


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


# --------------------------------------------------------------------------- #
# run_task_view
# --------------------------------------------------------------------------- #
def _body(response):
    return json.loads(response.content)


@pytest.mark.django_db
def test_run_task_method_not_allowed(rf):
    response = tv.run_task_view(rf.get("/api/tasks/run/"))
    assert response.status_code == 405
    assert _body(response)["error"] == "Method not allowed"


@pytest.mark.django_db
def test_run_task_invalid_json(rf):
    response = _post_run_task(rf, raw="not-json")
    assert response.status_code == 400
    assert _body(response)["error"] == "Invalid JSON payload"


@pytest.mark.django_db
def test_run_task_missing_fields(rf):
    response = _post_run_task(rf, {"task_id": "abc"})
    assert response.status_code == 400
    assert "required" in _body(response)["error"]


@pytest.mark.django_db
def test_run_task_unregistered(rf):
    response = _post_run_task(rf, {"task_id": "id1", "task_name": "does_not_exist"})
    assert response.status_code == 400
    assert "not registered" in _body(response)["error"]
    # Failure result is persisted in the cache for later polling.
    cached = cache.get("task_result:id1")
    assert cached["state"] == "FAILURE"
    assert "not registered" in cached["result"]["error"]


@pytest.mark.django_db
def test_run_task_success(rf):
    task = MagicMock(return_value={"ok": 42})
    with patch.object(tv, "get_registered_task", return_value=task):
        response = _post_run_task(
            rf,
            {
                "task_id": "id2",
                "task_name": "my_task",
                "args": [1, 2],
                "kwargs": {"x": "y"},
            },
        )

    assert response.status_code == 200
    assert _body(response) == {"status": "success", "task_id": "id2"}
    task.assert_called_once_with(1, 2, x="y")
    cached = cache.get("task_result:id2")
    assert cached["state"] == "SUCCESS"
    assert cached["result"] == {"ok": 42}


@pytest.mark.django_db
def test_run_task_execution_error(rf):
    task = MagicMock(side_effect=RuntimeError("boom"))
    with patch.object(tv, "get_registered_task", return_value=task):
        response = _post_run_task(rf, {"task_id": "id3", "task_name": "my_task"})

    # 500 so Cloud Tasks retries.
    assert response.status_code == 500
    assert _body(response)["error"] == "boom"
    cached = cache.get("task_result:id3")
    assert cached["state"] == "FAILURE"
    assert cached["result"]["error"] == "boom"


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, GCP_TASKS_WORKER_URL="https://worker")
def test_run_task_prod_missing_auth(rf):
    response = _post_run_task(rf, {"task_id": "id", "task_name": "t"})
    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, GCP_TASKS_WORKER_URL="https://worker")
def test_run_task_prod_bad_token(rf):
    with patch(
        "google.oauth2.id_token.verify_oauth2_token",
        side_effect=ValueError("bad token"),
    ):
        response = _post_run_task(
            rf,
            {"task_id": "id", "task_name": "t"},
            HTTP_AUTHORIZATION="Bearer faketoken",
        )
    assert response.status_code == 403
    assert _body(response)["error"] == "Invalid OIDC token"


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, GCP_TASKS_WORKER_URL="https://worker")
def test_run_task_prod_valid_token(rf):
    task = MagicMock(return_value={"done": True})
    with (
        patch(
            "google.oauth2.id_token.verify_oauth2_token", return_value={"sub": "svc"}
        ),
        patch.object(tv, "get_registered_task", return_value=task),
    ):
        response = _post_run_task(
            rf,
            {"task_id": "p1", "task_name": "t"},
            HTTP_AUTHORIZATION="Bearer goodtoken",
        )
    assert response.status_code == 200
    assert cache.get("task_result:p1")["state"] == "SUCCESS"


# --------------------------------------------------------------------------- #
# poll_workflow_view
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_poll_workflow_method_not_allowed(client):
    response = client.get(reverse("poll-workflow"))
    assert response.status_code == 405


@pytest.mark.django_db
def test_poll_workflow_invalid_json(client):
    response = client.post(
        reverse("poll-workflow"), data="{bad", content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid payload"


@pytest.mark.django_db
def test_poll_workflow_missing_fields(client):
    response = client.post(
        reverse("poll-workflow"),
        data=json.dumps({"task_id": "t"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Missing" in response.json()["error"]


@pytest.mark.django_db
def test_poll_workflow_active(client):
    wf = MagicMock()
    wf.get_execution_status.return_value = {"state": "ACTIVE"}
    with patch.object(tv, "GCPWorkflowsClient", return_value=wf):
        response = client.post(
            reverse("poll-workflow"),
            data=json.dumps({"execution_name": "exec/1", "task_id": "t1"}),
            content_type="application/json",
        )
    # 503 makes Cloud Tasks retry.
    assert response.status_code == 503
    wf.get_execution_status.assert_called_once_with("exec/1")


@pytest.mark.django_db
def test_poll_workflow_succeeded(client):
    wf = MagicMock()
    wf.get_execution_status.return_value = {
        "state": "SUCCEEDED",
        "result": {"translated_text": "hola", "audio_url": "http://a"},
    }
    with patch.object(tv, "GCPWorkflowsClient", return_value=wf):
        response = client.post(
            reverse("poll-workflow"),
            data=json.dumps({"execution_name": "exec/2", "task_id": "t2"}),
            content_type="application/json",
        )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    cached = cache.get("task_result:t2")
    assert cached["status"] == "success"
    assert cached["result"]["translated_text"] == "hola"
    assert cached["result"]["audio_url"] == "http://a"


@pytest.mark.django_db
def test_poll_workflow_failed(client):
    wf = MagicMock()
    wf.get_execution_status.return_value = {"state": "FAILED", "error": "nope"}
    with patch.object(tv, "GCPWorkflowsClient", return_value=wf):
        response = client.post(
            reverse("poll-workflow"),
            data=json.dumps({"execution_name": "exec/3", "task_id": "t3"}),
            content_type="application/json",
        )
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    cached = cache.get("task_result:t3")
    assert cached["status"] == "failed"
    assert cached["error"] == "nope"


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, GCP_WORKFLOW_POLL_URL="https://poll")
def test_poll_workflow_prod_missing_auth(client):
    response = client.post(
        reverse("poll-workflow"),
        data=json.dumps({"execution_name": "e", "task_id": "t"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, GCP_WORKFLOW_POLL_URL="https://poll")
def test_poll_workflow_prod_bad_token(client):
    with patch(
        "animetix.tasks_views.id_token.verify_oauth2_token",
        side_effect=ValueError("bad"),
    ):
        response = client.post(
            reverse("poll-workflow"),
            data=json.dumps({"execution_name": "e", "task_id": "t"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer x",
        )
    assert response.status_code == 403
    assert response.json()["error"] == "Forbidden"


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, GCP_WORKFLOW_POLL_URL="https://poll")
def test_poll_workflow_prod_valid_token(client):
    wf = MagicMock()
    wf.get_execution_status.return_value = {"state": "ACTIVE"}
    with (
        patch("animetix.tasks_views.id_token.verify_oauth2_token", return_value={}),
        patch.object(tv, "GCPWorkflowsClient", return_value=wf),
    ):
        response = client.post(
            reverse("poll-workflow"),
            data=json.dumps({"execution_name": "e", "task_id": "t"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer good",
        )
    assert response.status_code == 503


# --------------------------------------------------------------------------- #
# eventarc_gcs_upload_view
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_eventarc_method_not_allowed(client):
    response = client.get(reverse("eventarc-gcs-upload"))
    assert response.status_code == 405


@pytest.mark.django_db
def test_eventarc_invalid_json(client):
    response = client.post(
        reverse("eventarc-gcs-upload"), data="{bad", content_type="application/json"
    )
    assert response.status_code == 400
    assert "Invalid JSON body" in response.json()["error"]


@pytest.mark.django_db
def test_eventarc_missing_fields(client):
    response = client.post(
        reverse("eventarc-gcs-upload"),
        data=json.dumps({"bucket": "b"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Missing bucket or name" in response.json()["error"]


@pytest.mark.django_db
def test_eventarc_non_manga_no_enqueue(client):
    with patch.object(tv, "enqueue_task") as enqueue:
        response = client.post(
            reverse("eventarc-gcs-upload"),
            data=json.dumps({"bucket": "b", "name": "docs/readme.txt"}),
            content_type="application/json",
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "event processed"
    assert body["bucket"] == "b"
    enqueue.assert_not_called()


@pytest.mark.django_db
def test_eventarc_manga_enqueues(client):
    with patch.object(tv, "enqueue_task") as enqueue:
        response = client.post(
            reverse("eventarc-gcs-upload"),
            data=json.dumps({"bucket": "b", "name": "raw-manga/page1.PNG"}),
            content_type="application/json",
        )
    assert response.status_code == 200
    assert response.json()["status"] == "event processed"
    enqueue.assert_called_once_with(
        "process_gcs_upload_task", bucket="b", name="raw-manga/page1.PNG"
    )


@pytest.mark.django_db
def test_eventarc_manga_enqueue_failure(client):
    with patch.object(tv, "enqueue_task", side_effect=RuntimeError("queue down")):
        response = client.post(
            reverse("eventarc-gcs-upload"),
            data=json.dumps({"bucket": "b", "name": "manga/p.jpeg"}),
            content_type="application/json",
        )
    assert response.status_code == 500
    assert "Failed to enqueue task" in response.json()["error"]


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, EVENTARC_RECEIVER_URL="https://recv")
def test_eventarc_prod_missing_auth(client):
    response = client.post(
        reverse("eventarc-gcs-upload"),
        data=json.dumps({"bucket": "b", "name": "n"}),
        content_type="application/json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, EVENTARC_RECEIVER_URL="https://recv")
def test_eventarc_prod_bad_token(client):
    with patch(
        "animetix.tasks_views.id_token.verify_oauth2_token",
        side_effect=ValueError("bad"),
    ):
        response = client.post(
            reverse("eventarc-gcs-upload"),
            data=json.dumps({"bucket": "b", "name": "n"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer x",
        )
    assert response.status_code == 403
    assert response.json()["error"] == "Invalid OIDC token"


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True, EVENTARC_RECEIVER_URL="https://recv")
def test_eventarc_prod_valid_token(client):
    with (
        patch("animetix.tasks_views.id_token.verify_oauth2_token", return_value={}),
        patch.object(tv, "enqueue_task") as enqueue,
    ):
        response = client.post(
            reverse("eventarc-gcs-upload"),
            data=json.dumps({"bucket": "b", "name": "manga/p.webp"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer good",
        )
    assert response.status_code == 200
    enqueue.assert_called_once()
