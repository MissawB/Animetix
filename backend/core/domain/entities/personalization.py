from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal

class VisualConfig(BaseModel):
    archetype_id: str
    primary_accent: str
    aura_type: Literal["none", "fire", "electric", "shadow", "sparkles"]
    aura_intensity: float = Field(ge=0.0, le=1.0)
    font_vibe: Literal["default", "manga", "brush"]

class ArchetypeScore(BaseModel):
    scores: Dict[str, float]  # Map archetype name to current intensity

ARCHETYPE_VISUAL_MAP = {
    "shonen_hero": {
        "primary_accent": "#FF4500",
        "aura_type": "fire",
        "font_vibe": "brush"
    },
    "seinen_mystery": {
        "primary_accent": "#2F4F4F",
        "aura_type": "shadow",
        "font_vibe": "manga"
    },
    "cyberpunk": {
        "primary_accent": "#00FFFF",
        "aura_type": "electric",
        "font_vibe": "default"
    }
}
