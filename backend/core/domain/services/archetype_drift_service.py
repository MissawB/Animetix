import logging
from typing import Dict, List, Any
from ..entities.personalization import VisualConfig, ARCHETYPE_VISUAL_MAP

logger = logging.getLogger('animetix.personalization.drift')

class ArchetypeDriftService:
    def __init__(self, feedback_port, memory_service):
        self.feedback_port = feedback_port
        self.memory_service = memory_service
        self.alpha = 0.3  # Inertia factor (0.3 = 30% recent, 70% past)

    def calculate_drift(self, user_id: int) -> VisualConfig:
        # Default fallback
        default_config = VisualConfig(
            archetype_id="default",
            primary_accent="#FD7706",
            aura_type="none",
            aura_intensity=0.0,
            font_vibe="default"
        )
        
        if not user_id: return default_config

        # 1. Fetch signals (mocked logic for brevity, would query DB/Chroma)
        # In real impl, we aggregate AIFeedback, GameplaySession and memories
        # For now, let's assume a simplified scoring
        recent_stats = {"shonen_hero": 0.8, "seinen_mystery": 0.2} 
        
        # 2. Select dominant archetype
        dominant = max(recent_stats, key=recent_stats.get)
        vibe = ARCHETYPE_VISUAL_MAP.get(dominant, {})
        
        return VisualConfig(
            archetype_id=dominant,
            primary_accent=vibe.get("primary_accent", "#FD7706"),
            aura_type=vibe.get("aura_type", "none"),
            aura_intensity=recent_stats[dominant],
            font_vibe=vibe.get("font_vibe", "default")
        )
