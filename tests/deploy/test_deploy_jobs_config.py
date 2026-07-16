"""The Cloud Run Jobs config (``deploy/deployments.yaml`` ->
``gcp_services.jobs.items``) is consumed by ``scripts/deploy/gcp/deploy_jobs.py``,
which indexes ``job['name']``, ``job['args']``, ``job['memory']`` and
``job['cpu']`` (and ``job.get('timeout'/'schedule')``). A job missing a required
key raises ``KeyError`` at deploy time — in prod. Pin the contract here so a
malformed entry fails in CI instead.
"""

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _jobs():
    data = yaml.safe_load(
        (ROOT / "deploy" / "deployments.yaml").read_text(encoding="utf-8")
    )
    return data["gcp_services"]["jobs"]["items"]


def test_every_job_has_the_keys_deploy_jobs_indexes():
    for job in _jobs():
        for key in ("name", "args", "memory", "cpu"):
            assert key in job, f"job {job.get('name')!r} missing required key {key!r}"
        # deploy_jobs runs `--command=python --args=<args>`, so the first arg
        # must be the manage.py entrypoint.
        assert job["args"].split(",")[0].endswith("manage.py"), job["args"]


def test_character_index_build_is_wired_on_demand():
    job = next(
        (j for j in _jobs() if j["name"] == "animetix-build-character-index"), None
    )
    assert job is not None, "character index build job is not defined"
    assert job["args"] == "backend/api/manage.py,build_visual_index,--target,character"
    # A ~35k-portrait one-shot backfill must be on-demand, never scheduled.
    assert job["schedule"] == ""
