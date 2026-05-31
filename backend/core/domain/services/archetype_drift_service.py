import logging
from typing import Dict, List, Any
from ..entities.personalization import VisualConfig, ARCHETYPE_VISUAL_MAP

logger = logging.getLogger('animetix.personalization.drift')

class ArchetypeDriftService:
    def __init__(self, feedback_port, memory_service, repository):
        self.feedback_port = feedback_port
        self.memory_service = memory_service
        self.repository = repository

    def calculate_drift(self, user_id: int, user_settings: Dict[str, Any] = None) -> VisualConfig:
        # 0. Initial Default or Manual Mode
        user_settings = user_settings or {}
        mode = user_settings.get("mode", "auto")
        intensity_mult = user_settings.get("intensity_multiplier", 1.0)
        feature_toggles = user_settings.get("features", {"aura": True, "font": True, "accent": True})

        if mode == "manual":
            dominant = user_settings.get("manual_archetype", "shonen_hero")
            vibe = ARCHETYPE_VISUAL_MAP.get(dominant, {})
            return VisualConfig(
                archetype_id=dominant,
                primary_accent=vibe.get("primary_accent", "#FD7706") if feature_toggles.get("accent", True) else "#FD7706",
                aura_type=vibe.get("aura_type", "none") if feature_toggles.get("aura", True) else "none",
                aura_intensity=intensity_mult,
                font_vibe=vibe.get("font_vibe", "default") if feature_toggles.get("font", True) else "default"
            )

        # Default fallback if auto mode fails
        default_config = VisualConfig(
            archetype_id="default",
            primary_accent="#FD7706",
            aura_type="none",
            aura_intensity=0.0,
            font_vibe="default"
        )
        
        if not user_id: return default_config

        scores = {archetype: 0.0 for archetype in ARCHETYPE_VISUAL_MAP.keys()}
        
        # 1. Fetch Feedback signals
        feedbacks = self.feedback_port.get_user_feedback(user_id)
        for fb in feedbacks:
            if fb.get("is_positive"):
                context = (fb.get("input_context", "") + " " + fb.get("output_text", "")).lower()
                for arch in scores.keys():
                    if arch in context:
                        scores[arch] += 1.0

        # 2. Fetch Gameplay signals
        gameplay = self.repository.get_user_gameplay_history(user_id)
        for session in gameplay:
            target = session.get("target", "").lower()
            for arch in scores.keys():
                if arch in target:
                    scores[arch] += 1.0

        # 3. Fetch Creative signals
        creative = self.repository.get_user_creative_history(user_id)
        for fusion in creative:
            art_style = fusion.get("art_style", "").lower()
            for arch in scores.keys():
                if arch in art_style:
                    scores[arch] += 1.0

        # 4. Fetch Semantic Memories (The missing deep signal)
        memories = self.memory_service.get_user_memories(user_id)
        for summary in memories:
            summary_low = summary.lower()
            for arch in scores.keys():
                if arch in summary_low:
                    scores[arch] += 1.5  # Memories have high weight

        # 5. Select dominant archetype
        total_score = sum(scores.values())
        if total_score == 0:
            return default_config
            
        dominant = max(scores, key=scores.get)
        vibe = ARCHETYPE_VISUAL_MAP.get(dominant, {})
        
        # Normalize intensity (max 1.0) and apply multiplier
        intensity = min(1.0, (scores[dominant] / (total_score if total_score > 0 else 1)) * intensity_mult)
        
        return VisualConfig(
            archetype_id=dominant,
            primary_accent=vibe.get("primary_accent", "#FD7706") if feature_toggles.get("accent", True) else "#FD7706",
            aura_type=vibe.get("aura_type", "none") if feature_toggles.get("aura", True) else "none",
            aura_intensity=intensity,
            font_vibe=vibe.get("font_vibe", "default") if feature_toggles.get("font", True) else "default"
        )
