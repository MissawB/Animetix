from typing import List, Literal

from pydantic import BaseModel, Field, RootModel


class OfflineGameResult(BaseModel):
    game_mode: Literal[
        "classic",
        "emoji",
        "animinator",
        "paradox",
        "vision_quest",
        "blindtest",
        "covertest",
    ]
    media_type: str = "Anime"
    score: int = Field(..., ge=0, le=100)
    attempts: int = Field(1, ge=1)


class OfflineSyncSchema(RootModel):
    root: List[OfflineGameResult] = Field(..., max_length=50)
