# -*- coding: utf-8 -*-
"""Nettoyage et normalisation de texte pour le dataset de fine-tuning.

Fonctions sans dépendance sur les bases de données locales ni les settings :
nettoyage HTML, injection de bruit réaliste (fautes/argot/abréviations) et
traduction/filtrage des tags.
"""

import html
import random
import re

random = random.SystemRandom()


def clean_description(text: str) -> str:
    if not text:
        return ""
    # 1. Décoder les entités HTML
    text = html.unescape(text)
    # 2. Supprimer les balises HTML
    text = re.sub(r"</?[a-zA-Z]+(?:\s+[^>]*)?>", " ", text)
    # 3. Supprimer les espaces multiples et les retours à la ligne
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def inject_query_noise(text: str, language: str = "Français") -> str:
    """
    Injecte du bruit réaliste dans une instruction utilisateur pour simuler
    les fautes de frappe, abréviations, argot et absence de ponctuation
    que l'on retrouve en conditions réelles d'utilisation.
    """
    if not text:
        return text

    # --- A. Slang & Abbreviation dictionaries ---
    fr_phrase_replacements = [
        ("s'il te plaît", "stp"),
        ("s'il vous plaît", "svp"),
        ("qu'est-ce que", "keske"),
        ("qu'est ce que", "keske"),
        ("est-ce que", "eske"),
        ("est ce que", "eske"),
        ("chef-d'œuvre", "masterclass"),
        ("chef-d'oeuvres", "masterclass"),
        ("chef d'œuvre", "masterclass"),
        ("chef d'oeuvres", "masterclass"),
    ]
    fr_word_replacements = {
        "quelque": "qq",
        "quelques": "qqs",
        "pourquoi": "pq",
        "avec": "avc",
        "dans": "ds",
        "anime": "anim",
        "animes": "anims",
        "personnage": "perso",
        "personnages": "persos",
        "adoré": "kiffé",
        "aimé": "kiffé",
        "salut": "slt",
        "bonjour": "bjr",
        "c'est-à-dire": "càd",
    }
    en_word_replacements = {
        "what": "wht",
        "you": "u",
        "are": "r",
        "please": "pls",
        "information": "info",
        "background": "bg",
        "character": "char",
        "characters": "chars",
        "favorite": "fav",
        "favorites": "favs",
        "really": "rlly",
        "masterpiece": "banger",
        "masterpieces": "bangers",
        "hello": "hllo",
        "thanks": "thx",
        "about": "abt",
    }

    modified_text = text

    # Apply multi-word phrase replacements first (French only)
    if language != "English":
        for phrase, replacement in fr_phrase_replacements:
            modified_text = re.sub(
                re.escape(phrase), replacement, modified_text, flags=re.IGNORECASE
            )

    # Apply single-word replacements
    word_replacements = (
        en_word_replacements if language == "English" else fr_word_replacements
    )
    words = modified_text.split()
    new_words = []
    for w in words:
        w_clean = re.sub(r"[^\w\'\-àâäéèêëïîôùûüçœæ]", "", w, flags=re.UNICODE).lower()
        if w_clean in word_replacements:
            new_words.append(word_replacements[w_clean])
        else:
            new_words.append(w)
    modified_text = " ".join(new_words)

    # --- B. Formatting laziness (50% probability) ---
    if random.random() < 0.5:
        modified_text = modified_text.lower()
        modified_text = re.sub(r'[?,.!;:\'"]', "", modified_text)

    # --- C. Typo mutations (1 or 2 random words of length >= 4) ---
    words_list = modified_text.split()
    eligible_indices = [i for i, w in enumerate(words_list) if len(w) >= 4]
    if eligible_indices:
        num_typos = random.randint(1, min(2, len(eligible_indices)))
        indices_to_mutate = random.sample(eligible_indices, num_typos)
        for idx in indices_to_mutate:
            w = words_list[idx]
            typo_type = random.choice(["swap", "drop", "duplicate"])
            if typo_type == "swap" and len(w) >= 2:
                pos = random.randint(0, len(w) - 2)
                w_list = list(w)
                w_list[pos], w_list[pos + 1] = w_list[pos + 1], w_list[pos]
                w = "".join(w_list)
            elif typo_type == "drop":
                pos = random.randint(0, len(w) - 1)
                w = w[:pos] + w[pos + 1 :]
            elif typo_type == "duplicate":
                pos = random.randint(0, len(w) - 1)
                w = w[:pos] + w[pos] + w[pos:]
            words_list[idx] = w
        modified_text = " ".join(words_list)

    return modified_text


def clean_tags(tags, language="Français"):
    if not tags:
        return []
    invalid_keywords = [
        "aucune unité",
        "ia n'est disponible",
        "ollama",
        "hf",
        "désolé",
        "sorry",
        "no computational unit",
        "error",
        "pas de description",
        "inconnu",
        "unknown",
    ]
    cleaned = []
    for tag in tags:
        lower_tag = tag.lower()
        if any(kw in lower_tag for kw in invalid_keywords):
            continue
        if language == "English":
            tag_translation = {
                "Shounen": "Shonen",
                "Primarily Teen Cast": "Teen Cast",
                "Male Protagonist": "Male Protagonist",
                "Swordplay": "Swordplay",
            }
        else:
            tag_translation = {
                "Shounen": "Shonen",
                "Vampire": "Vampire",
                "Primarily Teen Cast": "Protagonistes adolescents",
                "Orphan": "Orphelin",
                "Demons": "Démons",
                "Monster Girl": "Fille monstre (Monster Girl)",
                "Male Protagonist": "Protagoniste masculin",
                "Travel": "Voyage",
                "Revenge": "Vengeance",
                "Tragedy": "Tragédie",
                "Swordplay": "Combat au sabre (Swordplay)",
                "Action": "Action",
                "Adventure": "Aventure",
                "Drama": "Drame",
                "Fantasy": "Fantasy",
                "Supernatural": "Surnaturel",
                "Seinen": "Seinen",
                "Slice of Life": "Tranche de vie",
                "Comedy": "Comédie",
                "Romance": "Romance",
                "School": "Milieu scolaire",
                "Sci-Fi": "Science-Fiction",
                "Mecha": "Mécha",
                "Psychological": "Psychologique",
                "Mystery": "Mystère",
                "Thriller": "Thriller",
                "Horror": "Horreur",
                "Historical": "Historique",
                "Military": "Militaire",
                "Magic": "Magie",
                "Sports": "Sport",
                "Music": "Musique",
                "Super Power": "Super-pouvoirs",
                "Martial Arts": "Arts martiaux",
            }
        cleaned.append(tag_translation.get(tag, tag))
    return cleaned
