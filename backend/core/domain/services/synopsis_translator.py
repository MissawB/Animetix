"""Traduction à la volée d'un synopsis anglais vers un français littéraire (Gemini)."""

import logging
import os

logger = logging.getLogger("animetix.synopsis_translator")

_PROMPT = """Tu es un traducteur et scénariste littéraire expert en japanimation, mangas et culture geek.
Traduis fidèlement, avec style, richesse et de façon fluide le synopsis/description suivant en français.
Conserve le ton mystérieux, dramatique ou d'action de l'œuvre d'origine.
N'ajoute absolument aucun commentaire ou métadonnée, retourne UNIQUEMENT la traduction fluide et propre en français.

Titre de l'œuvre : {title}
Synopsis en anglais :
{english}
"""


class SynopsisTranslator:
    """Best-effort translator. Returns "" on any failure — never raises."""

    def translate_to_fr(self, title: str, english_synopsis: str) -> str:
        if not english_synopsis:
            return ""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.info("GEMINI_API_KEY absent — traduction ignorée.")
            return ""
        try:
            from core.utils.gemini_models import GEMINI_FLASH
            from google import genai

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_FLASH,
                contents=_PROMPT.format(title=title, english=english_synopsis),
            )
            return (response.text or "").strip()
        except Exception:
            logger.exception("Échec de traduction Gemini pour '%s'", title)
            return ""
