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
    },
    "tsundere": {
        "primary_accent": "#FF1493",
        "aura_type": "electric",
        "font_vibe": "manga"
    },
    "kuudere": {
        "primary_accent": "#00BFFF",
        "aura_type": "shadow",
        "font_vibe": "default"
    },
    "yandere": {
        "primary_accent": "#8B0000",
        "aura_type": "shadow",
        "font_vibe": "manga"
    },
    "shonen": {
        "primary_accent": "#FFA500",
        "aura_type": "fire",
        "font_vibe": "brush"
    },
    "seinen": {
        "primary_accent": "#4682B4",
        "aura_type": "shadow",
        "font_vibe": "manga"
    },
    "mahou_shoujo": {
        "primary_accent": "#FF69B4",
        "aura_type": "sparkles",
        "font_vibe": "default"
    },
    "isekai": {
        "primary_accent": "#E0FFFF",
        "aura_type": "sparkles",
        "font_vibe": "default"
    },
    "slice_of_life": {
        "primary_accent": "#90EE90",
        "aura_type": "none",
        "font_vibe": "default"
    },
    "mecha": {
        "primary_accent": "#708090",
        "aura_type": "electric",
        "font_vibe": "default"
    },
    "horror": {
        "primary_accent": "#000000",
        "aura_type": "shadow",
        "font_vibe": "brush"
    },
    "fantasy": {
        "primary_accent": "#DAA520",
        "aura_type": "sparkles",
        "font_vibe": "brush"
    },
    "romance": {
        "primary_accent": "#FFB6C1",
        "aura_type": "sparkles",
        "font_vibe": "default"
    },
    "psychological": {
        "primary_accent": "#4B0082",
        "aura_type": "shadow",
        "font_vibe": "manga"
    },
    "sports": {
        "primary_accent": "#32CD32",
        "aura_type": "fire",
        "font_vibe": "brush"
    }
}
