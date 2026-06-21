# -*- coding: utf-8 -*-
"""Chemins de fichiers partagés du compilateur de dataset de fine-tuning.

Centralise `BASE_DIR` et les chemins des bases de données / sorties, afin que la
façade `finetuning_dataset.py` et les sous-modules (`paraphrase`, …) partagent
les mêmes constantes sans duplication.
"""

import os

from dotenv import load_dotenv

# backend/pipeline/mlops/ft_dataset/paths.py -> 5 niveaux au-dessus = racine projet
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
load_dotenv(os.path.join(BASE_DIR, ".env"))

ANIME_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_animes.json")
MANGA_DB = os.path.join(BASE_DIR, "data", "processed", "clean_root_mangas.json")
CHAR_DB = os.path.join(BASE_DIR, "data", "processed", "refined_characters.json")
OUTPUT_DATASET = os.path.join(
    BASE_DIR, "data", "mlops", "datasets", "animetix_expert_ft.jsonl"
)
CACHE_FILE = os.path.join(
    BASE_DIR, "data", "mlops", "datasets", "gemini_paraphrase_cache.json"
)
