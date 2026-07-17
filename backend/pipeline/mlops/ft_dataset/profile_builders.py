# -*- coding: utf-8 -*-
"""Constructeurs de texte naturel (FR/EN) pour les profils d'animes/mangas et
les biographies de personnages, plus les tables de synonymes/surnoms.

Constantes en lecture seule (`MULTI_TITLE_MAP`, `CHARACTER_NICKNAMES`) et
fonctions pures dépendant uniquement de `clean_tags`.
"""

import random
from typing import List

from .text_cleaning import clean_tags

random = random.SystemRandom()  # type: ignore[assignment]  # intentional secure-RNG module shadowing

MULTI_TITLE_MAP = {
    "Shingeki no Kyojin": ["L'Attaque des Titans", "Attack on Titan", "SnK"],
    "Kimetsu no Yaiba": [
        "Demon Slayer",
        "Demon Slayer: Kimetsu no Yaiba",
        "Pourfendeur de démons",
    ],
    "Boku no Hero Academia": ["My Hero Academia", "MHA"],
    "Jujutsu Kaisen": ["JJK"],
    "One Piece": ["OP"],
    "Naruto Shippuuden": ["Naruto Shippuden"],
    "Hagane no Renkinjutsushi: FULLMETAL ALCHEMIST": [
        "Fullmetal Alchemist: Brotherhood",
        "FMAB",
    ],
    "Steins;Gate": ["Steins Gate"],
    "Kiseijuu: Sei no Kakuritsu": ["Parasyte", "Parasyte -the maxim-"],
    "Sen to Chihiro no Kamikakushi": ["Le Voyage de Chihiro", "Spirited Away"],
    "Mononoke Hime": ["Princesse Mononoké", "Princess Mononoke"],
    "Tonari no Totoro": ["Mon Voisin Totoro", "My Neighbor Totoro"],
    "Howl no Ugoku Shiro": ["Le Château ambulant", "Howl's Moving Castle"],
    "Kaze no Tani no Nausicaa": [
        "Nausicaä de la Vallée du Vent",
        "Nausicaa of the Valley of the Wind",
    ],
    "Kimi no Na wa.": ["Your Name.", "Your Name"],
    "Koe no Katachi": ["A Silent Voice"],
    "Shin Seiki Evangelion": ["Neon Genesis Evangelion", "Evangelion", "NGE"],
    "Tengen Toppa Gurren Lagann": ["Gurren Lagann"],
    "Hunter x Hunter (2011)": ["HxH (2011)", "Hunter x Hunter"],
    "Code Geass: Hangyaku no Lelouch": ["Code Geass", "Lelouch of the Rebellion"],
    "One Punch Man": ["OPM"],
    "Yakusoku no Neverland": ["The Promised Neverland"],
    "Shigatsu wa Kimi no Uso": ["Your Lie in April"],
    "Seishun Buta Yarou wa Bunny Girl Senpai no Yume wo Minai": ["Bunny Girl Senpai"],
    "Kaguya-sama wa Kokurasetai: Tensaitachi no Renai Zounousen": [
        "Kaguya-sama: Love is War",
        "Kaguya-sama",
    ],
    "Re:Zero kara Hajimeru Isekai Seikatsu": ["Re:Zero", "Re Zero"],
    "Fate/stay night [Unlimited Blade Works]": ["Fate Unlimited Blade Works", "UBW"],
    "Violet Evergarden": ["Violet Evergarden"],
    "Tokyo Ghoul": ["TG"],
    "No Game No Life": ["NGNL"],
    "Boku dake ga Inai Machi": ["ERASED"],
    "Ansatsu Kyoushitsu": ["Assassination Classroom"],
    "Mahou Shoujo Madoka★Magica": ["Puella Magi Madoka Magica", "Madoka Magica"],
}

CHARACTER_NICKNAMES = {
    "Levi": ["Livaï", "Caporal Levi", "Rivaille", "Levi Ackerman"],
    "Luffy": ["Monkey D. Luffy", "Chapeau de Paille", "Mugiwara"],
    "Goku": ["Son Goku", "Kakarot", "Sangoku"],
    "Naruto": ["Naruto Uzumaki", "Uzuman", "Héros de Konoha"],
    "Sasuke": ["Sasuke Uchiha", "Sasuke Uchiwa"],
    "Zoro": ["Roronoa Zoro", "Zoro le chasseur de pirates"],
    "Edward Elric": ["Ed", "Le Fullmetal Alchemist", "L'Alchimiste d'État d'Acier"],
    "Light Yagami": ["Kira", "Light"],
    "Lelouch Lamperouge": ["Lelouch vi Britannia", "Zero"],
    "Guts": ["Le Guerrier Noir", "Gatsu"],
    "Killua Zoldyck": ["Killua"],
    "Mikasa Ackerman": ["Mikasa"],
    "Nezuko Kamado": ["Nezuko"],
    "Tanjiro Kamado": ["Tanjiro"],
    "Ken Kaneki": ["Kaneki le cache-œil", "Kaneki Ken"],
    "Saitama": ["Le Chauve au Cape", "Saitama-sensei"],
    "Saber": ["Artoria Pendragon", "Roi des Chevaliers"],
    "Rin Tohsaka": ["Rin"],
    "Kurisu Makise": ["Christina", "Kurigohan and Kamehameha"],
}


def get_synonyms_string(title, language="Français"):
    if title in MULTI_TITLE_MAP:
        names = [f"'{n}'" for n in MULTI_TITLE_MAP[title]]
        if language == "English":
            return f" (also known as {', '.join(names)})"
        return f" (également connu sous les noms de {', '.join(names)})"
    return ""


def get_character_synonyms_string(name, language="Français"):
    if name in CHARACTER_NICKNAMES:
        names = [f"'{n}'" for n in CHARACTER_NICKNAMES[name]]
        if language == "English":
            return f" (also known as {', '.join(names)})"
        return f" (connu aussi comme {', '.join(names)})"
    return ""


def get_display_title(title):
    if title in MULTI_TITLE_MAP:
        return random.choice([title] + MULTI_TITLE_MAP[title])
    return title


def get_display_character(name):
    if name in CHARACTER_NICKNAMES:
        return random.choice([name] + CHARACTER_NICKNAMES[name])
    return name


_FR_ANIME_LEADINS = [
    "L'anime '{title}'{syns} est sorti en {year} et relève des genres {genres}.",
    "'{title}'{syns} ({year}) est un anime des genres {genres}.",
    "Sorti en {year}, l'anime '{title}'{syns} appartient aux genres {genres}.",
    "'{title}'{syns} est un anime de {year}, classé dans {genres}.",
]


def make_french_anime_profile(
    title: str, genres: List[str], studios: List[str], tags: List[str], year: int
) -> str:
    cleaned_genres = clean_tags(genres)
    cleaned_tags = clean_tags(tags)
    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "genres variés"
    studios_str = ", ".join(studios) if studios else "un studio non précisé"
    tags_str = ", ".join(cleaned_tags[:5]) if cleaned_tags else ""
    syns = get_synonyms_string(title)
    lead = random.choice(_FR_ANIME_LEADINS).format(
        title=title, syns=syns, year=year, genres=genres_str
    )
    parts = [lead, f"Il a été produit par {studios_str}."]
    if tags_str:
        parts.append(f"Ses thématiques incluent : {tags_str}.")
    return " ".join(parts)


_FR_MANGA_LEADINS = [
    "'{title}'{syns} est un manga des genres {genres}.",
    "Le manga '{title}'{syns} relève des genres {genres}.",
    "'{title}'{syns} est un manga classé dans {genres}.",
]


def make_french_manga_profile(title: str, genres: List[str], tags: List[str]) -> str:
    cleaned_genres = clean_tags(genres)
    cleaned_tags = clean_tags(tags)
    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "genres variés"
    tags_str = ", ".join(cleaned_tags[:5]) if cleaned_tags else ""
    syns = get_synonyms_string(title)
    lead = random.choice(_FR_MANGA_LEADINS).format(
        title=title, syns=syns, genres=genres_str
    )
    parts = [lead]
    if tags_str:
        parts.append(f"Ses thématiques incluent : {tags_str}.")
    return " ".join(parts)


_FR_CHAR_LEADINS = [
    "{name}{syns} est un personnage de l'œuvre '{origin}'{osyns}.",
    "{name}{syns} apparaît dans '{origin}'{osyns}.",
    "Dans '{origin}'{osyns}, on trouve le personnage de {name}{syns}.",
    "{name}{syns} fait partie de l'univers de '{origin}'{osyns}.",
    "Voici {name}{syns}, issu de '{origin}'{osyns}.",
]


def make_french_character_bio(name, origin, orgs):
    org_mapping = {
        "Survey Corps": "le Bataillon d'exploration",
        "Straw Hat Pirates": "l'Équipage du Chapeau de paille",
        "Gotei 13": "le Gotei 13",
        "Akatsuki": "l'organisation criminelle Akatsuki",
        "League of Villains": "la Ligue des Vilains",
        "U.A. High School": "le lycée Yuei (U.A. High School)",
        "Hunter Association": "l'Association des Hunters",
        "Jujutsu High": "l'école d'exorcisme de Tokyo (Jujutsu High)",
        "Demon Slayer Corps": "l'Armée des pourfendeurs de démons",
        "Special Operations Squad": "l'Escouade tactique de Levi",
        "Black Bulls": "la compagnie du Taureau Noir (Black Bulls)",
    }
    french_orgs = [org_mapping.get(o, o) for o in orgs]

    syns = get_character_synonyms_string(name)
    origin_syns = get_synonyms_string(origin)
    lead = random.choice(_FR_CHAR_LEADINS).format(
        name=name, syns=syns, origin=origin, osyns=origin_syns
    )
    parts = [lead]
    if french_orgs:
        org_str = " et ".join(french_orgs)
        parts.append(f"Il est notamment associé à {org_str}.")
    return " ".join(parts)


_EN_ANIME_LEADINS = [
    "'{title}'{syns} is a {year} anime in the {genres} genre(s).",
    "'{title}'{syns} ({year}) is an anime spanning {genres}.",
    "The anime '{title}'{syns}, released in {year}, falls under {genres}.",
    "Released in {year}, the anime '{title}'{syns} covers {genres}.",
]


def make_english_anime_profile(
    title: str,
    genres: List[str],
    studios: List[str],
    tags: List[str],
    year: int,
    description: str = "",
) -> str:
    cleaned_genres = clean_tags(genres, "English")
    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "various genres"
    studios_str = ", ".join(studios) if studios else "an unspecified studio"
    syns = get_synonyms_string(title, "English")
    lead = random.choice(_EN_ANIME_LEADINS).format(
        title=title, syns=syns, year=year, genres=genres_str
    )
    parts = [lead, f"It was produced by {studios_str}."]
    body = (description or "").strip()
    if body:
        parts.append(body)
    return " ".join(parts)


_EN_MANGA_LEADINS = [
    "'{title}'{syns} is a manga in the {genres} genre(s).",
    "The manga '{title}'{syns} spans {genres}.",
    "'{title}'{syns} is a manga covering {genres}.",
]


def make_english_manga_profile(
    title: str, genres: List[str], tags: List[str], description: str = ""
) -> str:
    cleaned_genres = clean_tags(genres, "English")
    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "various genres"
    syns = get_synonyms_string(title, "English")
    lead = random.choice(_EN_MANGA_LEADINS).format(
        title=title, syns=syns, genres=genres_str
    )
    parts = [lead]
    body = (description or "").strip()
    if body:
        parts.append(body)
    return " ".join(parts)


_EN_CHAR_LEADINS = [
    "{name}{syns} is a character from '{origin}'{osyns}.",
    "{name}{syns} appears in '{origin}'{osyns}.",
    "In '{origin}'{osyns}, {name}{syns} is one of the cast.",
    "Meet {name}{syns}, from the series '{origin}'{osyns}.",
    "{name}{syns} belongs to the world of '{origin}'{osyns}.",
    "Here is {name}{syns}, a figure of '{origin}'{osyns}.",
]


def make_english_character_bio(name, origin, orgs, biography):
    syns = get_character_synonyms_string(name, "English")
    origin_syns = get_synonyms_string(origin, "English")
    lead = random.choice(_EN_CHAR_LEADINS).format(
        name=name, syns=syns, origin=origin, osyns=origin_syns
    )
    parts = [lead]
    if orgs:
        org_str = " and ".join(orgs)
        parts.append(f"They are affiliated with {org_str}.")
    bio = biography.strip() if biography else ""
    if bio:
        parts.append(bio)
    return " ".join(parts)
