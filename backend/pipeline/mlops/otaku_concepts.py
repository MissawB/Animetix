# -*- coding: utf-8 -*-
"""
Dictionnaire exhaustif de concepts méta de la culture Otaku, Anime, Manga, production et fan-culture.
Ce module sert à enrichir le jeu de données pour le fine-tuning du modèle expert.
"""

import json
import os

_JSON_PATH = os.path.join(os.path.dirname(__file__), "otaku_concepts.json")
try:
    with open(_JSON_PATH, "r", encoding="utf-8") as f:
        OTAKU_VOCABULARY = json.load(f)
except Exception as e:
    # Fallback to empty dict to prevent complete failure if JSON is missing or corrupt
    import logging

    logging.getLogger("animetix.otaku_concepts").error(
        f"Failed to load otaku_concepts.json: {e}"
    )
    OTAKU_VOCABULARY = {}

# --- VALIDATION TECHNIQUE DU NOMBRE DE TERMES (457 STRICTS) ---
assert (
    len(OTAKU_VOCABULARY) >= 457
), f"Le dictionnaire contient seulement {len(OTAKU_VOCABULARY)} termes uniques. Complétez pour atteindre 457."  # noqa: S101
