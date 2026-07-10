"""Coverage for animetix.creative_tasks — Celery task bodies.

These are not HTTP views: each is a registered task function. They are called
directly with a mocked dependency-injection container. Each task does:

    container = get_container()          # patched -> MagicMock
    bytes = base64.b64decode(<input>)    # real decode of a tiny payload
    result = container.<service>().<method>(...)

We patch ``animetix.containers.get_container`` (the symbol the task imports
locally via ``from .containers import get_container``) and assert the service
method is called with the decoded bytes and that the return value is wrapped
as the task documents.

``process_gcs_upload_task`` has dev/prod branches and several failure paths;
those are covered with ``override_settings`` and patched GCS storage.
"""

import base64
from unittest.mock import MagicMock, patch

import pytest
from animetix import creative_tasks as ct
from django.test import override_settings

PAYLOAD = base64.b64encode(b"raw-binary-data").decode()


def _container_with(service_attr, method_name, return_value):
    """Build a mock container whose ``core.service_attr()`` exposes ``method_name``."""
    container = MagicMock()
    service = MagicMock()
    getattr(service, method_name).return_value = return_value
    getattr(container.core, service_attr).return_value = service
    return container, service


# --------------------------------------------------------------------------- #
# process_video_search_task
# --------------------------------------------------------------------------- #
def test_process_video_search_task():
    container, service = _container_with(
        "video_quest_service", "index_video_clips", ["seg1", "seg2"]
    )
    service.search_moment_in_video.return_value = {"moment": "3:14"}

    with patch("animetix.containers.get_container", return_value=container):
        result = ct.process_video_search_task(PAYLOAD, "a fight scene")

    assert result == {"moment": "3:14"}
    service.index_video_clips.assert_called_once_with(b"raw-binary-data")
    service.search_moment_in_video.assert_called_once_with(
        "a fight scene", ["seg1", "seg2"]
    )


# --------------------------------------------------------------------------- #
# transform_user_image_task
# --------------------------------------------------------------------------- #
def test_transform_user_image_task():
    container, service = _container_with(
        "studio_transform_service", "transform_user_to_anime", "http://img"
    )
    with patch("animetix.containers.get_container", return_value=container):
        result = ct.transform_user_image_task(PAYLOAD, "Ghibli")

    assert result == {"image_url": "http://img"}
    service.transform_user_to_anime.assert_called_once_with(
        b"raw-binary-data", "Ghibli"
    )


# --------------------------------------------------------------------------- #
# translate_manga_page_task
# --------------------------------------------------------------------------- #
def test_translate_manga_page_task():
    container, service = _container_with(
        "manga_flow_service", "translate_manga_page", "http://translated"
    )
    with patch("animetix.containers.get_container", return_value=container):
        result = ct.translate_manga_page_task(PAYLOAD, "French")

    assert result == {"translated_image_url": "http://translated"}
    service.translate_manga_page.assert_called_once_with(b"raw-binary-data", "French")


# --------------------------------------------------------------------------- #
# localize_video_action_task
# --------------------------------------------------------------------------- #
def test_localize_video_action_task():
    container, service = _container_with(
        "video_quest_service", "find_action_boundaries", [(0, 5)]
    )
    with patch("animetix.containers.get_container", return_value=container):
        result = ct.localize_video_action_task(PAYLOAD, ["punch"])

    assert result == {"actions_found": [(0, 5)]}
    service.find_action_boundaries.assert_called_once_with(
        b"raw-binary-data", ["punch"]
    )


# --------------------------------------------------------------------------- #
# transform_video_task
# --------------------------------------------------------------------------- #
def test_transform_video_task():
    container, service = _container_with(
        "studio_transform_service",
        "transform_video_to_anime_consistent",
        "http://vid",
    )
    with patch("animetix.containers.get_container", return_value=container):
        result = ct.transform_video_task(PAYLOAD, "Madhouse")

    assert result == {"video_url": "http://vid"}
    service.transform_video_to_anime_consistent.assert_called_once_with(
        b"raw-binary-data", "Madhouse"
    )


# --------------------------------------------------------------------------- #
# generate_video_soundscape_task
# --------------------------------------------------------------------------- #
def test_generate_video_soundscape_task():
    container, service = _container_with(
        "soundscape_service", "generate_soundscape_for_video", "http://audio"
    )
    with patch("animetix.containers.get_container", return_value=container):
        result = ct.generate_video_soundscape_task(PAYLOAD)

    assert result == {"audio_url": "http://audio"}
    service.generate_soundscape_for_video.assert_called_once_with(b"raw-binary-data")


# --------------------------------------------------------------------------- #
# generate_3d_scene_task
# --------------------------------------------------------------------------- #
def test_generate_3d_scene_task():
    container, service = _container_with(
        "spatial_computing_service", "reconstruct_3d_scene", {"mesh": "x"}
    )
    with patch("animetix.containers.get_container", return_value=container):
        result = ct.generate_3d_scene_task(PAYLOAD, "My Scene")

    assert result == {"mesh": "x"}
    service.reconstruct_3d_scene.assert_called_once_with(b"raw-binary-data", "My Scene")


# --------------------------------------------------------------------------- #
# generate_fusion_image (plain helper, not a registered task)
# --------------------------------------------------------------------------- #
def test_generate_fusion_image_default_style():
    container, service = _container_with(
        "fusion_service", "generate_fusion_image", "http://fusion"
    )
    with patch("animetix.containers.get_container", return_value=container):
        result = ct.generate_fusion_image("Naruto", "Goku")

    assert result == "http://fusion"
    service.generate_fusion_image.assert_called_once_with(
        "Naruto", "Goku", art_style="Cyberpunk"
    )


def test_generate_fusion_image_custom_style():
    container, service = _container_with(
        "fusion_service", "generate_fusion_image", "http://fusion2"
    )
    with patch("animetix.containers.get_container", return_value=container):
        result = ct.generate_fusion_image("A", "B", art_style="Watercolor")

    assert result == "http://fusion2"
    service.generate_fusion_image.assert_called_once_with(
        "A", "B", art_style="Watercolor"
    )


# --------------------------------------------------------------------------- #
# process_gcs_upload_task — dev branch (IS_PRODUCTION False)
# --------------------------------------------------------------------------- #
@override_settings(IS_PRODUCTION=False)
def test_process_gcs_upload_dev_success():
    container = MagicMock()
    manga = MagicMock()
    # A valid data URI; the task strips the header and decodes the payload.
    manga.translate_manga_page.return_value = (
        "data:image/jpeg;base64," + base64.b64encode(b"out").decode()
    )
    container.core.manga_flow_service.return_value = manga

    with patch("animetix.containers.get_container", return_value=container):
        result = ct.process_gcs_upload_task("bucket", "raw-manga/page.jpg")

    # raw-manga/ is rewritten to translated-manga/
    assert result["status"] == "success"
    assert result["processed_path"] == "translated-manga/page.jpg"
    # In dev the input bytes come from a synthesised PIL image (non-empty).
    args, kwargs = manga.translate_manga_page.call_args
    assert isinstance(args[0], (bytes, bytearray)) and len(args[0]) > 0
    assert kwargs["target_lang"] == "French"


@override_settings(IS_PRODUCTION=False)
def test_process_gcs_upload_dev_processed_name_fallback():
    """A name with no known prefix falls back to processed/<basename>."""
    container = MagicMock()
    manga = MagicMock()
    manga.translate_manga_page.return_value = (
        "data:image/png;base64," + base64.b64encode(b"out").decode()
    )
    container.core.manga_flow_service.return_value = manga

    with patch("animetix.containers.get_container", return_value=container):
        result = ct.process_gcs_upload_task("bucket", "manga/cover.png")

    assert result["processed_path"] == "processed/cover.png"


@override_settings(IS_PRODUCTION=False)
def test_process_gcs_upload_invalid_output_format():
    container = MagicMock()
    manga = MagicMock()
    manga.translate_manga_page.return_value = "not-a-data-uri"
    container.core.manga_flow_service.return_value = manga

    with patch("animetix.containers.get_container", return_value=container):
        with pytest.raises(ValueError, match="Invalid output format"):
            ct.process_gcs_upload_task("bucket", "raw-manga/page.jpg")


# --------------------------------------------------------------------------- #
# process_gcs_upload_task — prod branch (IS_PRODUCTION True)
# --------------------------------------------------------------------------- #
@override_settings(IS_PRODUCTION=True)
def test_process_gcs_upload_prod_success():
    container = MagicMock()
    manga = MagicMock()
    manga.translate_manga_page.return_value = (
        "data:image/jpeg;base64," + base64.b64encode(b"processed").decode()
    )
    container.core.manga_flow_service.return_value = manga

    storage = MagicMock()
    opened = MagicMock()
    opened.read.return_value = b"downloaded-bytes"
    storage.open.return_value.__enter__.return_value = opened

    with (
        patch("animetix.containers.get_container", return_value=container),
        patch("storages.backends.gcloud.GoogleCloudStorage", return_value=storage),
    ):
        result = ct.process_gcs_upload_task("bkt", "raw/page.jpg")

    assert result["status"] == "success"
    # raw/ -> processed/
    assert result["processed_path"] == "processed/page.jpg"
    manga.translate_manga_page.assert_called_once_with(
        b"downloaded-bytes", target_lang="French"
    )
    storage.save.assert_called_once()


@override_settings(IS_PRODUCTION=True)
def test_process_gcs_upload_prod_download_failure():
    container = MagicMock()
    container.core.manga_flow_service.return_value = MagicMock()
    storage = MagicMock()
    storage.open.side_effect = OSError("not found")

    with (
        patch("animetix.containers.get_container", return_value=container),
        patch("storages.backends.gcloud.GoogleCloudStorage", return_value=storage),
    ):
        with pytest.raises(OSError, match="not found"):
            ct.process_gcs_upload_task("bkt", "raw/page.jpg")


@override_settings(IS_PRODUCTION=True)
def test_process_gcs_upload_prod_translate_failure():
    container = MagicMock()
    manga = MagicMock()
    manga.translate_manga_page.side_effect = RuntimeError("model down")
    container.core.manga_flow_service.return_value = manga

    storage = MagicMock()
    opened = MagicMock()
    opened.read.return_value = b"bytes"
    storage.open.return_value.__enter__.return_value = opened

    with (
        patch("animetix.containers.get_container", return_value=container),
        patch("storages.backends.gcloud.GoogleCloudStorage", return_value=storage),
    ):
        with pytest.raises(RuntimeError, match="model down"):
            ct.process_gcs_upload_task("bkt", "raw/page.jpg")


@override_settings(IS_PRODUCTION=True)
def test_process_gcs_upload_prod_upload_failure():
    container = MagicMock()
    manga = MagicMock()
    manga.translate_manga_page.return_value = (
        "data:image/jpeg;base64," + base64.b64encode(b"x").decode()
    )
    container.core.manga_flow_service.return_value = manga

    storage = MagicMock()
    opened = MagicMock()
    opened.read.return_value = b"bytes"
    storage.open.return_value.__enter__.return_value = opened
    storage.save.side_effect = RuntimeError("upload failed")

    with (
        patch("animetix.containers.get_container", return_value=container),
        patch("storages.backends.gcloud.GoogleCloudStorage", return_value=storage),
    ):
        with pytest.raises(RuntimeError, match="upload failed"):
            ct.process_gcs_upload_task("bkt", "raw/page.jpg")
