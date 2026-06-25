import logging
import random
from typing import Dict, List, Optional

from .llm_service import LLMService

logger = logging.getLogger("animetix.emoji")


class EmojiDomainService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def select_secret(self, catalog: Dict) -> Optional[str]:
        """Sélectionne un titre aléatoire pour le défi Emoji."""
        valid_choices = [
            t
            for t in catalog.get("titles", [])
            if t in catalog.get("title_to_full_data", {})
        ][:500]
        if not valid_choices:
            return None
        return random.choice(valid_choices)

    def generate_emojis_stream(self, media_type: str, title: str, description: str):
        """Version streaming de la génération d'emojis avec Thought Steps."""
        yield {"type": "thought", "content": f"Analyse du synopsis de {title}..."}

        # Simulation d'étapes de réflexion pour l'UX
        import time  # noqa: E402

        yield {
            "type": "thought",
            "content": "Identification des thèmes clés et des objets iconiques...",
        }
        time.sleep(0.5)
        yield {
            "type": "thought",
            "content": "Traduction sémantique en symboles universels...",
        }

        prompt, system = self.llm_service.prompt_manager.get_prompt(
            "emoji_generation", title=title, description=description[:1000]
        )

        full_response = ""
        for token in self.llm_service.inference_engine.stream_generate(
            prompt, system_prompt=system
        ):
            full_response += token.text
            # Note: on ne stream pas les tokens un par un ici car on veut la liste finale,
            # mais on pourrait si on voulait un effet machine à écrire sur les emojis.

        # Extraction finale
        emojis = self._parse_emojis(full_response)
        yield {"type": "result", "content": emojis}

    async def agenerate_emojis_stream(
        self, media_type: str, title: str, description: str
    ):
        """Variante async de generate_emojis_stream (consomme astream_generate)."""
        import asyncio  # noqa: E402

        yield {"type": "thought", "content": f"Analyse du synopsis de {title}..."}
        yield {
            "type": "thought",
            "content": "Identification des thèmes clés et des objets iconiques...",
        }
        await asyncio.sleep(0.5)
        yield {
            "type": "thought",
            "content": "Traduction sémantique en symboles universels...",
        }

        prompt, system = self.llm_service.prompt_manager.get_prompt(
            "emoji_generation", title=title, description=description[:1000]
        )

        full_response = ""
        async for token in self.llm_service.inference_engine.astream_generate(
            prompt, system_prompt=system
        ):
            full_response += token.text

        emojis = self._parse_emojis(full_response)
        yield {"type": "result", "content": emojis}

    def generate_emojis(
        self, media_type: str, title: str, description: str
    ) -> List[str] | str:
        """Génère la suite d'emojis pour une œuvre donnée avec robustesse.

        Retourne la chaîne d'emojis brute du LLM si elle est non vide, sinon une
        liste de repli ``["❓", "❓", "❓"]`` — d'où le type de retour ``List[str] | str``.
        (La variante streaming ``generate_emojis_stream`` parse, elle, en ``List[str]``.)
        """
        try:
            res = self.llm_service.generate_emojis(media_type, title, description)
            return res if res else ["❓", "❓", "❓"]
        except Exception as e:
            logger.warning(f"Emoji generation failed for '{title}': {e}")
            return ["❓", "❓", "❓"]

    def _parse_emojis(self, text: str) -> List[str]:
        """Extrait les emojis d'une chaîne de texte LLM."""
        if not text:
            return ["❓"]
        # On garde uniquement les caractères emoji
        import emoji  # noqa: E402

        found = [c for c in text if emoji.is_emoji(c)]
        return found if found else ["❓"]
