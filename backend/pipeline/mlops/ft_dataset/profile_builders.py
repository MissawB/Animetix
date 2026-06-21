# -*- coding: utf-8 -*-
"""Constructeurs de texte naturel (FR/EN) pour les profils d'animes/mangas et
les biographies de personnages, plus les tables de synonymes/surnoms.

Constantes en lecture seule (`MULTI_TITLE_MAP`, `CHARACTER_NICKNAMES`) et
fonctions pures dépendant uniquement de `clean_tags`.
"""

import random
from typing import List

from .text_cleaning import clean_tags

random = random.SystemRandom()

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


def make_french_anime_profile(
    title: str, genres: List[str], studios: List[str], tags: List[str], year: int
) -> str:
    cleaned_tags = clean_tags(tags)
    cleaned_genres = clean_tags(genres)

    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "genres indéterminés"
    studios_str = ", ".join(studios) if studios else "un studio de talent non spécifié"
    tags_str = ", ".join(cleaned_tags[:5]) if cleaned_tags else "thématiques diverses"
    syns = get_synonyms_string(title)

    profile_parts = [
        f"L'anime '{title}'{syns} est une œuvre marquante de la japanimation sortie en {year}.",
        f"Elle s'inscrit avec brio dans les genres de type {genres_str}.",
        f"Produite de manière impressionnante par le studio {studios_str}, cette série s'est imposée par sa réalisation soignée.",
        f"Son univers aborde des thématiques profondes telles que {tags_str}.",
        f"En raison de ses grandes qualités artistiques et de son scénario palpitant, '{title}' est grandement recommandée pour les passionnés du genre.",
    ]
    return " ".join(profile_parts)


def make_french_manga_profile(title: str, genres: List[str], tags: List[str]) -> str:
    cleaned_tags = clean_tags(tags)
    cleaned_genres = clean_tags(genres)

    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "genres indéterminés"
    tags_str = ", ".join(cleaned_tags[:5]) if cleaned_tags else "thématiques diverses"
    syns = get_synonyms_string(title)

    profile_parts = [
        f"Le manga culte '{title}'{syns} est une œuvre majeure très appréciée des lecteurs.",
        f"Elle s'illustre particulièrement dans les registres éditoriaux et genres suivants : {genres_str}.",
        f"Ce manga propose une intrigue riche, se démarquant par ses thématiques fortes telles que {tags_str}.",
        f"À travers un découpage graphique saisissant et un scénario dense, '{title}' reste une référence incontournable de sa catégorie.",
    ]
    return " ".join(profile_parts)


def make_french_character_bio(name, origin, orgs, favs, rank, height):
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

    french_orgs = []
    for org in orgs:
        mapped = org_mapping.get(org, org)
        french_orgs.append(mapped)

    org_str = (
        " et ".join(french_orgs)
        if french_orgs
        else "plusieurs factions et groupes de son univers"
    )

    syns = get_character_synonyms_string(name)
    origin_syns = get_synonyms_string(origin)

    bio_parts = [
        f"{name}{syns} est un personnage légendaire et de premier plan issu de l'œuvre à succès '{origin}'{origin_syns}.",
        "Au sein de cette œuvre, son importance narrative est colossale.",
    ]

    if french_orgs:
        bio_parts.append(
            f"Il est principalement connu pour son affiliation et son rôle majeur au sein de : {org_str}."
        )

    if height and height != "Unknown":
        bio_parts.append(
            f"Ses caractéristiques physiques et son profil officiel mentionnent notamment : {height}."
        )

    bio_parts.append(
        f"Il jouit d'une immense popularité auprès de la communauté mondiale des passionnés de japanimation, se plaçant au rang numéro {rank} des personnages favoris avec pas moins de {favs} votes d'admiration."
    )

    bio_parts.append(
        f"En tant que figure incontournable de '{origin}', {name} incarne les valeurs et les conflits majeurs de son univers, marquant profondément les spectateurs par son écriture et son développement scénaristique de premier ordre."
    )

    return " ".join(bio_parts)


def make_english_anime_profile(
    title: str, genres: List[str], studios: List[str], tags: List[str], year: int
) -> str:
    cleaned_tags = clean_tags(tags, "English")
    cleaned_genres = clean_tags(genres, "English")

    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "undetermined genres"
    studios_str = ", ".join(studios) if studios else "unspecified talented studio"
    tags_str = ", ".join(cleaned_tags[:5]) if cleaned_tags else "various themes"
    syns = get_synonyms_string(title, "English")

    profile_parts = [
        f"The anime '{title}'{syns} is a landmark work of Japanese animation released in {year}.",
        f"It fits brilliantly into the {genres_str} genres.",
        f"Produced impressively by the studio {studios_str}, this series has established itself through its careful direction and production quality.",
        f"Its story and universe address deep thematic concepts such as {tags_str}.",
        f"Due to its high artistic quality and thrilling plot, '{title}' is highly recommended for anime fans.",
    ]
    return " ".join(profile_parts)


def make_english_manga_profile(title: str, genres: List[str], tags: List[str]) -> str:
    cleaned_tags = clean_tags(tags, "English")
    cleaned_genres = clean_tags(genres, "English")

    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "undetermined genres"
    tags_str = ", ".join(cleaned_tags[:5]) if cleaned_tags else "various themes"
    syns = get_synonyms_string(title, "English")

    profile_parts = [
        f"The cult manga '{title}'{syns} is a major work highly appreciated by readers.",
        f"It is particularly famous in the following genres and publishing categories: {genres_str}.",
        f"This manga offers a rich plot, standing out for its strong themes such as {tags_str}.",
        f"With its striking graphic panels and a dense story, '{title}' remains an essential reference in its category.",
    ]
    return " ".join(profile_parts)


def make_english_character_bio(name, origin, orgs, favs, rank, height):
    org_str = (
        " and ".join(orgs) if orgs else "several factions and groups in their universe"
    )

    syns = get_character_synonyms_string(name, "English")
    origin_syns = get_synonyms_string(origin, "English")

    formatted_favs = f"{favs:,}"

    bio_parts = [
        f"{name}{syns} is a legendary and prominent character from the hit series '{origin}'{origin_syns}.",
        "Within this work, their narrative importance is colossal.",
    ]

    if orgs:
        bio_parts.append(
            f"They are primarily known for their affiliation and major role within: {org_str}."
        )

    if height and height != "Unknown":
        bio_parts.append(
            f"Their physical characteristics and official profile notably mention: {height}."
        )

    bio_parts.append(
        f"They enjoy immense popularity among the global community of anime fans, ranking at number {rank} of favorite characters with no less than {formatted_favs} votes of admiration."
    )

    bio_parts.append(
        f"As an essential figure in '{origin}', {name} embodies the values and major conflicts of their universe, deeply marking the audience with their writing and top-tier character development."
    )

    return " ".join(bio_parts)
