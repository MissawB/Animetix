# -*- coding: utf-8 -*-
"""
Compilateur de jeu de données de préférence DPO / RLHF.
Génère offline des paires (chosen, rejected) à partir du jeu de données SFT.
"""

import os
import json
import random
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("animetix.pipeline.mlops.dpo_dataset_compiler")
logging.basicConfig(level=logging.INFO)

# Tentatives d'importation des bases locales d'entités pour la substitution factuelle
try:
    from creators_db import CREATORS_AND_STUDIOS
except ImportError:
    try:
        from backend.pipeline.mlops.creators_db import CREATORS_AND_STUDIOS
    except ImportError:
        CREATORS_AND_STUDIOS = {}

try:
    from french_market_db import FRENCH_VOICE_ACTORS, FRENCH_MANGA_PUBLISHERS, FRENCH_ANIME_DISTRIBUTORS
except ImportError:
    try:
        from backend.pipeline.mlops.french_market_db import FRENCH_VOICE_ACTORS, FRENCH_MANGA_PUBLISHERS, FRENCH_ANIME_DISTRIBUTORS
    except ImportError:
        FRENCH_VOICE_ACTORS = {}
        FRENCH_MANGA_PUBLISHERS = {}
        FRENCH_ANIME_DISTRIBUTORS = {}

# Listes d'entités par défaut en cas d'échec d'importation
STUDIOS_LIST = list(CREATORS_AND_STUDIOS.keys()) if CREATORS_AND_STUDIOS else [
    "Wit Studio", "Studio Ghibli", "MAPPA", "ufotable", "Madhouse", "Shaft", "Studio Trigger", "Bones", "Sunrise", "Toei Animation"
]

VOICE_ACTORS_LIST = list(FRENCH_VOICE_ACTORS.keys()) if FRENCH_VOICE_ACTORS else [
    "Brigitte Lecordier", "Benoît DuPac", "Alexis Tomassian", "Arthur Pestel", "Patrick Borg", "Eric Legrand", "Philippe Ariotti"
]

PUBLISHERS_LIST = list(FRENCH_MANGA_PUBLISHERS.keys()) if FRENCH_MANGA_PUBLISHERS else [
    "Glénat Manga", "Kana", "Pika Édition", "Kurokawa", "Ki-oon", "Delcourt/Tonkam", "Soleil Manga", "Akata", "Meian"
]

DISTRIBUTORS_LIST = list(FRENCH_ANIME_DISTRIBUTORS.keys()) if FRENCH_ANIME_DISTRIBUTORS else [
    "Crunchyroll France", "ADN", "Netflix France", "Prime Video Channels", "Disney+ France", "Wakanim"
]

POPULAR_TITLES = [
    "One Piece", "Naruto", "Bleach", "Death Note", "Berserk", "Dragon Ball Z", "My Hero Academia",
    "Jujutsu Kaisen", "L'Attaque des Titans", "Attack on Titan", "Neon Genesis Evangelion",
    "Demon Slayer", "GTO", "Fullmetal Alchemist", "Sword Art Online", "Chainsaw Man",
    "Spy x Family", "Hunter x Hunter", "Tokyo Ghoul", "Fairy Tail"
]


def corrupt_fact_substitution(text: str, language: str = "Français") -> str:
    """
    Substitue des entités (studios, doubleurs, éditeurs, titres, années) par d'autres valeurs incorrectes.
    Garantit toujours qu'une modification a lieu (avec repli sur les chiffres ou les mots).
    """
    original_text = text
    modified = False

    # 1. Remplacer les années (ex: 2018 -> 1995)
    years = re.findall(r'\b(19\d\d|20\d\d)\b', text)
    if years:
        for yr in set(years):
            new_yr = str(random.choice([y for y in range(1980, 2027) if str(y) != yr]))
            text = re.sub(rf'\b{yr}\b', new_yr, text)
            modified = True

    # Helper pour remplacer les entités d'une liste
    def replace_from_list(current_text: str, entities: List[str]) -> tuple[str, bool]:
        text_mod = current_text
        found_any = False
        # Trier par longueur décroissante pour éviter d'écraser des sous-chaînes
        sorted_entities = sorted(entities, key=len, reverse=True)
        for ent in sorted_entities:
            # Recherche insensible à la casse avec bordures de mots ou caractères spéciaux
            pattern = rf'\b{re.escape(ent)}\b'
            if re.search(pattern, text_mod, re.IGNORECASE):
                choices = [e for e in entities if e.lower() != ent.lower()]
                if choices:
                    rep = random.choice(choices)
                    text_mod = re.sub(pattern, rep, text_mod, flags=re.IGNORECASE)
                    found_any = True
        return text_mod, found_any

    # Appliquer les substitutions d'entités
    for entity_list in [STUDIOS_LIST, VOICE_ACTORS_LIST, PUBLISHERS_LIST, DISTRIBUTORS_LIST, POPULAR_TITLES]:
        text, is_mod = replace_from_list(text, entity_list)
        if is_mod:
            modified = True

    # 2. Si aucune modification n'a eu lieu, corrompre n'importe quel nombre
    if not modified:
        numbers = re.findall(r'\b\d+\b', text)
        if numbers:
            for num in set(numbers):
                new_num = str(random.choice([n for n in range(1, 101) if str(n) != num]))
                text = re.sub(rf'\b{num}\b', new_num, text)
                modified = True

    # 3. Repli ultime : inverser deux mots de longueur >= 4
    if not modified or text == original_text:
        words = text.split()
        eligible_indices = [i for i, w in enumerate(words) if len(w) >= 4]
        if len(eligible_indices) >= 2:
            idx1, idx2 = random.sample(eligible_indices, 2)
            words[idx1], words[idx2] = words[idx2], words[idx1]
            text = " ".join(words)

    return text


def corrupt_tonal_deviation(text: str, language: str = "Français") -> str:
    """
    Dégrade le ton en injectant du code-switching agressif/slang et en rendant
    la ponctuation absente / le texte en minuscules.
    """
    fr_slang = [
        " c'est trop un banger fr fr",
        " wesh bro",
        " like literally",
        " lmao",
        " c'est kiffant de fou",
        " wesh",
        " genre grave"
    ]
    en_slang = [
        " fr fr",
        " lmao",
        " bro",
        " like, literally",
        " dude",
        " ikr"
    ]

    # Minuscules et suppression de la ponctuation standard
    text = text.lower()
    text = re.sub(r'[?,.!;:\'"]', '', text)

    # Injection de slang
    slangs = en_slang if language == "English" else fr_slang
    # Ajouter 1 ou 2 expressions au hasard
    text += random.choice(slangs)
    if random.random() < 0.5:
        text = random.choice(slangs).strip() + " " + text

    return text.strip()


def corrupt_abrupt_truncation(text: str) -> str:
    """
    Simule une coupure brutale de génération en coupant au milieu du texte.
    """
    if len(text) < 10:
        return text
    
    ratio = random.uniform(0.3, 0.7)
    cut_idx = int(len(text) * ratio)
    truncated = text[:cut_idx].rstrip()
    
    # Nettoyer les ponctuations de fin pour que la coupure soit vraiment abrupte
    truncated = re.sub(r'[.,!?;:\s]+$', '', truncated)
    return truncated


def corrupt_evasive_refusal(text: str, language: str = "Français") -> str:
    """
    Remplace toute la réponse par un refus évasif non-informatif.
    """
    fr_refusals = [
        "Désolé, je ne dispose pas de ces informations pour le moment.",
        "Aucune idée, je ne connais pas ce sujet.",
        "Désolé, je n'ai pas le temps de répondre à ça, cherche sur Google."
    ]
    en_refusals = [
        "Sorry, I don't have this information.",
        "Sorry, I have no idea about this.",
        "I don't know, search on Google."
    ]
    
    refusals = en_refusals if language == "English" else fr_refusals
    return random.choice(refusals)


def compile_dpo_pairs(sft_path: str, output_path: str, limit: int = 2000, seed: int = 42) -> int:
    """
    Lit le dataset SFT, filtre les entrées éligibles, génère les paires
    DPO par corruption équilibrée, et les écrit au format JSONL.
    """
    random.seed(seed)
    
    if not os.path.exists(sft_path):
        logger.error(f"SFT dataset not found at: {sft_path}")
        return 0

    logger.info(f"Reading SFT dataset from {sft_path}...")
    eligible_entries = []
    
    # Mots clés de refus à filtrer
    refusal_keywords = [
        "je ne peux pas", "je ne dispose pas", "désolé",
        "i cannot", "i don't have", "sorry"
    ]

    with open(sft_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                # On ne traite que les dialogues à tour unique simple pour DPO simple
                if "instruction" not in entry or "output" not in entry:
                    continue
                
                output_text = entry["output"]
                instruction_text = entry["instruction"]
                
                # Filtre de longueur
                if len(output_text) < 40:
                    continue
                
                # Filtre de refus
                if any(kw in output_text.lower() for kw in refusal_keywords) or \
                   any(kw in instruction_text.lower() for kw in refusal_keywords):
                    continue
                
                eligible_entries.append(entry)
            except json.JSONDecodeError:
                continue

    total_eligible = len(eligible_entries)
    logger.info(f"Found {total_eligible} eligible SFT entries for DPO conversion.")
    
    if total_eligible == 0:
        return 0

    # Mélanger et limiter
    random.shuffle(eligible_entries)
    selected_entries = eligible_entries[:limit]
    
    compiled_pairs = []
    
    # Les 4 stratégies
    strategies = ["fact", "tone", "truncation", "refusal"]
    
    for idx, entry in enumerate(selected_entries):
        prompt = entry["instruction"]
        chosen = entry["output"]
        lang = entry.get("language", "Français")
        
        # Choix de la stratégie de manière cyclique/équilibrée
        strategy = strategies[idx % len(strategies)]
        
        if strategy == "fact":
            rejected = corrupt_fact_substitution(chosen, lang)
        elif strategy == "tone":
            rejected = corrupt_tonal_deviation(chosen, lang)
        elif strategy == "truncation":
            rejected = corrupt_abrupt_truncation(chosen)
        else:
            rejected = corrupt_evasive_refusal(chosen, lang)
            
        # Par sécurité, si la corruption échoue et renvoie la même chose, utiliser le refus
        if rejected == chosen:
            rejected = corrupt_evasive_refusal(chosen, lang)
            
        compiled_pairs.append({
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected
        })

    # Sauvegarder au format JSONL
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out_f:
        for pair in compiled_pairs:
            out_f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            
    logger.info(f"Successfully compiled {len(compiled_pairs)} DPO pairs saved to {output_path}")
    return len(compiled_pairs)


if __name__ == "__main__":
    # Paramètres via variables d'environnement
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    sft_default = os.path.join(base_dir, "data", "mlops", "datasets", "animetix_expert_ft.jsonl")
    dpo_default = os.path.join(base_dir, "data", "mlops", "datasets", "dpo_train_validated.jsonl")
    
    dpo_size = int(os.getenv("ANIMETIX_DPO_SIZE", "2000"))
    dpo_seed = int(os.getenv("ANIMETIX_DPO_SEED", "42"))
    
    compile_dpo_pairs(sft_default, dpo_default, limit=dpo_size, seed=dpo_seed)
