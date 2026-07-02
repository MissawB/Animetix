import ast
import logging
import random
from typing import Dict, List, Optional

from .llm_service import LLMService

logger = logging.getLogger("animetix.emoji")

# Lexical genre/tag → emoji fallback used ONLY when a title has no precomputed
# sequence (cf. pipeline/games/build_emoji_sequences.py). Genre-ish first (vaguer).
_FALLBACK_EMOJI = {
    "action": "💥",
    "adventure": "🗺️",
    "comedy": "😂",
    "drama": "🎭",
    "fantasy": "✨",
    "horror": "👻",
    "romance": "❤️",
    "sci-fi": "🚀",
    "science fiction": "🚀",
    "mystery": "🕵️",
    "supernatural": "✨",
    "sport": "🏆",
    "music": "🎵",
    "mecha": "🤖",
    "magic": "🪄",
    "school": "🏫",
    "demon": "👹",
    "vampire": "🧛",
    "military": "⚔️",
    "war": "⚔️",
    "space": "🌌",
    "psychological": "🧠",
    "thriller": "🔪",
    "historical": "🏯",
    "samurai": "🗡️",
    "pirate": "🏴‍☠️",
    "police": "🚔",
    "superhero": "🦸",
    "isekai": "🌀",
    "cooking": "🍜",
    "idol": "🎤",
    "slice of life": "🌸",
    "sword": "⚔️",
    "gore": "🩸",
    "tragedy": "😭",
    "dragon": "🐉",
    "zombie": "🧟",
    "robot": "🤖",
    "monster": "👹",
    "ghost": "👻",
    "detective": "🕵️",
}


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = ast.literal_eval(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except (ValueError, SyntaxError):
            return [value]
    return []


class EmojiDomainService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    # ── CPU emoji sequence (no LLM / no GPU) ───────────────────────────────
    def build_sequence(self, sequences: Dict, media_type: str, item: Dict) -> List[str]:
        """Vague→obvious emoji sequence for an item: the precomputed one if
        available, else a lexical genre/tag fallback. Never calls an LLM."""
        seq = (sequences or {}).get(media_type, {}).get(str(item.get("id")))
        if seq:
            return list(seq)
        return self._fallback_sequence(item)

    def _fallback_sequence(self, item: Dict) -> List[str]:
        words = [str(g).lower() for g in _as_list(item.get("genres"))]
        words += [str(t).lower() for t in _as_list(item.get("tags"))[:10]]
        picked, seen = [], set()
        for w in words:
            for key, emo in _FALLBACK_EMOJI.items():
                if key in w and emo not in seen:
                    seen.add(emo)
                    picked.append(emo)
                    break
            if len(picked) >= 5:
                break
        return picked or ["❓", "❓", "❓"]

    def select_secret(self, catalog: Dict, limit: int = 500) -> Optional[str]:
        """Sélectionne un titre aléatoire dans le pool de popularité `limit`.

        Le catalogue est trié par popularité décroissante : un `limit` petit ne
        garde que les œuvres les plus connues (facile), un `limit` grand ouvre
        aux pépites obscures (difficile).
        """
        valid_choices = [
            t
            for t in catalog.get("titles", [])
            if t in catalog.get("title_to_full_data", {})
        ][: max(1, limit)]
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
