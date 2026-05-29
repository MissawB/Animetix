import json
import os
import httpx
import re
import logging
from typing import List
from dotenv import load_dotenv

logger = logging.getLogger("animetix." + __name__)

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

BRAIN_URL = os.getenv("BRAIN_API_URL")

class DataIntelligence:
    def __init__(self):
        self.brain_url = BRAIN_URL

    def extract_micro_tags(self, title, description, media_type):
        """Utilise le LLM pour générer des tags ultra-précis."""
        if not self.brain_url: return []
        
        prompt = f"""Analyse cette œuvre ({media_type}) et génère 5 à 8 micro-tags thématiques très précis (ex: 'Héros stoïque', 'Univers mélancolique', 'Plot-twist temporel', 'Esthétique Cyberpunk').
        Titre : {title}
        Description : {description[:1000]}
        
        Réponds UNIQUEMENT par une liste de tags séparés par des virgules.
        """
        
        try:
            response = httpx.post(f"{self.brain_url}/generate", json={
                "prompt": prompt,
                "system_prompt": "Tu es un documentaliste expert en culture geek. Tes tags sont précis et utiles pour un moteur de recherche."
            }, timeout=30, follow_redirects=True)
            
            if response.status_code == 200:
                text = response.json().get("text", "")
                tags = [t.strip() for t in text.split(',') if len(t.strip()) > 2]
                return tags[:10]
        except Exception as e:
            logger.warning(f"⚠️ Error generating tags for {title}: {e}")
            pass
        return []

    def extract_visual_knowledge(self, image_data: bytes) -> List[str]:
        """Extrait des connaissances à partir du visuel (posters/screenshots)."""
        # Utilisation du service de vision centralisé
        from animetix.containers import get_container
        vision_service = get_container().vision_service()
        return vision_service.detect_visual_attributes(image_data)

    def build_relation_graph(self, media_data, media_type):
        """Extrait les entités pour le graphe de connaissances (Studio, Staff, etc.)."""
        relations = {
            "studios": media_data.get('studios', []),
            "author": media_data.get('author'),
            "director": media_data.get('director'),
            "genre_nodes": media_data.get('genres', []),
            "year_node": media_data.get('year')
        }
        return {k: v for k, v in relations.items() if v}

intelligence_service = DataIntelligence()
