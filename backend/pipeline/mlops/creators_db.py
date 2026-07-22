# -*- coding: utf-8 -*-
"""
Dictionnaire exhaustif de 100 créateurs, réalisateurs et studios d'animation japonais.
Externalisé sous data/mlops/creators_data.json pour décharger le code source des données brutes.
"""

import json
import os

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_JSON_PATH = os.path.join(_BASE_DIR, "data", "mlops", "creators_data.json")

CREATORS_AND_STUDIOS = {}

if os.path.exists(_JSON_PATH):
    with open(_JSON_PATH, "r", encoding="utf-8") as _f:
        CREATORS_AND_STUDIOS = json.load(_f)
