import pathlib

import yaml

MANIFEST = (
    pathlib.Path(__file__).resolve().parents[2] / "deploy" / "run-brain.service.yaml"
)


def _load():
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_exists_and_is_a_cloud_run_service():
    doc = _load()
    assert doc["kind"] == "Service"
    assert doc["metadata"]["name"] == "animetix-brain"


def test_manifest_scales_to_zero():
    ann = _load()["spec"]["template"]["metadata"]["annotations"]
    # The scale-to-zero guarantee: no warm GPU billed at idle.
    assert ann["autoscaling.knative.dev/minScale"] == "0"
    # Ceiling aligned with restore_brain_service default (Task 3).
    assert ann["autoscaling.knative.dev/maxScale"] == "3"


def test_manifest_pins_l4_gpu_and_port():
    tspec = _load()["spec"]["template"]["spec"]
    assert tspec["nodeSelector"]["run.googleapis.com/accelerator"] == "nvidia-l4"
    container = tspec["containers"][0]
    assert container["resources"]["limits"]["nvidia.com/gpu"] == "1"
    assert container["ports"][0]["containerPort"] == 7861


def test_manifest_injects_api_key_from_secret():
    container = _load()["spec"]["template"]["spec"]["containers"][0]
    env = {e["name"]: e for e in container["env"]}
    assert env["BRAIN_API_KEY"]["valueFrom"]["secretKeyRef"]["name"] == "brain-api-key"


def test_manifest_keeps_image_placeholder_for_deploy_substitution():
    container = _load()["spec"]["template"]["spec"]["containers"][0]
    assert container["image"] == "__IMAGE__"
