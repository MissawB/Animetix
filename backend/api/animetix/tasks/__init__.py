from animetix_project.logging_config import get_logger

from animetix.tasks_registry import register_task


def get_container():
    from ..containers import get_container as _get_container  # noqa: E402

    return _get_container()


logger = get_logger("animetix." + __name__)


def generate_fusion_image(item1, item2, art_style="Cyberpunk"):
    container = get_container()
    return container.core.fusion_service.generate_fusion_image(
        item1, item2, art_style=art_style
    )


@register_task("generate_fusion_scenario_task")
def generate_fusion_scenario_task(
    media_type,
    item1,
    item2,
    language,
    chaos_level=50,
    universe_balance=50,
    art_style="Cyberpunk",
):
    try:
        container = get_container()
        return container.llm_service.generate_fusion_scenario(
            media_type,
            item1,
            item2,
            language,
            chaos_level=chaos_level,
            universe_balance=universe_balance,
            art_style=art_style,
        )
    except Exception as e:
        logger.error(f"Task Error in generate_fusion_scenario: {e}")
        return "Erreur lors de la génération du scénario."


@register_task("generate_fusion_image_task")
def generate_fusion_image_task(fusion_data, item1, item2, art_style="Cyberpunk"):
    try:
        if isinstance(fusion_data, str):
            fusion_data = {"scenario": fusion_data}
        image_url = generate_fusion_image(item1, item2, art_style=art_style)
        fusion_data["fusion_image"] = image_url
        return fusion_data
    except Exception as e:
        logger.error(f"Task Error in generate_fusion_image: {e}")
        return fusion_data


@register_task("generate_fusion_flow_task")
def generate_fusion_flow_task(
    media_type,
    item1,
    item2,
    language,
    chaos_level=50,
    universe_balance=50,
    art_style="Cyberpunk",
):
    scenario = generate_fusion_scenario_task(
        media_type,
        item1,
        item2,
        language,
        chaos_level=chaos_level,
        universe_balance=universe_balance,
        art_style=art_style,
    )
    result = generate_fusion_image_task(scenario, item1, item2, art_style=art_style)
    return result


@register_task("run_star_training_cycle_task")
def run_star_training_cycle_task():
    container = get_container()
    new_entries = container.star_mlops_service.prepare_star_dataset()
    if new_entries < 1:
        return "Insufficient new traces."
    result = container.star_mlops_service.trigger_finetuning()
    return f"STaR cycle triggered: {result['status']}"


@register_task("sync_media_item_task")
def sync_media_item_task(media_type, item_id, data):
    container = get_container()
    container.sync_service.handle_media_update(media_type, item_id, data)


@register_task("trigger_club_event")
def trigger_club_event(club_id, event_id):
    """
    Signals all members of a club via WebSocket that an event has started.
    """
    from asgiref.sync import async_to_sync  # noqa: E402
    from channels.layers import get_channel_layer  # noqa: E402

    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.error("No channel layer found for club event trigger.")
        return

    group_name = f"club_{club_id}"

    # Broadcast to the club's WebSocket group
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "event_start",
            "event_id": event_id,
            "message": "L'événement du club commence maintenant !",
        },
    )
    logger.info(f"Triggered event {event_id} for club {club_id}")


@register_task("self_hosted_image_generation_task")
def self_hosted_image_generation_task(prompt: str, style: str = ""):
    from django.core.cache import cache

    logger.info(f"Starting self_hosted_image_generation_task for prompt: {prompt}")
    cache.set("self_hosted_image_worker:status", "active")
    cache.set("self_hosted_image_worker:active_task", prompt)
    try:
        container = get_container()
        adapter = container.inference.diffusers_adapter()
        result = adapter.generate_image(prompt, style=style)
        logger.info("Successfully generated image via diffusers_adapter")
        return result
    except Exception as e:
        logger.error(f"Error in self_hosted_image_generation_task: {e}")
        raise e
    finally:
        cache.delete("self_hosted_image_worker:active_task")
        try:
            queue_len = cache.get("self_hosted_image_worker:queue_length", 0)
            cache.set("self_hosted_image_worker:queue_length", max(0, queue_len - 1))
        except Exception as e:
            logger.debug(f"Could not decrement worker queue length: {e}")

        # Re-check queue length to set worker status back to idle if empty
        new_queue_len = cache.get("self_hosted_image_worker:queue_length", 0)
        if new_queue_len <= 0:
            cache.set("self_hosted_image_worker:status", "idle")


from . import (  # noqa: E402
    manga_tasks as manga_tasks,
    telemetry_tasks as telemetry_tasks,
)
