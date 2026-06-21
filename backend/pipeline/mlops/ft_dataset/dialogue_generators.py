# -*- coding: utf-8 -*-
"""Génération procédurale de dialogues multi-tours à partir des bases locales
(passées en paramètres). Utilise les helpers de nettoyage et de profils.
"""

import random
from typing import Any, List

from .profile_builders import (
    get_display_character,
    get_display_title,
    make_english_anime_profile,
    make_english_character_bio,
    make_french_anime_profile,
    make_french_character_bio,
)
from .text_cleaning import clean_tags

random = random.SystemRandom()  # type: ignore[assignment]  # intentional module-shadow: use CSPRNG


def generate_multiturn_dialogues(
    animes, mangas, characters, otaku_vocab, count=1000
) -> List[dict]:
    """
    Génère procéduralement des dialogues multi-tours à partir des bases de données locales.
    """
    dialogues = []

    # Templates de questions/réponses en Français
    fr_anime_templates = [
        {
            "t1": "Salut ! Tu as un bon anime de {genre} à me conseiller ?",
            "t2": "Ah super. Et c'est quel studio qui l'a produit, et en quelle année ?",
            "t3": "Génial, merci. Et quelles sont les thématiques principales abordées ?",
        }
    ]
    # Templates de questions/réponses en Anglais
    en_anime_templates = [
        {
            "t1": "Hi! Can you recommend a good {genre} anime?",
            "t2": "Awesome. Which studio produced it, and in what year was it released?",
            "t3": "Thanks! What are the primary themes in this anime?",
        }
    ]

    fr_char_templates = [
        {
            "t1": "Qui est le personnage {name} ?",
            "t2": "D'accord, et à quel groupe ou faction appartient-il ?",
            "t3": "Quelle est sa taille officielle et est-il populaire ?",
        }
    ]
    en_char_templates = [
        {
            "t1": "Who is the character {name}?",
            "t2": "Understood, and which group or faction do they belong to?",
            "t3": "What is their official height and are they popular?",
        }
    ]

    fr_vocab_templates = [
        {
            "t1": "Peux-tu m'expliquer le concept otaku de '{term}' ?",
            "t2": "Quels sont des exemples connus qui illustrent ce trope ?",
            "t3": "D'où vient ce terme et quel est son impact sur l'écriture ?",
        }
    ]
    en_vocab_templates = [
        {
            "t1": "Can you explain the otaku concept of '{term}'?",
            "t2": "What are some well-known examples illustrating this trope?",
            "t3": "Where does this term come from and what is its writing impact?",
        }
    ]

    for idx in range(count):
        lang = "English" if (idx // 7) % 2 == 1 else "Français"
        scenario = idx % 7

        # Safe fallback if databases are empty or not matching requirements
        if scenario == 3 and (not animes or len(animes) < 2):
            scenario = 0
        if scenario == 4 and not animes:
            scenario = 1
        if scenario == 5 and (not animes or len(animes) < 2):
            scenario = 0

        if scenario == 0 and animes:
            # Anime / Manga exploration dialogue
            anime = random.choice(animes)
            title = anime.get("title", "Unknown")
            display_title = get_display_title(title)
            genres = anime.get("genres", ["Action"])
            genre = random.choice(genres) if genres else "Action"
            studios = anime.get("studios", ["Pierrot"])
            studio_str = ", ".join(studios)
            year = anime.get("year", 2002)
            tags = anime.get("tags", [])
            tags_str = ", ".join(clean_tags(tags, lang)[:4])

            if lang == "English":
                p_text = make_english_anime_profile(title, genres, studios, tags, year)
                t = en_anime_templates[0]
                turns = [
                    {"user": t["t1"].format(genre=genre), "assistant": p_text},
                    {
                        "user": t["t2"],
                        "assistant": f"This anime was produced by the studio {studio_str} and released in {year}.",
                    },
                    {
                        "user": t["t3"],
                        "assistant": f"In '{display_title}', the primary themes explored are: {tags_str}.",
                    },
                ]
            else:
                p_text = make_french_anime_profile(title, genres, studios, tags, year)
                t = fr_anime_templates[0]
                turns = [
                    {"user": t["t1"].format(genre=genre), "assistant": p_text},
                    {
                        "user": t["t2"],
                        "assistant": f"Cet anime a été produit par le studio {studio_str} et est sorti en {year}.",
                    },
                    {
                        "user": t["t3"],
                        "assistant": f"Dans '{display_title}', les thématiques principales abordées sont : {tags_str}.",
                    },
                ]

        elif scenario == 1 and characters:
            # Character dialogue
            char = random.choice(characters)
            name = char.get("name", "Unknown")
            display_name = get_display_character(name)
            origin = char.get("origin", "Unknown")
            get_display_title(origin)
            ents = char.get("entities", {})
            orgs = ents.get("organizations", []) if isinstance(ents, dict) else []
            orgs_str = ", ".join(orgs) if orgs else "several groups"
            favs = (
                char.get("popularity", {}).get("favourites", 0)
                if isinstance(char.get("popularity"), dict)
                else 0
            )
            rank = (
                char.get("popularity", {}).get("rank", 999)
                if isinstance(char.get("popularity"), dict)
                else 999
            )
            height = (
                char.get("metadata", {}).get("height", "Unknown")
                if isinstance(char.get("metadata"), dict)
                else "Unknown"
            )

            if lang == "English":
                p_text = make_english_character_bio(
                    name, origin, orgs, favs, rank, height
                )
                t = en_char_templates[0]
                turns = [
                    {"user": t["t1"].format(name=display_name), "assistant": p_text},
                    {
                        "user": t["t2"],
                        "assistant": f"They are primarily known for their affiliation with: {orgs_str}.",
                    },
                    {
                        "user": t["t3"],
                        "assistant": f"Their official height is {height}. They are ranked #{rank} in popularity with {favs:,} favourites.",
                    },
                ]
            else:
                p_text = make_french_character_bio(
                    name, origin, orgs, favs, rank, height
                )
                t = fr_char_templates[0]
                turns = [
                    {"user": t["t1"].format(name=display_name), "assistant": p_text},
                    {
                        "user": t["t2"],
                        "assistant": f"Il est principalement connu pour son affiliation avec : {orgs_str}.",
                    },
                    {
                        "user": t["t3"],
                        "assistant": f"Sa taille officielle est {height}. Il est classé au rang #{rank} des favoris avec {favs} votes d'admiration.",
                    },
                ]

        elif scenario == 2:
            # Otaku concept dialogue
            vocab_list = list(otaku_vocab.keys())
            term = random.choice(vocab_list) if vocab_list else "Tsundere"
            data = otaku_vocab.get(
                term,
                {
                    "definition": "trope",
                    "examples": "Taiga",
                    "impact": "popular",
                    "origin": "Japan",
                },
            )

            if lang == "English":
                t = en_vocab_templates[0]
                turns = [
                    {
                        "user": t["t1"].format(term=term),
                        "assistant": f"In otaku culture, '{term}' refers to: {data['definition']}.",
                    },
                    {
                        "user": t["t2"],
                        "assistant": f"Iconic examples illustrating this concept include: {data['examples']}.",
                    },
                    {
                        "user": t["t3"],
                        "assistant": f"Origin: {data['origin']}. Narrative impact: {data['impact']}.",
                    },
                ]
            else:
                t = fr_vocab_templates[0]
                turns = [
                    {
                        "user": t["t1"].format(term=term),
                        "assistant": f"Dans la culture otaku, '{term}' désigne : {data['definition']}.",
                    },
                    {
                        "user": t["t2"],
                        "assistant": f"Parmi les exemples emblématiques illustrant ce concept, on peut citer : {data['examples']}.",
                    },
                    {
                        "user": t["t3"],
                        "assistant": f"Origine : {data['origin']}. Impact narratif : {data['impact']}.",
                    },
                ]

        elif scenario == 3:
            # comparative debate
            anime1 = random.choice(animes)
            anime2 = random.choice(animes)
            while anime2.get("title") == anime1.get("title"):
                anime2 = random.choice(animes)

            title1 = get_display_title(anime1.get("title", "Unknown"))
            title2 = get_display_title(anime2.get("title", "Unknown"))
            genres1 = ", ".join(clean_tags(anime1.get("genres", []), lang))
            genres2 = ", ".join(clean_tags(anime2.get("genres", []), lang))
            studio1 = ", ".join(anime1.get("studios", ["Pierrot"]))
            studio2 = ", ".join(anime2.get("studios", ["Toei Animation"]))
            year1 = anime1.get("year", 2002)
            year2 = anime2.get("year", 1999)
            pop1 = anime1.get("popularity", 10000)
            pop2 = anime2.get("popularity", 10000)

            char_name = "Luffy"
            for c in characters:
                if c.get("origin") == anime1.get("title"):
                    char_name = get_display_character(c.get("name"))
                    break

            if lang == "English":
                turns = [
                    {
                        "user": f"I want to compare two major anime: '{title1}' and '{title2}'. Which one should I watch?",
                        "assistant": f"Both are incredible shows but quite different. '{title1}' fits into the {genres1} genres and was produced by {studio1}. On the other hand, '{title2}' is a {genres2} show produced by {studio2}. If you enjoy character-driven shows, '{title1}' is a great pick. If you prefer high-stakes action, go with '{title2}'.",
                    },
                    {
                        "user": f"But I heard that '{title1}' has much better character development, do you agree?",
                        "assistant": f"That is a very common opinion! The character writing in '{title1}' is indeed stellar, especially with figures like {char_name}. However, '{title2}' makes up for it with its thrilling pacing and outstanding production values. It depends on whether you value psychological depth or action-packed animation more.",
                    },
                    {
                        "user": "Understood. Are both finished and were they popular?",
                        "assistant": f"Yes, '{title1}' was released in {year1} and has a popularity score of {pop1:,} members. '{title2}' was released in {year2} with {pop2:,} members. Both are major hits in otaku culture.",
                    },
                ]
            else:
                turns = [
                    {
                        "user": f"Je cherche à comparer deux œuvres majeures de la japanimation : '{title1}' et '{title2}'. Lequel devrais-je regarder ?",
                        "assistant": f"Ce sont deux œuvres formidables mais très différentes. '{title1}' s'inscrit dans les genres de type {genres1} et a été produit par {studio1}. De l'autre côté, '{title2}' s'illustre dans les genres {genres2} par {studio2}. Si tu aimes la profondeur des personnages, '{title1}' est un excellent choix. Si tu préfères l'action pure, opte pour '{title2}'.",
                    },
                    {
                        "user": f"Mais j'ai entendu dire que '{title1}' a une bien meilleure écriture de personnages, tu es d'accord ?",
                        "assistant": f"C'est un point de vue très répandu ! L'écriture des personnages dans '{title1}' est en effet brillante, notamment grâce à des figures emblématiques comme {char_name}. Cependant, '{title2}' compense par son rythme haletant et ses qualités d'animation. Tout dépend de ce qui prime pour toi entre la profondeur psychologique et la mise en scène.",
                    },
                    {
                        "user": "D'accord, je vois. Est-ce que les deux sont terminés et ont été populaires ?",
                        "assistant": f"Oui, '{title1}' est sorti en {year1} et jouit d'une popularité de {pop1} membres. '{title2}' est sorti en {year2} et compte {pop2} membres. Les deux sont des succès majeurs incontournables.",
                    },
                ]

        elif scenario == 4:
            # Clarification request
            sub_scenario = random.choice(
                ["studio_genre", "character_name", "adaptation"]
            )

            if sub_scenario == "studio_genre":
                anime = random.choice(animes)
                title = get_display_title(anime.get("title", "Unknown"))
                genres = clean_tags(anime.get("genres", ["Action"]), lang)
                genre = (
                    genres[0]
                    if genres
                    else ("Action" if lang == "English" else "Action")
                )
                studio = ", ".join(anime.get("studios", ["Pierrot"]))
                year = anime.get("year", 2002)
                genres_str = ", ".join(genres)

                tags = clean_tags(anime.get("tags", []), lang)
                tag = (
                    tags[0]
                    if tags
                    else ("adventure" if lang == "English" else "aventure")
                )
                tags_str = ", ".join(tags[:3])

                char_name = "Luffy"
                for c in characters:
                    if c.get("origin") == anime.get("title"):
                        char_name = get_display_character(c.get("name"))
                        break

                if lang == "English":
                    turns = [
                        {
                            "user": f"Can you tell me about that popular {genre} anime produced by {studio}?",
                            "assistant": f"Could you please clarify which anime you mean? Studio {studio} has produced several {genre} anime, such as '{title}' (with themes like {tag}) or other notable projects. Were you referring to this one?",
                        },
                        {
                            "user": f"Yes, I was referring to '{title}'!",
                            "assistant": f"Great! '{title}' was released in {year} and falls into the genres: {genres_str}. The story explores key themes like: {tags_str}. It is a prominent production by {studio}.",
                        },
                        {
                            "user": "Thanks for the details. Are there any highly popular characters in it?",
                            "assistant": f"Definitely! Within this universe, {char_name} is extremely popular among fans, ranking high with many votes of admiration.",
                        },
                    ]
                else:
                    turns = [
                        {
                            "user": f"Peux-tu me parler de cet anime de {genre} très populaire produit par {studio} ?",
                            "assistant": f"Pourrais-tu préciser de quelle œuvre il s'agit ? Le studio {studio} a produit plusieurs animés de {genre}, notamment '{title}' (avec des thèmes comme {tag}) ou d'autres projets marquants. Parlais-tu de celui-ci ?",
                        },
                        {
                            "user": f"Oui, je parlais bien de '{title}' !",
                            "assistant": f"Excellent choix ! '{title}' est sorti en {year} et s'inscrit dans les genres : {genres_str}. L'histoire aborde des thématiques fortes comme : {tags_str}. C'est une production majeure de {studio}.",
                        },
                        {
                            "user": "Merci pour ces détails. Est-ce qu'il y a des personnages très populaires dedans ?",
                            "assistant": f"Absolument ! Si on regarde les personnages de cet univers, {char_name} est particulièrement apprécié de la communauté, se classant dans le top avec de nombreux votes d'admiration.",
                        },
                    ]

            elif sub_scenario == "character_name":
                # Clarification about character names that are ambiguous
                choices: list[dict[str, Any]] = [
                    {
                        "common_name": "Sakura",
                        "char1": "Sakura Haruno",
                        "anime1": "Naruto",
                        "char2": "Sakura Kinomoto",
                        "anime2": "Cardcaptor Sakura",
                    },
                    {
                        "common_name": "Rin",
                        "char1": "Rin Tohsaka",
                        "anime1": "Fate/stay night",
                        "char2": "Rin Okumura",
                        "anime2": "Blue Exorcist",
                    },
                    {
                        "common_name": "Yuki",
                        "char1": "Yuki Sohma",
                        "anime1": "Fruits Basket",
                        "char2": "Yuki Nagato",
                        "anime2": "The Melancholy of Haruhi Suzumiya",
                    },
                ]
                choice = random.choice(choices)
                common_name = choice["common_name"]
                char1 = choice["char1"]
                anime1 = choice["anime1"]
                char2 = choice["char2"]
                anime2 = choice["anime2"]

                orgs1 = [
                    "le village de Konoha" if lang == "Français" else "Konoha Village"
                ]

                for c in characters:
                    if c.get("name") == char1:
                        ents = c.get("entities", {})
                        if isinstance(ents, dict) and ents.get("organizations"):
                            orgs1 = ents["organizations"]
                    if c.get("name") == char2:
                        ents = c.get("entities", {})
                        if isinstance(ents, dict) and ents.get("organizations"):
                            ents["organizations"]

                orgs1_str = ", ".join(orgs1)

                if lang == "English":
                    turns = [
                        {
                            "user": f"Can you give me information about the character '{common_name}'?",
                            "assistant": f"There are several famous characters named '{common_name}' in anime. Are you referring to {char1} from '{anime1}' or {char2} from '{anime2}'?",
                        },
                        {
                            "user": f"I was talking about {char1} in '{anime1}'.",
                            "assistant": f"Understood! {char1} is a key protagonist in '{anime1}'. Within this work, they play a narrative-defining role and are deeply connected to the main plot.",
                        },
                        {
                            "user": "Great, thanks. What groups or factions do they belong to?",
                            "assistant": f"In '{anime1}', they are primarily associated with the following groups or factions: {orgs1_str}.",
                        },
                    ]
                else:
                    turns = [
                        {
                            "user": f"Peux-tu me donner des informations sur le personnage '{common_name}' ?",
                            "assistant": f"Il existe plusieurs personnages célèbres nommés '{common_name}' dans la japanimation. Fais-tu référence à {char1} de '{anime1}' ou à {char2} de '{anime2}' ?",
                        },
                        {
                            "user": f"Je parlais de {char1} dans '{anime1}'.",
                            "assistant": f"D'accord ! {char1} est un protagoniste clé de '{anime1}'. Dans cette œuvre, il joue un rôle narratif déterminant et est intimement lié à l'intrigue principale.",
                        },
                        {
                            "user": "Super, merci. Quels sont ses groupes d'appartenance ?",
                            "assistant": f"Dans '{anime1}', il est principalement associé aux groupes ou factions suivantes : {orgs1_str}.",
                        },
                    ]

            else:
                # Clarification about adaptations (e.g., FMA vs FMAB, or first adaptation vs remake)
                choices = [
                    {
                        "title": "Fullmetal Alchemist",
                        "studio1": "Studio Bones",
                        "year1": 2003,
                        "studio2": "Studio Bones (Brotherhood)",
                        "year2": 2009,
                        "episodes1": 51,
                        "episodes2": 64,
                    },
                    {
                        "title": "Hunter x Hunter",
                        "studio1": "Nippon Animation",
                        "year1": 1999,
                        "studio2": "Madhouse",
                        "year2": 2011,
                        "episodes1": 62,
                        "episodes2": 148,
                    },
                    {
                        "title": "Fate/stay night",
                        "studio1": "Studio Deen",
                        "year1": 2006,
                        "studio2": "ufotable",
                        "year2": 2014,
                        "episodes1": 24,
                        "episodes2": 26,
                    },
                ]
                choice = random.choice(choices)
                title = choice["title"]
                studio1 = choice["studio1"]
                year1 = choice["year1"]
                studio2 = choice["studio2"]
                year2 = choice["year2"]
                choice["episodes1"]
                episodes2 = choice["episodes2"]

                if lang == "English":
                    turns = [
                        {
                            "user": f"I would like to get details about the anime adaptation of '{title}'.",
                            "assistant": f"The franchise '{title}' has multiple adaptations. Are you referring to the first series animated by {studio1} in {year1}, or the remake version animated by {studio2} in {year2}?",
                        },
                        {
                            "user": f"The version from {year2}.",
                            "assistant": f"Excellent choice! The {year2} adaptation of '{title}' by {studio2} is highly praised for its faithful retelling of the original manga source material, offering stellar production values.",
                        },
                        {
                            "user": "How many episodes does it have in total?",
                            "assistant": f"This version of '{title}' consists of {episodes2} episodes in total.",
                        },
                    ]
                else:
                    turns = [
                        {
                            "user": f"Je voudrais des détails sur l'adaptation en animé de '{title}'.",
                            "assistant": f"La franchise '{title}' possède plusieurs adaptations. Fais-tu référence à la première série produite par {studio1} en {year1}, ou à la version remake produite par {studio2} en {year2} ?",
                        },
                        {
                            "user": f"La version de {year2}.",
                            "assistant": f"Excellent choix ! L'adaptation de {year2} de '{title}' par {studio2} est particulièrement réputée pour sa fidélité totale au manga d'origine et ses combats spectaculaires.",
                        },
                        {
                            "user": "Combien d'épisodes comporte-t-elle au total ?",
                            "assistant": f"Cette version de '{title}' comporte un total de {episodes2} épisodes.",
                        },
                    ]

        elif scenario == 5:
            # Progressive recommendation (user refines tastes)
            anime1 = random.choice(animes)
            anime2 = random.choice(animes)
            while anime2.get("title") == anime1.get("title"):
                anime2 = random.choice(animes)

            title1 = get_display_title(anime1.get("title", "Unknown"))
            title2 = get_display_title(anime2.get("title", "Unknown"))

            genres1 = anime1.get("genres", ["Action"])
            genre1 = random.choice(genres1) if genres1 else "Action"

            # Translate genre1 if language is English
            if lang == "English":
                genre1_translated = clean_tags([genre1], "English")[0]
            else:
                genre1_translated = clean_tags([genre1], "Français")[0]

            genres2 = anime2.get("genres", [])
            tags2 = anime2.get("tags", [])
            all_genres_tags2_lower = [g.lower() for g in genres2 + tags2]

            # Determine mood of anime2
            dark_keywords = [
                "drama",
                "psychological",
                "horror",
                "tragedy",
                "mystery",
                "thriller",
                "seinen",
                "dark fantasy",
            ]
            light_keywords = [
                "comedy",
                "slice of life",
                "parody",
                "school",
                "romance",
                "shoujo",
                "josei",
            ]
            action_keywords = [
                "action",
                "adventure",
                "fantasy",
                "supernatural",
                "mecha",
                "shonen",
                "super power",
            ]

            if any(k in all_genres_tags2_lower for k in dark_keywords):
                mood_fr = "sombre et psychologique"
                mood_en = "dark and psychological"
            elif any(k in all_genres_tags2_lower for k in light_keywords):
                mood_fr = "léger, comique ou axé tranche de vie"
                mood_en = "light, comedy or slice-of-life"
            elif any(k in all_genres_tags2_lower for k in action_keywords):
                mood_fr = "dynamique avec de l'action ou de l'aventure"
                mood_en = "dynamic, action-packed or adventurous"
            else:
                mood_fr = "captivant et profond"
                mood_en = "captivating and deep"

            studio2 = ", ".join(anime2.get("studios", ["MAPPA"]))
            year2 = anime2.get("year", 2021)
            (
                ", ".join(clean_tags(tags2, lang)[:3])
                if tags2
                else ("animation" if lang == "English" else "animation")
            )

            # Check if we have volume/episode count from database or use a realistic dummy
            from backend.pipeline.mlops.volumes_and_episodes_db import (  # noqa: E402
                VOLUMES_AND_EPISODES_DATA,
            )

            episodes2 = "12 épisodes" if lang == "Français" else "12 episodes"
            if anime2.get("title") in VOLUMES_AND_EPISODES_DATA:
                episodes2 = VOLUMES_AND_EPISODES_DATA[anime2.get("title")][
                    "anime_episodes"
                ]
            else:
                episodes2 = random.choice(["12", "24", "26", "50", "75"])
                if lang == "Français":
                    episodes2 = f"{episodes2} épisodes"
                else:
                    episodes2 = f"{episodes2} episodes"

            if lang == "English":
                p_text1 = make_english_anime_profile(
                    anime1.get("title"),
                    genres1,
                    anime1.get("studios", []),
                    anime1.get("tags", []),
                    anime1.get("year", 2010),
                )
                p_text2 = make_english_anime_profile(
                    anime2.get("title"),
                    genres2,
                    anime2.get("studios", []),
                    tags2,
                    year2,
                )

                turns = [
                    {
                        "user": f"Hi! I'm looking for a good {genre1_translated} anime. Do you have any recommendation?",
                        "assistant": f"Hello! I highly recommend '{title1}'. {p_text1}",
                    },
                    {
                        "user": f"Thanks, but actually I would prefer something more {mood_en}. Do you have something else?",
                        "assistant": f"I see! In that case, you should check out '{title2}'. {p_text2}",
                    },
                    {
                        "user": "That looks awesome! Which studio produced it, and how many episodes does it have?",
                        "assistant": f"'{title2}' was produced by the studio {studio2} and consists of {episodes2} in total. It was released in {year2}.",
                    },
                ]
            else:
                p_text1 = make_french_anime_profile(
                    anime1.get("title"),
                    genres1,
                    anime1.get("studios", []),
                    anime1.get("tags", []),
                    anime1.get("year", 2010),
                )
                p_text2 = make_french_anime_profile(
                    anime2.get("title"),
                    genres2,
                    anime2.get("studios", []),
                    tags2,
                    year2,
                )

                turns = [
                    {
                        "user": f"Salut ! Je cherche un bon anime de type {genre1_translated}. Tu as une recommandation ?",
                        "assistant": f"Bonjour ! Je te conseille vivement '{title1}'. {p_text1}",
                    },
                    {
                        "user": f"Merci, mais en fait je préfère quelque chose de plus {mood_fr}. Tu as un autre choix ?",
                        "assistant": f"Je vois ! Dans ce cas, tu devrais adorer '{title2}'. {p_text2}",
                    },
                    {
                        "user": "Ça a l'air super ! Quel studio a produit cette série, et elle fait combien d'épisodes ?",
                        "assistant": f"'{title2}' a été produit par le studio {studio2} et compte un total de {episodes2}. Cet anime est sorti en {year2}.",
                    },
                ]
        else:
            # Self-correction after feedback
            anime_choice = random.choice(
                [
                    {
                        "title_fr": "L'Attaque des Titans",
                        "title_en": "Attack on Titan",
                        "s1": "Wit Studio",
                        "s2": "MAPPA",
                        "year1": 2013,
                        "year2": 2020,
                        "vols": 34,
                    },
                    {
                        "title_fr": "One Punch Man",
                        "title_en": "One Punch Man",
                        "s1": "Madhouse",
                        "s2": "J.C.Staff",
                        "year1": 2015,
                        "year2": 2019,
                        "vols": 30,
                    },
                    {
                        "title_fr": "Vinland Saga",
                        "title_en": "Vinland Saga",
                        "s1": "Wit Studio",
                        "s2": "MAPPA",
                        "year1": 2019,
                        "year2": 2023,
                        "vols": 27,
                    },
                ]
            )

            if lang == "English":
                title = anime_choice["title_en"]
                s1 = anime_choice["s1"]
                s2 = anime_choice["s2"]
                y1 = anime_choice["year1"]
                y2 = anime_choice["year2"]
                vols = anime_choice["vols"]
                turns = [
                    {
                        "user": f"Which animation studio produced '{title}'?",
                        "assistant": f"The anime adaptation of '{title}' was primarily produced by {s1} starting in {y1}.",
                    },
                    {
                        "user": f"Wait, wasn't it produced by {s2} instead?",
                        "assistant": f"You are absolutely correct, thank you for pointing that out! There was a change in production: {s1} animated the initial part (starting in {y1}), and then {s2} took over for the subsequent seasons starting in {y2}.",
                    },
                    {
                        "user": "Ah I see, thanks. Is the manga finished?",
                        "assistant": f"Yes, the manga has finished its publication run, compiling a total of {vols} volumes.",
                    },
                ]
            else:
                title = anime_choice["title_fr"]
                s1 = anime_choice["s1"]
                s2 = anime_choice["s2"]
                y1 = anime_choice["year1"]
                y2 = anime_choice["year2"]
                vols = anime_choice["vols"]
                turns = [
                    {
                        "user": f"Quel studio d'animation s'est occupé de l'anime '{title}' ?",
                        "assistant": f"L'adaptation animée de '{title}' a été initialement produite par le studio {s1} à partir de {y1}.",
                    },
                    {
                        "user": f"Attends, ce n'est pas plutôt le studio {s2} qui l'a fait ?",
                        "assistant": f"Vous avez tout à fait raison, et je vous remercie pour cette précision importante ! Il y a eu un changement de studio : {s1} a produit le début (à partir de {y1}), puis c'est le studio {s2} qui a repris la main pour produire les saisons suivantes à partir de {y2}.",
                    },
                    {
                        "user": "Ah d'accord, merci pour l'explication. Et le manga est terminé ?",
                        "assistant": f"Oui, le manga s'est achevé avec un total de {vols} volumes publiés.",
                    },
                ]

        dialogues.append({"turns": turns, "language": lang})

    return dialogues
