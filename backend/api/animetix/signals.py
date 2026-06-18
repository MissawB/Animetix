from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    MediaItem,
    ChallengeResult,
    GlobalBoss,
    Friendship,
    Notification,
    ArchetypeDriftSnapshot,
    DuelRoom,
    AIFeedback,
    GoldDatasetEntry,
)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# ... [existing signal handlers are unmodified] ...


@receiver(post_save, sender=Notification)
def broadcast_notification(sender, instance, created, **kwargs):
    """
    Pousse la notification en temps réel vers le client via WebSocket.
    """
    if created:
        channel_layer = get_channel_layer()
        group_name = f"user_notifications_{instance.user.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "data": {
                    "id": instance.id,
                    "title": instance.title,
                    "message": instance.message,
                    "type": instance.notification_type,
                    "link": instance.link,
                    "created_at": instance.created_at.isoformat(),
                    "is_read": instance.is_read,
                },
            },
        )


@receiver(post_save, sender=ChallengeResult)
def broadcast_challenge_result(sender, instance, created, **kwargs):
    """
    Notifie les followers du joueur lorsqu'il réussit un défi du jour.
    """
    if created and instance.was_won:
        channel_layer = get_channel_layer()
        followers = Friendship.objects.filter(to_user=instance.user)

        for f in followers:
            group_name = f"user_notifications_{f.from_user.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",
                    "data": {
                        "type": "friend_achievement",
                        "user": instance.user.username,
                        "game_mode": instance.game_mode,
                        "message": f"Ton ami(e) {instance.user.username} a réussi le Défi du Jour !",
                    },
                },
            )


@receiver(post_save, sender=GlobalBoss)
def broadcast_boss_phase(sender, instance, created, **kwargs):
    """
    Alerte globale lorsque la phase du World Boss change.
    """
    if not created:
        # On surveille les changements d'état
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "global_notifications",
            {
                "type": "send_notification",
                "data": {
                    "type": "boss_alert",
                    "title": instance.title,
                    "phase": instance.current_phase,
                    "message": f"🚨 ALERTE : Le World Boss {instance.title} entre en Phase {instance.current_phase} !",
                },
            },
        )


@receiver(post_save, sender=MediaItem)
def sync_media_on_save(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser automatiquement ChromaDB et Neo4j
    lorsqu'un MediaItem est créé ou modifié (Asynchrone via Celery).
    """
    from animetix.tasks_client import enqueue_task  # noqa: E402

    # Préparation des données pour le domaine
    data = {
        "id": instance.external_id,
        "title": instance.title,
        "title_english": instance.title_english,
        "title_native": instance.title_native,
        "description": instance.description,
        "image": instance.image_url,
        "year": instance.release_year,
        "popularity": instance.popularity,
        "genres": instance.metadata.get("genres", []),
        "tags": instance.metadata.get("tags", []),
        "metadata": instance.metadata,
    }

    # Lancement de la tâche asynchrone via Cloud Tasks
    enqueue_task(
        "sync_media_item_task", instance.media_type, instance.external_id, data
    )


@receiver(post_save, sender=ArchetypeDriftSnapshot)
def trigger_drift_telemetry(sender, instance, created, **kwargs):
    if created:
        from animetix.tasks_client import enqueue_task  # noqa: E402

        enqueue_task("ingest_drift_telemetry", instance.id)

        # Publish to Pub/Sub
        from animetix.pubsub_service import PubSubPublisherService  # noqa: E402

        pubsub = PubSubPublisherService()
        pubsub.publish_event(
            "animetix-events-topic",
            {
                "event_type": "archetype_drift_created",
                "snapshot_id": instance.id,
                "user_id": instance.user.id,
                "archetype_id": instance.archetype_id,
                "intensity": float(instance.intensity),
                "shonen_affinity": float(instance.shonen_affinity),
                "seinen_affinity": float(instance.seinen_affinity),
                "logic_consistency": float(instance.logic_consistency),
            },
        )


@receiver(post_save, sender=DuelRoom)
def trigger_duel_telemetry(sender, instance, created, **kwargs):
    if instance.is_finished:
        from animetix.tasks_client import enqueue_task  # noqa: E402

        enqueue_task("ingest_duel_telemetry", instance.id)

        # Publish to Pub/Sub
        from animetix.pubsub_service import PubSubPublisherService  # noqa: E402

        pubsub = PubSubPublisherService()
        pubsub.publish_event(
            "animetix-events-topic",
            {
                "event_type": "duel_completed",
                "room_id": instance.id,
                "player1_id": instance.player1.id if instance.player1 else None,
                "player2_id": instance.player2.id if instance.player2 else None,
                "winner_id": instance.winner.id if instance.winner else None,
                "secret_title": instance.secret_title,
                "media_type": instance.media_type,
            },
        )


@receiver(post_save, sender=AIFeedback)
def flag_and_stage_complex_user_query(sender, instance, created, **kwargs):
    """
    Connecte le système de feedback utilisateur de l'application Django pour flagger
    et stager automatiquement les requêtes utilisateur complexes dans une file
    de modération HITL (GoldDatasetEntry) avant leur intégration dans le Gold Set.
    """
    if created:
        query = instance.input_context
        if not query:
            return

        try:
            # 1. Évaluation de la complexité via le ComplexityAnalyser ou des règles heuristiques
            from core.domain.services.complexity_analyser import ComplexityAnalyser  # noqa: E402
            from animetix.containers import get_container  # noqa: E402

            container = get_container()
            pm = getattr(container, "prompt_manager", None)
            llm = getattr(container, "llm_service", None)

            if pm and llm:
                analyser = ComplexityAnalyser(pm(), llm())
            else:
                analyser = ComplexityAnalyser()

            _, complexity_score = analyser.assess_complexity(query)
        except Exception as e:
            import logging
            logger = logging.getLogger("animetix.signals")
            logger.warning(
                f"Failed to use ComplexityAnalyser in signal, falling back to simple rules: {e}"
            )
            complexity_score = 0
            q_lower = query.lower()
            keywords = [
                "ressemble",
                "comparaison",
                "similaire",
                "recommande",
                "différence",
                "pourquoi",
                "paradoxe",
                "intrus",
                "thème",
                "influence",
                "explication",
                "philosophique",
                "scénar",
                "scénario",
                "décors",
            ]
            if any(w in q_lower for w in keywords) or len(query.split()) > 10:
                complexity_score = 1

        is_complex = complexity_score >= 1

        # 2. Si la requête est complexe, on la stage dans GoldDatasetEntry pour validation HITL
        if is_complex:
            if not GoldDatasetEntry.objects.filter(source_feedback=instance).exists():
                GoldDatasetEntry.objects.create(
                    context=instance.input_context,
                    instruction=instance.input_context,
                    response=instance.output_text,
                    entry_type="QA",
                    source_feedback=instance,
                    is_validated=False,  # En attente de revue humaine
                    metadata={
                        "staged_from_feedback": True,
                        "is_complex_user_query": True,
                        "complexity_score": complexity_score,
                        "user_id": instance.user.id if instance.user else None,
                    },
                )
