# -*- coding: utf-8 -*-
"""Générateurs d'instructions synthétiques (templates + tirage aléatoire) :
appels d'outils MCP, contextes RAG (Truth Path) et exemples de refus négatifs.

Ne dépendent que du module `random` (et de `FRENCH_VOICE_ACTORS` pour les
contextes RAG) — aucun appel LLM.
"""

import json
import random
from typing import Any, List

from ..french_market_db import FRENCH_VOICE_ACTORS  # noqa: F401

random = random.SystemRandom()  # type: ignore[assignment]  # intentional module-shadow: use CSPRNG


def generate_mcp_tool_instructions() -> List[dict]:
    """
    Génère des exemples d'entraînement SFT pour apprendre au modèle expert
    à appeler des serveurs MCP (Jikan et Spotify) et à en traiter les réponses.
    Génère ~250 variations.
    """
    instructions = []

    # Éléments de données pour l'injection
    titles = [
        "Kimetsu no Yaiba",
        "Shingeki no Kyojin",
        "One Piece",
        "Naruto",
        "Jujutsu Kaisen",
        "Boku no Hero Academia",
        "Hunter x Hunter",
        "Fullmetal Alchemist",
        "Steins;Gate",
        "Bleach",
        "Chainsaw Man",
    ]

    studios = [
        "Ufotable",
        "MAPPA",
        "Wit Studio",
        "Madhouse",
        "Bones",
        "Pierrot",
        "Toei Animation",
    ]

    tracks_data = [
        {
            "track": "Gurenge",
            "artist": "LiSA",
            "album": "Leo-Nine",
            "popularity": 85,
            "track_id": "0TrPqh5AaXEtzd52oKM769",
        },
        {
            "track": "Idol",
            "artist": "YOASOBI",
            "album": "Idol",
            "popularity": 92,
            "track_id": "2d1FDF2v80pB8E9f69b82F",
        },
        {
            "track": "Kaikai Kitan",
            "artist": "Eve",
            "album": "Kaikai Kitan",
            "popularity": 80,
            "track_id": "0yEvEvEve0py1EvE83jf8e",
        },
        {
            "track": "Shinzou wo Sasageyo!",
            "artist": "Linked Horizon",
            "album": "Shinzou wo Sasageyo",
            "popularity": 88,
            "track_id": "2SASASASA038sasasasas",
        },
        {
            "track": "Zankyou Sanka",
            "artist": "Aimer",
            "album": "Zankyou Sanka",
            "popularity": 84,
            "track_id": "3AiAiAimer039aierarera",
        },
        {
            "track": "Unravel",
            "artist": "TK from Ling Tosite Sigure",
            "album": "Fantastic Magic",
            "popularity": 87,
            "track_id": "0TkTkTkTk038tktktktkt",
        },
        {
            "track": "Sign",
            "artist": "FLOW",
            "album": "FLOW ANIME BEST",
            "popularity": 79,
            "track_id": "0FlFlFlFl038flflflflf",
        },
        {
            "track": "The Rumbling",
            "artist": "SiM",
            "album": "The Rumbling",
            "popularity": 86,
            "track_id": "0SiMSiMSiM038simsimsim",
        },
    ]

    artists = [
        "LiSA",
        "YOASOBI",
        "Aimer",
        "Eve",
        "FLOW",
        "Linked Horizon",
        "SiM",
        "Kenshi Yonezu",
        "RADWIMPS",
    ]

    characters_data = [
        {
            "title": "Kimetsu no Yaiba",
            "char1": "Tanjiro Kamado",
            "va1": "Natsuki Hanae",
            "char2": "Nezuko Kamado",
            "va2": "Akari Kito",
        },
        {
            "title": "Shingeki no Kyojin",
            "char1": "Eren Yeager",
            "va1": "Yuki Kaji",
            "char2": "Mikasa Ackerman",
            "va2": "Yui Ishikawa",
        },
        {
            "title": "One Piece",
            "char1": "Monkey D. Luffy",
            "va1": "Mayumi Tanaka",
            "char2": "Roronoa Zoro",
            "va2": "Kazuya Nakai",
        },
        {
            "title": "Jujutsu Kaisen",
            "char1": "Yuji Itadori",
            "va1": "Junya Enoki",
            "char2": "Satoru Gojo",
            "va2": "Yuichi Nakamura",
        },
        {
            "title": "Boku no Hero Academia",
            "char1": "Izuku Midoriya",
            "va1": "Daiki Yamashita",
            "char2": "Katsuki Bakugo",
            "va2": "Nobuhiko Okamoto",
        },
        {
            "title": "Hunter x Hunter",
            "char1": "Gon Freecss",
            "va1": "Megumi Han",
            "char2": "Killua Zoldyck",
            "va2": "Mariya Ise",
        },
    ]

    # --- 1. JIKAN SEARCH ANIME & DETAILS ---
    for title in titles:
        # Tool Call Generation
        q_templates = [
            f"Recherche les détails de l'anime '{title}' sur MyAnimeList pour voir sa note et ses épisodes.",
            f"Peux-tu interroger MyAnimeList (Jikan) pour l'anime '{title}' ?",
            f"Donne-moi les infos en temps réel de '{title}' depuis MAL.",
            f"Cherche l'anime '{title}' sur MAL avec l'API Jikan.",
        ]

        for q in q_templates:
            tool_call_json = {
                "server": "jikan",
                "tool": "search_anime",
                "arguments": {"query": title},
            }
            instructions.append(
                {
                    "instruction": q,
                    "input": "",
                    "output": f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False, indent=2)}\n</tool_call>",
                }
            )

        # Tool Response Processing
        for studio in studios:
            episodes = random.choice([12, 24, 26, 75, 170])
            score = round(random.uniform(7.8, 9.1), 2)

            tool_response_json = {
                "status": "success",
                "data": {
                    "title": title,
                    "episodes": episodes,
                    "score": score,
                    "status": "Finished Airing",
                    "studios": [studio],
                },
            }

            q_proc = f"Recherche les détails de l'anime '{title}' sur MyAnimeList."
            ans = f"D'après les informations obtenues en temps réel via MyAnimeList (Jikan), l'anime '{title}' comporte {episodes} épisodes, est produit par le studio {studio} et obtient une note globale de {score}/10."

            instructions.append(
                {
                    "instruction": q_proc,
                    "input": f"<tool_response>\n{json.dumps(tool_response_json, ensure_ascii=False, indent=2)}\n</tool_response>",
                    "output": ans,
                }
            )

    # --- 2. JIKAN ANIME CHARACTERS ---
    for char_info in characters_data:
        t = char_info["title"]
        q_templates = [
            f"Trouve la liste des personnages et doublages pour l'anime '{t}'.",
            f"Qui double les personnages principaux de '{t}' ? Interroge Jikan.",
            f"Quels sont les seiyuu et personnages principaux de '{t}' sur MyAnimeList ?",
        ]

        for q in q_templates:
            tool_call_json = {
                "server": "jikan",
                "tool": "get_anime_characters",
                "arguments": {"query": t},
            }
            instructions.append(
                {
                    "instruction": q,
                    "input": "",
                    "output": f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False, indent=2)}\n</tool_call>",
                }
            )

        # Tool Response Processing
        tool_response_json = {
            "status": "success",
            "data": {
                "characters": [
                    {
                        "name": char_info["char1"],
                        "role": "Main",
                        "voice_actor": char_info["va1"],
                    },
                    {
                        "name": char_info["char2"],
                        "role": "Supporting",
                        "voice_actor": char_info["va2"],
                    },
                ]
            },
        }

        q_proc = f"Trouve la liste des personnages et doublages pour l'anime '{t}'."
        ans = f"Voici les personnages principaux et leurs seiyuu officiels pour '{t}' :\n- **{char_info['char1']}** (rôle principal), doublé par {char_info['va1']}.\n- **{char_info['char2']}** (rôle de soutien), doublé par {char_info['va2']}."

        instructions.append(
            {
                "instruction": q_proc,
                "input": f"<tool_response>\n{json.dumps(tool_response_json, ensure_ascii=False, indent=2)}\n</tool_response>",
                "output": ans,
            }
        )

    # --- 3. SPOTIFY SEARCH TRACK ---
    for track_info in tracks_data:
        tr = track_info["track"]
        art = track_info["artist"]
        alb = track_info["album"]
        pop = track_info["popularity"]
        tr_id = track_info["track_id"]

        q_templates = [
            f"Recherche le morceau '{tr}' sur Spotify.",
            f"Trouve le lien de la chanson '{tr}' de '{art}' sur Spotify.",
            f"Cherche la musique '{tr}' via l'API Spotify.",
        ]

        for q in q_templates:
            tool_call_json = {
                "server": "spotify",
                "tool": "search_track",
                "arguments": {"query": f"{art} {tr}"},
            }
            instructions.append(
                {
                    "instruction": q,
                    "input": "",
                    "output": f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False, indent=2)}\n</tool_call>",
                }
            )

        # Tool Response Processing
        tool_response_json = {
            "status": "success",
            "data": {
                "tracks": [
                    {
                        "name": tr,
                        "artist": art,
                        "album": alb,
                        "popularity": pop,
                        "spotify_url": f"https://open.spotify.com/track/{tr_id}",
                    }
                ]
            },
        }

        q_proc = f"Recherche le morceau '{tr}' sur Spotify."
        ans = f"La chanson '{tr}' interprétée par {art} est disponible sur Spotify. Elle figure sur l'album '{alb}' avec un indice de popularité de {pop}/100. Vous pouvez l'écouter ici : https://open.spotify.com/track/{tr_id}."

        instructions.append(
            {
                "instruction": q_proc,
                "input": f"<tool_response>\n{json.dumps(tool_response_json, ensure_ascii=False, indent=2)}\n</tool_response>",
                "output": ans,
            }
        )

    # --- 4. SPOTIFY ARTIST TOP TRACKS ---
    for art in artists:
        q_templates = [
            f"Quels sont les morceaux les plus populaires de '{art}' sur Spotify ?",
            f"Affiche le top des écoutes de '{art}' sur Spotify.",
            f"Interroge Spotify pour avoir les meilleurs titres de '{art}'.",
        ]

        for q in q_templates:
            tool_call_json = {
                "server": "spotify",
                "tool": "get_artist_top_tracks",
                "arguments": {"artist_name": art},
            }
            instructions.append(
                {
                    "instruction": q,
                    "input": "",
                    "output": f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False, indent=2)}\n</tool_call>",
                }
            )

        # Tool Response Processing
        t1, t2, t3 = f"Track A de {art}", f"Track B de {art}", f"Track C de {art}"
        p1, p2, p3 = (
            random.randint(85, 95),
            random.randint(75, 84),
            random.randint(65, 74),
        )

        tool_response_json = {
            "status": "success",
            "data": {
                "artist": art,
                "top_tracks": [
                    {"name": t1, "popularity": p1},
                    {"name": t2, "popularity": p2},
                    {"name": t3, "popularity": p3},
                ],
            },
        }

        q_proc = f"Quels sont les morceaux les plus populaires de '{art}' sur Spotify ?"
        ans = f"Sur Spotify, les titres les plus écoutés de l'artiste '{art}' sont :\n1. **{t1}** (popularité: {p1}/100)\n2. **{t2}** (popularité: {p2}/100)\n3. **{t3}** (popularité: {p3}/100)"

        instructions.append(
            {
                "instruction": q_proc,
                "input": f"<tool_response>\n{json.dumps(tool_response_json, ensure_ascii=False, indent=2)}\n</tool_response>",
                "output": ans,
            }
        )

    # --- SCENARIOS D'ERREURS ET RESILIENCE MCP ---
    # 1. Erreur Jikan (Rate Limit 429)
    for tr in titles[:5]:
        q = f"Recherche les personnages du manga ou de l'anime '{tr}'."
        tool_response_error = {
            "status": "error",
            "code": 429,
            "message": "Rate limit exceeded. Too many requests.",
        }
        ans = f"Je rencontre actuellement une limite de requêtes avec l'API Jikan (Erreur 429). Néanmoins, d'après mes connaissances encyclopédiques, les personnages principaux de l'œuvre '{tr}' incluent les figures incontournables de son univers."

        instructions.append(
            {
                "instruction": q,
                "input": f"<tool_response>\n{json.dumps(tool_response_error, ensure_ascii=False, indent=2)}\n</tool_response>",
                "output": ans,
            }
        )

    # 2. Erreur Spotify (Service Unavailable 503)
    for art in artists[:5]:
        q = f"Quels sont les morceaux les plus populaires de '{art}' sur Spotify ?"
        tool_response_error = {
            "status": "error",
            "code": 503,
            "message": "Service Unavailable. Please try again later.",
        }
        ans = f"L'API Spotify est temporairement indisponible (Erreur 503). Je ne peux pas récupérer le classement en temps réel pour '{art}'. D'après mes connaissances de base de données, cet artiste possède un catalogue très populaire apprécié des fans d'anisongs."

        instructions.append(
            {
                "instruction": q,
                "input": f"<tool_response>\n{json.dumps(tool_response_error, ensure_ascii=False, indent=2)}\n</tool_response>",
                "output": ans,
            }
        )

    return instructions


def generate_rag_context_instructions(
    animes: List[dict[str, Any]], characters: List[dict[str, Any]]
) -> List[dict]:
    """
    Génère des exemples d'entraînement SFT pour le RAG (Retrieval-Augmented Generation).
    Le modèle doit répondre à une question sur une œuvre ou un personnage en s'appuyant
    strictement sur des fragments de contexte fournis (synopsis, trivia, fiches doubleurs)
    qui incluent du bruit (publicités, informations sur d'autres œuvres).
    Génère ~320 exemples.
    """
    instructions = []

    # Fragments de bruit pour simuler des documents non pertinents ou des publicités
    noise_fr = [
        "Sponsor : Profitez de 10% de réduction sur la boutique Otaku-Shop avec le code ANIME10.",
        "Météo : Des pluies éparses sont attendues sur Tokyo ce week-end.",
        "Rumeur : Un nouveau film d'animation pour cette franchise serait en préparation pour fin 2027.",
        "Note de l'éditeur : Cet article est paru initialement dans le magazine Shonen Jump en 2021.",
        "Avis des lecteurs : Une note moyenne de 4.8/5 a été attribuée à ce tome par les membres du club.",
        "Publicité : Téléchargez l'application Manga-Reader dès maintenant sur iOS et Android.",
    ]
    noise_en = [
        "Sponsor: Get 10% off at the Otaku-Shop with promo code ANIME10.",
        "Weather: Scattered showers are expected over Tokyo this weekend.",
        "Rumor: A new anime movie for this franchise is reportedly in production for late 2027.",
        "Editor's Note: This article was originally published in the Shonen Jump magazine in 2021.",
        "Reader reviews: A rating of 4.8/5 was given to this volume by club members.",
        "Advertisement: Download the Manga-Reader app now on iOS and Android.",
    ]

    import random

    random = random.SystemRandom()  # type: ignore[assignment]  # intentional module-shadow: use CSPRNG
    # noqa: E402

    # Scenario A: Synopsis extraction with noise
    for idx in range(120):
        lang = "English" if idx % 2 == 1 else "Français"
        anime: dict[str, Any] = (
            random.choice(animes)
            if animes
            else {
                "title": "Naruto",
                "genres": ["Action"],
                "studios": ["Pierrot"],
                "year": 2002,
            }
        )
        title = anime.get("title", "Unknown")
        genres = ", ".join(anime.get("genres", ["Action"]))
        studio = ", ".join(anime.get("studios") or []) or (
            "an unspecified studio" if lang == "English" else "un studio non précisé"
        )
        year = anime.get("year", 2002)

        # Build clean info
        if lang == "English":
            clean_doc = f"[Document A (Official profile)] The anime '{title}' was produced by {studio} and released in the year {year}. It belongs to the genres: {genres}."
            unrelated_anime = "One Piece" if title != "One Piece" else "Dragon Ball"
            noise_doc1 = f"[Document B (Trivia)] The manga '{unrelated_anime}' has sold millions of copies worldwide and is serialized in Weekly Shonen Jump."
            noise_doc2 = f"[Document C (Ads)] {random.choice(noise_en)}"

            # Shuffle docs order
            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)

            q = f"According to the provided documents, which studio produced the anime '{title}', in which year was it released, and which genres does it belong to?"
            ans = f"Based on the provided documents (specifically Document A), the anime '{title}' was produced by {studio} and released in {year}. It belongs to the genres: {genres}. The other documents contain unrelated trivia about '{unrelated_anime}' and an advertisement, which have been ignored."
        else:
            clean_doc = f"[Document A (Fiche officielle)] L'anime '{title}' a été produit par {studio} et est sorti en {year}. Il appartient aux genres : {genres}."
            unrelated_anime = "One Piece" if title != "One Piece" else "Dragon Ball"
            noise_doc1 = f"[Document B (Anecdotes)] Le manga '{unrelated_anime}' s'est vendu à des millions d'exemplaires et est prépublié dans le Weekly Shonen Jump."
            noise_doc2 = f"[Document C (Pub)] {random.choice(noise_fr)}"

            # Shuffle docs order
            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)

            q = f"D'après les documents fournis, quel studio a produit l'anime '{title}', en quelle année est-il sorti et à quels genres appartient-il ?"
            ans = f"D'après le contexte fourni (spécifiquement le Document A), l'anime '{title}' a été produit par {studio} et est sorti en {year}. Ses genres sont : {genres}. Les autres documents mentionnent des anecdotes sur '{unrelated_anime}' et une annonce publicitaire, qui ont été ignorées."

        instructions.append(
            {"instruction": q, "input": context, "output": ans, "language": lang}
        )

    # Scenario B: Voice Actor (VF) profile extraction with conflict

    voice_actors_list = (
        list(FRENCH_VOICE_ACTORS.keys())
        if FRENCH_VOICE_ACTORS
        else ["Brigitte Lecordier", "Benoît DuPac"]
    )

    for idx in range(100):
        lang = "English" if idx % 2 == 1 else "Français"
        va = random.choice(voice_actors_list)
        va_data = FRENCH_VOICE_ACTORS.get(
            va,
            {
                "definition": "Doubleur",
                "examples": "Rôle A",
                "impact": "VF culte",
                "origin": "AB Production",
            },
        )

        # Build clean info
        roles = va_data["examples"]
        bio = va_data["definition"]

        if lang == "English":
            clean_doc = f"[Source 1 (French Voice Cast)] the famous French voice actor '{va}' is known for lending their voice to: {roles}. They are recognized as: {bio}."
            noise_doc1 = "[Source 2 (Music)] Yoasobi is a popular Japanese music duo composed of producer Ayase and singer ikura."
            noise_doc2 = f"[Source 3] {random.choice(noise_en)}"

            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)

            q = f"Based on the text above, who is the French voice actor '{va}' and what are some of their iconic roles?"
            ans = f"According to Source 1, '{va}' is {bio}. Their iconic French voice acting roles include: {roles}. The other sources regarding Japanese music (Yoasobi) and advertisements were ignored as they are not relevant to the question."
        else:
            clean_doc = f"[Source 1 (Doublage Français)] Le célèbre comédien de doublage '{va}' est connu pour prêter sa voix en VF à : {roles}. Il est défini comme : {bio}."
            noise_doc1 = "[Source 2 (Musique)] Yoasobi est un duo musical japonais très populaire, composé du producteur Ayase et de la chanteuse Ikura."
            noise_doc2 = f"[Source 3] {random.choice(noise_fr)}"

            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)

            q = f"En vous appuyant sur les documents fournis, qui est le doubleur français '{va}' et quels sont ses rôles marquants ?"
            ans = f"D'après la Source 1, '{va}' est {bio}. Ses rôles marquants en version française (VF) sont : {roles}. Les informations sur le duo de musique japonais Yoasobi (Source 2) et les publicités ont été ignorées car elles ne concernent pas le sujet."

        instructions.append(
            {"instruction": q, "input": context, "output": ans, "language": lang}
        )

    # Scenario C: Character Bio with multiple documents
    for idx in range(100):
        lang = "English" if idx % 2 == 1 else "Français"
        char: dict[str, Any] = (
            random.choice(characters)
            if characters
            else {
                "name": "Luffy",
                "origin": "One Piece",
                "entities": {"organizations": ["Straw Hats"]},
                "popularity": {"favourites": 150000, "rank": 1},
                "metadata": {"height": "174cm"},
            }
        )
        name = char.get("name", "Unknown")
        origin = char.get("origin", "Unknown")
        height = (
            char.get("metadata", {}).get("height", "Unknown")
            if isinstance(char.get("metadata"), dict)
            else "Unknown"
        )
        favs = (
            char.get("popularity", {}).get("favourites", 0)
            if isinstance(char.get("popularity"), dict)
            else 0
        )

        if lang == "English":
            clean_doc = f"[Document A (Character Wiki)] Character profile: {name} is from '{origin}'. Official height: {height}. Popularity rank: {favs} favorites."
            noise_doc1 = f"[Document B (Sponsor)] {random.choice(noise_en)}"
            noise_doc2 = "[Document C (Release Dates)] Studio Trigger announced a new project coming out in winter next year."

            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)

            q = f"According to the context, what is the official height of '{name}' and which anime/manga work are they from?"
            ans = f"Based on Document A, the character '{name}' is from '{origin}' and their official height is {height}. Documents B and C contain unrelated sponsor advertisements and Trigger release announcements, which were excluded from this answer."
        else:
            clean_doc = f"[Document A (Wiki Personnages)] Profil du personnage : {name} est issu de '{origin}'. Sa taille officielle est {height}. Popularité : {favs} votes d'admiration."
            noise_doc1 = f"[Document B (Sponsor)] {random.choice(noise_fr)}"
            noise_doc2 = "[Document C (Sorties)] Le studio Trigger a annoncé un nouveau projet pour l'hiver prochain."

            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)

            q = f"D'après le contexte fourni, quelle est la taille officielle de '{name}' et de quelle œuvre est-il issu ?"
            ans = f"D'après le Document A, le personnage '{name}' provient de l'œuvre '{origin}' et sa taille officielle est {height}. Les Documents B et C concernant le sponsor publicitaire et les annonces du studio Trigger n'ont pas été pris en compte car ils sont hors-sujet."

        instructions.append(
            {"instruction": q, "input": context, "output": ans, "language": lang}
        )

    return instructions


def generate_negative_refusal_examples(count=800) -> List[dict]:
    """
    Génère procéduralement des exemples négatifs (hors-sujet) avec des refus polis
    cadrant l'expertise exclusive d'Animetix sur l'univers anime/manga.
    """
    import random

    random = random.SystemRandom()  # type: ignore[assignment]  # intentional module-shadow: use CSPRNG
    # noqa: E402

    refusals = []

    # Categories of out-of-scope topics
    topics_fr = {
        "recette": [
            "Comment faire un gâteau au chocolat ?",
            "Donne-moi la recette des lasagnes maison.",
            "Comment préparer une soupe à l'oignon ?",
            "Quelle est la recette traditionnelle du boeuf bourguignon ?",
            "Peux-tu m'expliquer comment réussir des macarons ?",
            "Comment cuire des asperges vertes à la poêle ?",
            "Quelle est la recette d'une vraie quiche lorraine ?",
            "Comment préparer une pâte à crêpes sans grumeaux ?",
            "Quel temps de cuisson pour un oeuf mollet ?",
        ],
        "programmation": [
            "Écris une fonction Python pour trier une liste.",
            "Comment résoudre un NullPointerException en Java ?",
            "Explique-moi la différence entre let, var et const en JavaScript.",
            "Comment configurer un serveur web avec Nginx ?",
            "Donne-moi un exemple de requête SQL pour joindre deux tables.",
            "Comment inverser une chaîne de caractères en C++ ?",
            "Écris une feuille de style CSS pour centrer une div.",
            "Comment configurer une base de données PostgreSQL avec Docker ?",
            "Qu'est-ce qu'une promesse (Promise) en JavaScript et comment l'utiliser ?",
            "Comment annuler le dernier commit avec Git ?",
        ],
        "mathematiques": [
            "Calcule la dérivée de f(x) = 3x^2 + 5x - 2.",
            "Quel est le théorème de Pythagore ?",
            "Comment résoudre une équation du second degré ?",
            "Combien font 1547 fois 36 ?",
            "Explique-moi la conjecture de Goldbach.",
        ],
        "medecine": [
            "Que faire en cas de migraine persistante ?",
            "Quels sont les symptômes d'une grippe ?",
            "Comment soigner un rhume rapidement ?",
            "Est-ce que l'ibuprofène est conseillé pour le mal de ventre ?",
            "Donne-moi des conseils pour mieux dormir sans médicaments.",
        ],
        "finance": [
            "Comment investir 1000 euros en bourse ?",
            "Qu'est-ce qu'une action à dividendes ?",
            "Comment fonctionne le Bitcoin et la cryptomonnaie ?",
            "Quels sont les meilleurs placements financiers actuels ?",
            "Comment rédiger un plan d'épargne retraite ?",
        ],
        "histoire_geo": [
            "Qui était le premier président de la République Française ?",
            "Quelle est la capitale de l'Australie ?",
            "Explique les causes de la Première Guerre mondiale.",
            "Combien de pays compte l'Union Européenne ?",
            "Qui a découvert l'Amérique en 1492 ?",
        ],
        "redaction": [
            "Rédige une lettre de motivation pour un poste d'ingénieur commercial.",
            "Aide-moi à écrire un e-mail professionnel pour demander une augmentation.",
            "Écris un poème d'amour romantique en alexandrins.",
            "Rédige un compte-rendu de réunion synthétique.",
            "Écris une critique littéraire du roman Les Misérables.",
        ],
        "science_technologie": [
            "Peux-tu m'expliquer la théorie de la relativité d'Einstein ?",
            "Comment fonctionne la fusion nucléaire ?",
            "Quelle est la distance entre la Terre et Mars ?",
            "Qu'est-ce qu'un trou noir ?",
            "Comment fonctionne le chiffrement RSA ?",
        ],
        "pop_culture_occidentale": [
            "Qui joue le rôle principal dans le film Inception ?",
            "Donne-moi la liste des albums de Taylor Swift.",
            "Quel est le synopsis de la série Breaking Bad ?",
            "Qui a réalisé le film Le Parrain ?",
            "Peux-tu me résumer l'intrigue de Star Wars Episode IV ?",
        ],
        "loisirs_sport": [
            "Comment bien entretenir un bonsaï chez soi ?",
            "Quelles sont les règles de base du football américain ?",
            "Donne-moi un programme de musculation pour débutant.",
            "Comment fabriquer une étagère en bois soi-même ?",
            "Quelles plantes planter en extérieur au printemps ?",
        ],
        "culture_generale": [
            "Quand a eu lieu la Révolution Française ?",
            "Quelle est la capitale du Canada ?",
            "Qui a peint la Joconde ?",
            "Quel est le plus long fleuve du monde ?",
            "Quelle est la hauteur de la Tour Eiffel ?",
        ],
    }

    topics_en = {
        "recipe": [
            "How do I bake a chocolate cake?",
            "Give me a recipe for homemade lasagna.",
            "How you make a classic French onion soup?",
            "What is the traditional recipe for beef stew?",
            "Can you explain how to make chocolate chip cookies?",
            "How do you cook green asparagus in a pan?",
            "What is the traditional recipe for a French quiche lorraine?",
            "How do I make pancake batter without lumps?",
            "How long does it take to soft-boil an egg?",
        ],
        "programming": [
            "Write a Python function to sort a list of numbers.",
            "How do I fix a NullPointerException in Java?",
            "Explain the difference between let, var, and const in JavaScript.",
            "How do I set up a web server using Nginx?",
            "Give me a SQL query example to join two tables.",
            "How do I reverse a string in C++?",
            "Write a CSS stylesheet to center a div horizontally and vertically.",
            "How do you run a PostgreSQL database using Docker?",
            "What is a Promise in JavaScript and how do you use it?",
            "How can I undo my last commit in Git?",
        ],
        "mathematics": [
            "Calculate the derivative of f(x) = 3x^2 + 5x - 2.",
            "What is the Pythagorean theorem?",
            "How do you solve a quadratic equation?",
            "What is 1547 multiplied by 36?",
            "Explain Goldbach's conjecture.",
        ],
        "medical": [
            "What should I do for a persistent headache?",
            "What are the main symptoms of the flu?",
            "How can I cure a cold quickly?",
            "Is ibuprofen recommended for stomach pain?",
            "Give me tips for sleeping better without medication.",
        ],
        "finance": [
            "How should I invest 1000 dollars in the stock market?",
            "What is a dividend-paying stock?",
            "How do Bitcoin and cryptocurrencies work?",
            "What are the best financial investments right now?",
            "How do I write a retirement savings plan?",
        ],
        "history_geo": [
            "Who was the first president of the United States?",
            "What is the capital of Australia?",
            "Explain the causes of World War I.",
            "How many countries are in the European Union?",
            "Who discovered America in 1492?",
        ],
        "writing": [
            "Write a cover letter for a sales engineer position.",
            "Help me write a professional email asking for a raise.",
            "Write a romantic love poem.",
            "Draft a concise meeting summary.",
            "Write a literary review of the novel Les Misérables.",
        ],
        "science_technology": [
            "Can you explain Einstein's theory of relativity?",
            "How does nuclear fusion work?",
            "What is the average distance between Earth and Mars?",
            "What is a black hole and how is it formed?",
            "How does RSA encryption secure data?",
        ],
        "western_pop_culture": [
            "Who plays the lead role in the movie Inception?",
            "Give me a list of all Taylor Swift albums.",
            "What is the plot of the TV show Breaking Bad?",
            "Who directed the movie The Godfather?",
            "Can you summarize the plot of Star Wars Episode IV?",
        ],
        "hobbies_sports": [
            "How do I properly care for a bonsai tree at home?",
            "What are the basic rules of American football?",
            "Give me a beginner-friendly workout routine.",
            "How can I build a wooden bookshelf myself?",
            "Which flowers should I plant in the spring?",
        ],
        "general_knowledge": [
            "When did the French Revolution start?",
            "What is the capital of Canada?",
            "Who painted the Mona Lisa?",
            "What is the longest river in the world?",
            "How tall is the Eiffel Tower?",
        ],
    }

    # Context / prefix templates to generate massive variations
    prefixes_fr = [
        "S'il te plaît, ",
        "Peux-tu me dire : ",
        "Est-ce que tu sais ",
        "J'ai besoin d'aide pour cela : ",
        "Dis-moi, ",
        "Est-il possible de m'expliquer ",
        "Pourrais-tu m'aider avec : ",
        "Bonjour, ",
        "Salut ! ",
        "J'aimerais savoir : ",
        "Dis, Animetix, ",
        "",
    ]

    prefixes_en = [
        "Please, ",
        "Can you tell me: ",
        "Do you know ",
        "I need help with this: ",
        "Tell me, ",
        "Is it possible to explain ",
        "Could you help me with: ",
        "Hello, ",
        "Hi! ",
        "I'd like to know: ",
        "Hey Animetix, ",
        "",
    ]

    refusal_templates_fr = [
        "En tant qu'Animetix, mon expertise se concentre exclusivement sur l'univers des animés, des mangas et de la culture otaku. Je ne peux donc pas vous aider avec des sujets hors de ce domaine comme {topic}. Si vous avez des questions sur des œuvres, des personnages, des doubleurs ou des créateurs de mangas, je serai ravi d'y répondre !",
        "Désolé, mais mon rôle d'assistant expert Animetix est dédié uniquement aux mangas, aux animés et à la pop-culture japonaise. Je dois refuser les requêtes concernant d'autres sujets comme {topic}. N'hésitez pas à me poser une question sur vos animes ou personnages préférés !",
        "Je ne peux pas répondre à cette demande. Animetix est une intelligence artificielle spécialisée uniquement dans les mangas, les animés et la culture otaku. Les questions concernant {topic} dépassent mon cadre d'expertise. Posez-moi plutôt une question sur l'univers des animés !",
        "En tant qu'expert de la japanimation et des mangas sous le nom d'Animetix, je me limite à ce domaine passionnant. Je ne peux pas traiter de sujets généraux tels que {topic}. Avez-vous une question sur les animés, les studios ou les seiyuu à me poser ?",
        "Navré, mais en tant qu'assistant Animetix, je suis uniquement conçu pour répondre aux questions relatives aux mangas, aux animés et à l'univers otaku. Je ne suis pas habilité à traiter des sujets comme {topic}. Si vous souhaitez parler de japanimation, je suis à votre disposition !",
        "Je regrette, mais ma base de connaissances sous le nom d'Animetix est spécialisée à 100% dans la pop-culture japonaise, les animés et les mangas. Je ne peux pas répondre aux demandes concernant {topic}. N'hésitez pas à me solliciter pour des recommandations d'animes !",
    ]

    refusal_templates_en = [
        "As Animetix, my expertise is exclusively focused on the universe of anime, manga, and otaku culture. Therefore, I cannot help you with topics outside this domain like {topic}. If you have questions about anime series, characters, voice actors, or manga creators, I would be delighted to answer!",
        "Sorry, but my role as the expert assistant Animetix is solely dedicated to manga, anime, and Japanese pop culture. I must decline requests concerning other topics like {topic}. Feel free to ask me questions about your favorite anime series or characters instead!",
        "I cannot answer this request. Animetix is an AI specialized exclusively in manga, anime, and otaku culture. Questions regarding {topic} fall outside my scope of expertise. Please ask me a question about the anime universe instead!",
        "As an anime and manga specialist known as Animetix, I restrict my answers to this exciting domain. I cannot assist with general topics such as {topic}. Do you have a question about anime, studios, or seiyuu for me?",
        "I am sorry, but as Animetix, I am strictly designed to answer queries about anime, manga, and otaku culture. I cannot assist with topics like {topic}. If you want to discuss Japanese animation or manga, I am here for you!",
        "Unfortunately, my database as Animetix is completely dedicated to Japanese pop culture, anime, and manga. I cannot address requests regarding {topic}. Please let me know if you need any anime recommendations instead!",
    ]

    for idx in range(count):
        lang = "English" if idx % 2 == 1 else "Français"

        if lang == "English":
            cat = random.choice(list(topics_en.keys()))
            question = random.choice(topics_en[cat])
            prefix = random.choice(prefixes_en)
            refusal_template = random.choice(refusal_templates_en)

            topic_names = {
                "recipe": "cooking recipes",
                "programming": "programming and coding",
                "mathematics": "mathematics",
                "medical": "medical advice",
                "finance": "financial topics",
                "history_geo": "general history or geography",
                "writing": "general writing",
                "science_technology": "science and technology",
                "western_pop_culture": "western pop culture",
                "hobbies_sports": "hobbies, sports, or DIY",
                "general_knowledge": "general knowledge or trivial facts",
            }
            topic_name = topic_names.get(cat, "general topics")
        else:
            cat = random.choice(list(topics_fr.keys()))
            question = random.choice(topics_fr[cat])
            prefix = random.choice(prefixes_fr)
            refusal_template = random.choice(refusal_templates_fr)

            topic_names = {
                "recette": "les recettes de cuisine",
                "programmation": "la programmation informatique",
                "mathematiques": "les mathématiques",
                "medecine": "les conseils médicaux",
                "finance": "la finance et les investissements",
                "histoire_geo": "l'histoire ou la géographie générale",
                "redaction": "la rédaction générale",
                "science_technologie": "les sciences et les technologies",
                "pop_culture_occidentale": "la pop culture occidentale",
                "loisirs_sport": "les loisirs, le sport ou le bricolage",
                "culture_generale": "la culture générale",
            }
            topic_name = topic_names.get(cat, "des sujets généraux")

        instruction = prefix + question
        # Ensure capitalization is clean
        if prefix and prefix[0].isupper() and len(question) > 0:
            instruction = prefix + question[0].lower() + question[1:]

        output = refusal_template.format(topic=topic_name)
        refusals.append(
            {
                "instruction": instruction,
                "input": "",
                "output": output,
                "language": lang,
            }
        )

    return refusals


# --- METHODE D'ASSEMBLAGE UNIFIEE ---
