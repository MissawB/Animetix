from celery import shared_task
from .services import LangChainService
import time

@shared_task
def generate_fusion_scenario_task(media_type, item1, item2, language):
    """Tâche asynchrone pour générer le synopsis de fusion."""
    langchain_service = LangChainService()
    # On simule un délai pour voir la progression côté UI si besoin
    # time.sleep(2) 
    res = langchain_service.generate_scenario_advanced(media_type, item1, item2, language)
    return res

@shared_task
def generate_fusion_image_task(scenario_text, title_A, title_B):
    """Tâche asynchrone pour générer l'image de fusion."""
    langchain_service = LangChainService()
    vis_prompt = f"Fusion of {title_A} and {title_B}: {scenario_text[:200]}"
    image_url = langchain_service.generate_fusion_image(vis_prompt)
    return image_url

@shared_task
def generate_full_fusion_task(media_type, item1, item2, language):
    """Tâche combo qui génère le texte PUIS l'image."""
    langchain_service = LangChainService()
    
    # 1. Texte
    res = langchain_service.generate_scenario_advanced(media_type, item1, item2, language)
    
    # 2. Image
    title_A = item1.get('title') or item1.get('name')
    title_B = item2.get('title') or item2.get('name')
    vis_prompt = f"Fusion of {title_A} and {title_B}: {res.get('scenario', '')[:200]}"
    image_url = langchain_service.generate_fusion_image(vis_prompt)
    
    return {
        'reasoning': res.get('reasoning'),
        'scenario': res.get('scenario'),
        'fusion_image': image_url
    }
