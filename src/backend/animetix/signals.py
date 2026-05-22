from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MediaItem, ChallengeResult, GlobalBoss, Friendship
from .services import AnimetixService
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
                        "message": f"Ton ami(e) {instance.user.username} a réussi le Défi du Jour !"
                    }
                }
            )

@receiver(post_save, sender=GlobalBoss)
def broadcast_boss_phase(sender, instance, created, **kwargs):
    """
    Alerte globale lorsque la phase du World Boss change.
    """
    if not created: # On surveille les changements d'état
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "global_notifications",
            {
                "type": "send_notification",
                "data": {
                    "type": "boss_alert",
                    "title": instance.title,
                    "phase": instance.current_phase,
                    "message": f"🚨 ALERTE : Le World Boss {instance.title} entre en Phase {instance.current_phase} !"
                }
            }
        )

@receiver(post_save, sender=MediaItem)
def sync_media_on_save(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser automatiquement ChromaDB et Neo4j 
    lorsqu'un MediaItem est créé ou modifié (Asynchrone via Celery).
    """
    from .tasks import sync_media_item_task
    
    # Préparation des données pour le domaine
    data = {
        'id': instance.external_id,
        'title': instance.title,
        'title_english': instance.title_english,
        'title_native': instance.title_native,
        'description': instance.description,
        'image': instance.image_url,
        'year': instance.release_year,
        'popularity': instance.popularity,
        'genres': instance.metadata.get('genres', []),
        'tags': instance.metadata.get('tags', []),
        'metadata': instance.metadata
    }
    
    # Lancement de la tâche asynchrone
    sync_media_item_task.delay(
        media_type=instance.media_type,
        item_id=instance.external_id,
        data=data
    )
