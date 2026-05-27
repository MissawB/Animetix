from celery import shared_task

from ..containers import get_container


@shared_task(name="animetix.tasks.generate_fusion_scenario_task")
def generate_fusion_scenario_task(media_type: str, item1: dict, item2: dict, language: str) -> dict:
    """Celery task that generates a fusion scenario via LLMService.
    Returns the raw dict returned by ``generate_fusion_scenario``.
    """
    container = get_container()
    # The LLM service returns a dict like {"scenario": "..."}
    return container.llm_service.generate_fusion_scenario(
        media_type, item1, item2, language
    )


@shared_task(name="animetix.tasks.generate_fusion_image_task")
def generate_fusion_image_task(fusion_data: dict, item1: dict, item2: dict, art_style: str = "Cyberpunk") -> dict:
    """Celery task that generates a fusion image URL.
    ``fusion_data`` is expected to contain the scenario dict, but is not used directly.
    Returns a dict with the generated image URL under the ``fusion_image`` key.
    """
    container = get_container()
    image_url = container.fusion_service.generate_fusion_image(item1, item2, art_style=art_style)
    return {"fusion_image": image_url}
