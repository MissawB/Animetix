import random
from typing import Dict, Optional, List, Tuple
from .llm_service import LLMService

class AniminatorDomainService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def select_secret(self, catalog: Dict) -> Optional[str]:
        """Sélectionne un titre aléatoire pour l'Oracle."""
        valid = [t for t in catalog.get('titles', []) if t in catalog.get('title_to_full_data', {})]
        if not valid:
            return None
        return random.choice(valid[:300])

    def ask_oracle(self, media_type: str, title: str, full_data: Dict, question: str) -> str:
        """Pose une question à l'Oracle (IA incarnant l'œuvre)."""
        return self.llm_service.ask_oracle(media_type, title, question)

    def check_guess(self, guess: str, secret: str) -> bool:
        """Vérifie si le guess correspond au titre secret."""
        return guess.strip().lower() == secret.strip().lower()
