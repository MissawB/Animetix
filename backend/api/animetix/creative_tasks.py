from animetix_project.logging_config import get_logger

from animetix.tasks_registry import register_task

logger = get_logger("animetix." + __name__)


@register_task("process_video_search_task")
def process_video_search_task(video_data_b64, query):
    """Tâche asynchrone pour Video-RAG."""
    import base64  # noqa: E402

    from .containers import get_container  # noqa: E402

    container = get_container()
    video_bytes = base64.b64decode(video_data_b64)

    # 1. Indexation temporelle
    segments = container.core.video_quest_service().index_video_clips(video_bytes)

    # 2. Recherche du moment
    result = container.core.video_quest_service().search_moment_in_video(
        query, segments
    )
    return result


@register_task("transform_user_image_task")
def transform_user_image_task(image_data_b64, studio_name):
    """Tâche asynchrone pour Anime-to-Real transformation."""
    import base64  # noqa: E402

    from .containers import get_container  # noqa: E402

    container = get_container()
    image_bytes = base64.b64decode(image_data_b64)

    image_url = container.core.studio_transform_service().transform_user_to_anime(
        image_bytes, studio_name
    )
    return {"image_url": image_url}


@register_task("translate_manga_page_task")
def translate_manga_page_task(image_data_b64, target_lang):
    """Tâche asynchrone pour le pipeline Manga Flow."""
    import base64  # noqa: E402

    from .containers import get_container  # noqa: E402

    container = get_container()
    image_bytes = base64.b64decode(image_data_b64)

    translated_image_url = container.core.manga_flow_service().translate_manga_page(
        image_bytes, target_lang
    )
    return {"translated_image_url": translated_image_url}


@register_task("localize_video_action_task")
def localize_video_action_task(video_data_b64, actions):
    """Tâche asynchrone pour la Temporal Action Localization (TAL)."""
    import base64  # noqa: E402

    from .containers import get_container  # noqa: E402

    container = get_container()
    video_bytes = base64.b64decode(video_data_b64)

    # 1. Détection des bornes de l'action
    action_boundaries = container.core.video_quest_service().find_action_boundaries(
        video_bytes, actions
    )
    return {"actions_found": action_boundaries}


@register_task("transform_video_task")
def transform_video_task(video_data_b64, studio_name):
    """Tâche asynchrone pour le Neural Style Transfer sur vidéo avec consistance temporelle."""
    import base64  # noqa: E402

    from .containers import get_container  # noqa: E402

    container = get_container()
    video_bytes = base64.b64decode(video_data_b64)

    video_url = (
        container.core.studio_transform_service().transform_video_to_anime_consistent(
            video_bytes, studio_name
        )
    )
    return {"video_url": video_url}


@register_task("generate_video_soundscape_task")
def generate_video_soundscape_task(video_data_b64):
    """Tâche asynchrone pour générer une ambiance sonore à partir d'une vidéo."""
    import base64  # noqa: E402

    from .containers import get_container  # noqa: E402

    container = get_container()
    video_bytes = base64.b64decode(video_data_b64)

    audio_url = container.core.soundscape_service().generate_soundscape_for_video(
        video_bytes
    )
    return {"audio_url": audio_url}


@register_task("generate_3d_scene_task")
def generate_3d_scene_task(image_data_b64, title):
    """Tâche asynchrone pour la reconstruction de scène 3D (Spatial Computing)."""
    import base64  # noqa: E402

    from .containers import get_container  # noqa: E402

    container = get_container()
    image_bytes = base64.b64decode(image_data_b64)

    scene_result = container.core.spatial_computing_service().reconstruct_3d_scene(
        image_bytes, title
    )
    return scene_result


def generate_fusion_image(item1, item2, art_style="Cyberpunk"):
    """Délégation au domaine pour la génération d'image de fusion."""
    from .containers import get_container  # noqa: E402

    container = get_container()
    return container.core.fusion_service().generate_fusion_image(
        item1, item2, art_style=art_style
    )


@register_task("process_gcs_upload_task")
def process_gcs_upload_task(bucket, name):
    """
    Asynchronously processes a raw manga page uploaded to GCS.
    Downloads the image, translates it via MangaFlowService, and uploads the result back.
    """
    import base64  # noqa: E402
    import os  # noqa: E402

    from django.conf import settings  # noqa: E402

    from .containers import get_container  # noqa: E402

    logger.info(f"Processing GCS upload event: gs://{bucket}/{name}")
    container = get_container()
    is_prod = getattr(settings, "IS_PRODUCTION", False)

    if not is_prod:
        logger.info("Local development fallback active. Simulating image retrieval.")
        from io import BytesIO  # noqa: E402

        from PIL import Image as PILImage  # noqa: E402

        img = PILImage.new("RGB", (100, 100), color="white")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        image_bytes = buf.getvalue()
    else:
        from storages.backends.gcloud import GoogleCloudStorage  # noqa: E402

        try:
            gcs_storage = GoogleCloudStorage(bucket_name=bucket)
            with gcs_storage.open(name) as f:
                image_bytes = f.read()
        except Exception as download_err:
            logger.error(
                f"GCS download failed for gs://{bucket}/{name}: {download_err}"
            )
            raise download_err

    try:
        translated_b64 = container.core.manga_flow_service().translate_manga_page(
            image_bytes, target_lang="French"
        )
        if not translated_b64.startswith("data:image/"):
            raise ValueError("Invalid output format from MangaFlowService")

        header, encoded = translated_b64.split(",", 1)
        processed_bytes = base64.b64decode(encoded)
    except Exception as translate_err:
        logger.error(
            f"Manga translation failed for gs://{bucket}/{name}: {translate_err}"
        )
        raise translate_err

    processed_name = name.replace("raw-manga/", "translated-manga/").replace(
        "raw/", "processed/"
    )
    if processed_name == name:
        processed_name = f"processed/{os.path.basename(name)}"

    if not is_prod:
        logger.info(
            f"Local development: would save translated image to GCS at: {processed_name}"
        )
    else:
        from django.core.files.base import ContentFile  # noqa: E402
        from storages.backends.gcloud import GoogleCloudStorage  # noqa: E402

        try:
            gcs_storage = GoogleCloudStorage(bucket_name=bucket)
            gcs_storage.save(processed_name, ContentFile(processed_bytes))
            logger.info(
                f"Successfully processed and uploaded to GCS at gs://{bucket}/{processed_name}"
            )
        except Exception as upload_err:
            logger.error(
                f"GCS upload failed for gs://{bucket}/{processed_name}: {upload_err}"
            )
            raise upload_err

    return {"status": "success", "processed_path": processed_name}
