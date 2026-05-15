import numpy as np
import orjson
import os
import random
import requests
import re
import hashlib
import base64
import torch
import logging
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.core.cache import cache

from .containers import get_container
from core.domain.exceptions import CatalogNotFoundError, InferenceError, AnimetixError
from core.domain.services.translation_service import TranslationService

TRANSLATIONS = TranslationService()._translations

logger = logging.getLogger('animetix')

def log_timing(func_name, start_time):
    duration = (time.time() - start_time) * 1000
    logger.info(f"Performance: {func_name} took {duration:.2f}ms", extra={'duration_ms': duration})

# --- SETTINGS & CONSTANTS ---
DIFFICULTY_SETTINGS = {
    'Anime': {'Easy': 1000, 'Normal': 500, 'Hard': 200, 'Impossible': 50},
    'Manga': {'Easy': 800, 'Normal': 400, 'Hard': 150, 'Impossible': 30},
    'Character': {'Easy': 500, 'Normal': 250, 'Hard': 100, 'Impossible': 20}
}

# --- 1. SPECIALIZED INFRASTRUCTURE SERVICES ---

class MediaCatalogService:
    """Manages data persistence, searching, and synchronization."""
    def __init__(self):
        container = get_container()
        self.repository = container.repository
        self.sql_repository = container.django_repository
        self.sync_service = container.sync_service
        self.game_service = container.game_service

    def load_catalog(self, media_type):
        catalog = self.game_service.get_catalog(media_type)
        if not catalog:
            raise CatalogNotFoundError(media_type)
        return catalog

    def get_media_item(self, media_type, external_id):
        item = self.sql_repository.get_media_item(media_type, external_id)
        if item: return item
        try:
            catalog = self.load_catalog(media_type)
            return catalog['id_to_full_data'].get(str(external_id))
        except CatalogNotFoundError:
            return None

    def search_items(self, query, media_type=None, limit=10):
        return self.sql_repository.search_media_items(query, media_type, limit)

# --- 2. THE COMPOSITE SERVICE (Facade) ---

class AnimetixService:
    """Facade for the refactored specialized services to maintain backward compatibility."""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnimetixService, cls).__new__(cls)
            container = get_container()
            
            # Using DI Container for all components
            cls._instance.catalog_service = MediaCatalogService()
            
            # Legacy pointers (mapping to container)
            cls._instance.repository = container.repository
            cls._instance.sql_repository = container.django_repository
            cls._instance.game_service = container.game_service
            cls._instance.llm_service = container.llm_service
            cls._instance.vision_service = container.vision_service
            cls._instance.rag_service = container.rag_service
            cls._instance.inference_adapter = container.inference_engine
            cls._instance.sync_service = container.sync_service
            
            # Creative Modes Pointers
            cls._instance.video_quest_service = container.video_quest_service
            cls._instance.studio_transform_service = container.studio_transform_service
            cls._instance.manga_flow_service = container.manga_flow_service
            cls._instance.soundscape_service = container.soundscape_service
            cls._instance.spatial_computing_service = container.spatial_computing_service
            
            # Robustness & Security Pointers
            cls._instance.guardrail_service = container.guardrail_service
            cls._instance.red_teaming_agent = container.red_teaming_agent
            
            # Modern Agentic & Multimodal Services
            cls._instance.orchestrator = container.orchestrator
            cls._instance.cross_modal_search = container.cross_modal_search
            cls._instance.reasoning_agent = container.reasoning_agent
            cls._instance.vlm_indexing = container.vlm_indexing
            
            # Spatial Audio & Voice
            cls._instance.voice_cloning_service = container.voice_cloning_service
            cls._instance.native_speech_llm_service = container.native_speech_llm_service
            
            # RL & Self-Play
            cls._instance.akinetix_rl_service = container.akinetix_rl_service
            cls._instance.self_play_debate_service = container.self_play_debate_service
            
            cls._instance.vision_quest_service = container.vision_quest_service
            cls._instance.emoji_service = container.emoji_service
            cls._instance.paradox_service = container.paradox_service
            cls._instance.animinator_service = container.animinator_service
            cls._instance.akinetix_service = container.akinetix_service
            cls._instance.achievement_listener = container.achievement_listener
            
            cls._instance.translation_service = container.translation_service
            
        return cls._instance

    def load_data(self, media_type): 
        try:
            return self.catalog_service.load_catalog(media_type)
        except CatalogNotFoundError:
            logger.warning(f"Catalog for {media_type} not found.")
            return None

    def get_media_item(self, media_type, external_id): return self.catalog_service.get_media_item(media_type, external_id)
    def search_items(self, query, media_type=None, limit=10): return self.catalog_service.search_items(query, media_type, limit)

    @property
    def translations(self): return self.translation_service._translations

    def get_nearest_neighbors(self, media_type, item_id, count=5):
        return self.game_service.find_similar_items(media_type, item_id, count=count)

    def calculate_raw_similarity(self, media_type, secret_title, guess_title, data):
        return self.game_service.calculate_raw_similarity(media_type, secret_title, guess_title, data)

    def get_status(self) -> dict:
        return self.inference_adapter.health_check()

# --- 3. AGENTIC AI SERVICE (ReAct Pattern) ---
class LangChainService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LangChainService, cls).__new__(cls)
            cls._instance.llm = get_container().llm_service
        return cls._instance

    def _safe_json_parse(self, text, default_reasoning="Analyse Indisponible", default_scenario="..."):
        if not text: return {"reasoning": default_reasoning, "scenario": default_scenario}
        try:
            if '{' in text and '}' in text:
                clean_json = text[text.find('{'):text.rfind('}')+1]
                parsed = orjson.loads(clean_json)
                return {"reasoning": parsed.get('reasoning', default_reasoning), "scenario": parsed.get('scenario', default_scenario)}
        except Exception as e:
            logger.debug(f"JSON Parse Error in LangChain: {e}")
        return {"reasoning": default_reasoning, "scenario": text}

    def generate_scenario_advanced(self, media_type, item_A, item_B, language):
        try:
            label_A, label_B = (item_A.get('title') or item_A.get('name') or "A"), (item_B.get('title') or item_B.get('name') or "B")
            start = time.time()
            res_text = self.llm.generate_fusion_scenario(media_type, label_A, label_B, language)
            log_timing("generate_fusion_scenario", start)
            return self._safe_json_parse(res_text)
        except Exception as e:
            raise InferenceError(f"Failed to generate scenario: {e}")

    def generate_paradox_logic(self, media_type, item_A, item_B, item_I, language):
        try:
            label_A, label_B, label_I = (item_A.get('title') or item_A.get('name')), (item_B.get('title') or item_B.get('name')), (item_I.get('title') or item_I.get('name'))
            res_text = self.llm.generate_paradox_explanation(media_type, label_A, label_B, label_I)
            return self._safe_json_parse(res_text)
        except Exception as e:
            logger.error(f"Paradox Generation Error: {e}")
            return {"reasoning": "Error", "scenario": "L'IA n'a pas pu générer l'explication."}

    def generate_undercover_clue(self, media_type, item_A, item_B, language): 
        try:
            return self.llm.generate_undercover_clue(media_type, item_A, item_B) or "Mystère..."
        except Exception: return "Mystère..."
        
    def generate_emojis(self, media_type, title, description): 
        try:
            return self.llm.generate_emojis(media_type, title, description) or "❓❓❓"
        except Exception: return "❓❓❓"
        
    def ask_oracle(self, media_type, title, data, question): 
        try:
            return self.llm.ask_oracle(media_type, title, question) or "Je ne peux pas répondre..."
        except Exception: return "Je ne peux pas répondre..."
        
    def propose_next_question(self, media_type, history, candidates): 
        try:
            return self.llm.propose_next_question(media_type, history, candidates) or "Es-tu un héros ?"
        except Exception: return "Es-tu un héros ?"

    def calculate_visual_similarity(self, query, secret_id, media_type):
        brain_url = os.getenv("BRAIN_API_URL", "")
        if not brain_url: return 0.0
        try:
            res = requests.post(f"{brain_url}/similarity/visual", json={"query": query, "item_id": secret_id, "media_type": media_type}, timeout=10)
            if res.status_code == 200: return res.json().get("score", 0.0)
        except Exception as e:
            logger.error(f"Visual Similarity API Error: {e}")
        return 0.0

    def generate_fusion_image(self, prompt: str) -> str:
        brain_url = os.getenv("BRAIN_API_URL", "")
        if not brain_url: return ""
        try:
            res = requests.post(f"{brain_url}/generate/image", json={"prompt": prompt}, timeout=60)
            if res.status_code == 200: return res.json().get("image_url", "")
        except Exception as e:
            logger.error(f"Image Generation API Error: {e}")
        return ""

# --- 4. COORDINATION SERVICES ---

class BlindTestService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BlindTestService, cls).__new__(cls)
            cls._instance.domain_service = get_container().blind_test_service
        return cls._instance
    def get_random_theme(self, theme_type=None): return self.domain_service.get_random_theme(theme_type)
    def get_daily_theme(self, date_obj): return self.domain_service.get_daily_theme(date_obj)

class CoverTestService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CoverTestService, cls).__new__(cls)
            cls._instance.domain_service = get_container().cover_test_service
        return cls._instance
    def get_random_cover(self, locale=None): return self.domain_service.get_random_cover(locale)
    def get_daily_cover(self, date_obj): return self.domain_service.get_daily_cover(date_obj)

def check_achievements(user, action_type, context=None):
    from core.domain.entities.achievement import GameEvent
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    
    container = get_container()
    context = context or {}
    event = GameEvent(
        user_id=user.id, game_mode=context.get('game_mode', 'unknown'), media_type=context.get('media_type', 'unknown'),
        was_won=(action_type == 'win'), is_daily=context.get('is_daily', False), is_ranked=context.get('is_ranked', False),
        attempts=context.get('attempts', 0), streak=user.profile.current_streak,
        total_wins=user.profile.total_wins, total_games=user.profile.total_games, item_rarity=context.get('item_rarity', 'Common')
    )
    
    newly_unlocked = container.achievement_listener.on_game_finished(event)
    
    # --- NOTIFICATION TEMPS RÉEL (WebSockets) ---
    if newly_unlocked:
        channel_layer = get_channel_layer()
        for ach in newly_unlocked:
            async_to_sync(channel_layer.group_send)(
                f"user_notifications_{user.id}",
                {
                    "type": "send_notification",
                    "data": {
                        "type": "achievement_unlocked",
                        "achievement": {
                            "name": ach.name,
                            "icon": ach.icon,
                            "xp": ach.xp_reward
                        }
                    }
                }
            )
            
    return newly_unlocked
