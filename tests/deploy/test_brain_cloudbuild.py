import pathlib

import yaml

CLOUDBUILD = (
    pathlib.Path(__file__).resolve().parents[2] / "deploy" / "cloudbuild.brain.yaml"
)


def _text():
    return CLOUDBUILD.read_text(encoding="utf-8")


def _doc():
    return yaml.safe_load(_text())


def test_cloudbuild_declares_region_and_tag_substitutions():
    subs = _doc()["substitutions"]
    assert subs["_REGION"] == "europe-west1"
    assert subs["_TAG"] == "latest"


def test_cloudbuild_deploys_via_services_replace():
    text = _text()
    # The declarative apply is what makes the cost posture auditable.
    assert "gcloud run services replace" in text
    assert "run-brain.service.yaml" in text
    assert "${_REGION}" in text


def test_cloudbuild_substitutes_pinned_image_into_manifest():
    text = _text()
    assert "__IMAGE__" in text  # placeholder is substituted at deploy time
    assert "brain:${_TAG}" in text
