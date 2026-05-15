from celery import shared_task
from backend.animetix.services import AnimetixService
import time

@shared_task
def process_video_search_task(video_data_b64, query):
    """Tâche asynchrone pour Video-RAG."""
    import base64
    video_bytes = base64.b64decode(video_data_b64)
    animetix = AnimetixService()
    
    # 1. Indexation temporelle
    segments = animetix.video_quest_service.index_video_clips(video_bytes)
    
    # 2. Recherche du moment
    result = animetix.video_quest_service.search_moment_in_video(query, segments)
    return result

@shared_task
def transform_user_image_task(image_data_b64, studio_name):
    """Tâche asynchrone pour Anime-to-Real transformation."""
    import base64
    image_bytes = base64.b64decode(image_data_b64)
    animetix = AnimetixService()
    
    image_url = animetix.studio_transform_service.transform_user_to_anime(image_bytes, studio_name)
    return {"image_url": image_url}

@shared_task
def translate_manga_page_task(image_data_b64, target_lang):
    """Tâche asynchrone pour le pipeline Manga Flow."""
    import base64
    image_bytes = base64.b64decode(image_data_b64)
    animetix = AnimetixService()
    
    translated_image_url = animetix.manga_flow_service.translate_manga_page(image_bytes, target_lang)
    return {"translated_image_url": translated_image_url}

@shared_task
def localize_video_action_task(video_data_b64, actions):
    """Tâche asynchrone pour la Temporal Action Localization (TAL)."""
    import base64
    video_bytes = base64.b64decode(video_data_b64)
    animetix = AnimetixService()
    
    # 1. Détection des bornes de l'action
    action_boundaries = animetix.video_quest_service.find_action_boundaries(video_bytes, actions)
    return {"actions_found": action_boundaries}

@shared_task
def transform_video_task(video_data_b64, studio_name):
    """Tâche asynchrone pour le Neural Style Transfer sur vidéo avec consistance temporelle."""
    import base64
    video_bytes = base64.b64decode(video_data_b64)
    animetix = AnimetixService()
    
    video_url = animetix.studio_transform_service.transform_video_to_anime_consistent(video_bytes, studio_name)
    return {"video_url": video_url}

@shared_task
def generate_video_soundscape_task(video_data_b64):
    """Tâche asynchrone pour générer une ambiance sonore à partir d'une vidéo."""
    import base64
    video_bytes = base64.b64decode(video_data_b64)
    animetix = AnimetixService()
    
    audio_url = animetix.soundscape_service.generate_soundscape_for_video(video_bytes)
    return {"audio_url": audio_url}

@shared_task
def generate_3d_scene_task(image_data_b64, title):
    """Tâche asynchrone pour la reconstruction de scène 3D (Spatial Computing)."""
    import base64
    image_bytes = base64.b64decode(image_data_b64)
    animetix = AnimetixService()
    
    scene_result = animetix.spatial_computing_service.reconstruct_3d_scene(image_bytes, title)
    return scene_result
