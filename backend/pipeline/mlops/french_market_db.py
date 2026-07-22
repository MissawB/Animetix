# -*- coding: utf-8 -*-
"""
Base de données du marché français du manga et de l'animation.
Externalisée sous data/mlops/french_market_data.json pour décharger le code source.
"""

import json
import os

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_JSON_PATH = os.path.join(_BASE_DIR, "data", "mlops", "french_market_data.json")

FRENCH_VOICE_ACTORS = {}
FRENCH_MANGA_PUBLISHERS = {}
FRENCH_ANIME_DISTRIBUTORS = {}
FRENCH_MARKET_RELATIONS = []

if os.path.exists(_JSON_PATH):
    with open(_JSON_PATH, "r", encoding="utf-8") as _f:
        _data = json.load(_f)
        FRENCH_VOICE_ACTORS = _data.get("FRENCH_VOICE_ACTORS", {})
        FRENCH_MANGA_PUBLISHERS = _data.get("FRENCH_MANGA_PUBLISHERS", {})
        FRENCH_ANIME_DISTRIBUTORS = _data.get("FRENCH_ANIME_DISTRIBUTORS", {})
        FRENCH_MARKET_RELATIONS = _data.get("FRENCH_MARKET_RELATIONS", [])
