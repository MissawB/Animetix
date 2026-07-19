"""PipelineControlView — the staff-only Beam trigger.

Audit dette 2026-07-19: ``run_beam_ingestion`` used to pass ``DATABASE_URL``
(credentials included) as a ``--database_url=...`` argv element of the spawned
subprocess — argv is world-readable via ``ps``/``/proc``. It must travel
through the child's environment instead (the Beam DoFns already fall back to
``os.environ`` when the CLI flag is absent).
"""

import pytest
from django.urls import reverse

SECRET_DB_URL = "postgres://animetix:s3cr3t-pw@db.example.com:5432/animetix"


@pytest.fixture
def staff_client(client, django_user_model):
    user = django_user_model.objects.create_user(
        "pipestaff", password="x", is_staff=True
    )
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_run_beam_ingestion_keeps_database_url_out_of_argv(
    staff_client, mocker, settings
):
    settings.DATABASE_URL = SECRET_DB_URL
    popen = mocker.patch("subprocess.Popen")

    resp = staff_client.post(
        reverse("api_pipeline_control", args=["run_beam_ingestion"])
    )

    assert resp.status_code == 200
    cmd = popen.call_args[0][0]
    assert not any("database_url" in part for part in cmd)
    assert not any("s3cr3t-pw" in part for part in cmd)


@pytest.mark.django_db
def test_run_beam_ingestion_passes_database_url_via_child_env(
    staff_client, mocker, settings
):
    settings.DATABASE_URL = SECRET_DB_URL
    popen = mocker.patch("subprocess.Popen")

    resp = staff_client.post(
        reverse("api_pipeline_control", args=["run_beam_ingestion"])
    )

    assert resp.status_code == 200
    env = popen.call_args[1]["env"]
    assert env["DATABASE_URL"] == SECRET_DB_URL
    # The child still needs the parent's environment (PATH, DJANGO_*, ...).
    assert "PATH" in env
