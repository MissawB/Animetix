from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AkinetixQuestion(BaseModel):
    """Represents a question and its answer in the history."""

    q: str
    a: str


class AkinetixGameState(BaseModel):
    """
    Structured state for an Akinetix game session.
    Ensures type safety and validation across domain and adapters.
    """

    history: List[AkinetixQuestion] = Field(default_factory=list)
    current_q: Optional[str] = None
    current_attr: Optional[str] = None
    game_over: bool = False
    ai_guess: Optional[str] = None
    user_target_id: Optional[str] = None
    user_target_name: Optional[str] = None
    probs: List[float] = Field(default_factory=list)
    asked_attrs: List[str] = Field(default_factory=list)
    is_daily: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Legacy compatibility for dictionary-based ports."""
        return self.model_dump()
