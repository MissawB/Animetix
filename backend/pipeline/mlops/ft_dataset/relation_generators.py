# -*- coding: utf-8 -*-
"""Générateurs d'instructions « pilotés par données » (Q&A à partir des bases de
relations). Chaque fonction ne dépend que de sa constante de données dédiée —
aucun helper de génération de texte ni appel LLM.
"""

from ..french_market_db import FRENCH_MARKET_RELATIONS
from ..japanese_market_db import JAPANESE_MARKET_RELATIONS
from ..magazines_and_awards_db import AWARDS_AND_MAGAZINES_RELATIONS
from ..songs_and_seiyuu_db import SONGS_AND_SEIYUU_RELATIONS
from ..transmedia_db import TRANSMEDIA_RELATIONS
from ..volumes_and_episodes_db import VOLUMES_AND_EPISODES_DATA


def generate_transmedia_instructions():
    """Génère exactly 400 variations expertes en français pour les 100 relations transmédia."""
    transmedia_instructions = []
    for relation in TRANSMEDIA_RELATIONS:
        q = relation["question"]
        a = relation["answer"]

        # Variations
        transmedia_instructions.append({"instruction": q, "input": "", "output": a})
        transmedia_instructions.append(
            {
                "instruction": f"Peux-tu m'expliquer cette relation transmédia : {q}",
                "input": "",
                "output": f"Voici l'explication experte : {a}",
            }
        )
        q_clean = q[0].lower() + q[1:]
        transmedia_instructions.append(
            {
                "instruction": f"En tant qu'expert culturel, saurais-tu me dire {q_clean}",
                "input": "",
                "output": a,
            }
        )
        transmedia_instructions.append(
            {
                "instruction": f"Décris le lien et l'impact transmédia du sujet suivant : {q}",
                "input": "",
                "output": f"Lien transmédia détaillé : {a}",
            }
        )

    return transmedia_instructions


def generate_awards_and_magazines_instructions():
    """Génère exactly 160 variations expertes en français pour les 40 relations d'awards et magazines."""
    instructions = []
    for relation in AWARDS_AND_MAGAZINES_RELATIONS:
        q = relation["question"]
        a = relation["answer"]

        # Variations
        instructions.append({"instruction": q, "input": "", "output": a})
        instructions.append(
            {
                "instruction": f"Donne l'explication d'industrie ou de récompense associée à cette question : {q}",
                "input": "",
                "output": f"Explication d'industrie : {a}",
            }
        )
        q_clean = q[0].lower() + q[1:]
        instructions.append(
            {
                "instruction": f"En tant qu'expert de l'histoire du manga et de l'animation, saurais-tu me dire {q_clean}",
                "input": "",
                "output": a,
            }
        )
        instructions.append(
            {
                "instruction": f"Analyse le contexte de publication ou de prix du sujet suivant : {q}",
                "input": "",
                "output": f"Analyse et contexte : {a}",
            }
        )
    return instructions


def generate_songs_and_seiyuu_instructions():
    """Génère exactly 160 variations expertes en français pour les 40 relations de chansons d'animes et seiyuu."""
    instructions = []
    for relation in SONGS_AND_SEIYUU_RELATIONS:
        q = relation["question"]
        a = relation["answer"]

        # Variations
        instructions.append({"instruction": q, "input": "", "output": a})
        instructions.append(
            {
                "instruction": f"Donne l'explication artistique, de doublage ou d'opening associée à cette question : {q}",
                "input": "",
                "output": f"Explication artistique : {a}",
            }
        )
        q_clean = q[0].lower() + q[1:]
        instructions.append(
            {
                "instruction": f"En tant qu'expert musical et de doublage de la japanimation, saurais-tu me dire {q_clean}",
                "input": "",
                "output": a,
            }
        )
        instructions.append(
            {
                "instruction": f"Analyse le rôle musical ou l'identité de voix du sujet suivant : {q}",
                "input": "",
                "output": f"Analyse vocale et artistique : {a}",
            }
        )
    return instructions


def generate_french_market_relations_instructions():
    """Génère 4 variations pour chacune des 40 relations du marché français (160 instructions)."""
    instructions = []
    for relation in FRENCH_MARKET_RELATIONS:
        q = relation["question"]
        a = relation["answer"]

        # Variations
        instructions.append({"instruction": q, "input": "", "output": a})
        instructions.append(
            {
                "instruction": f"Donne l'explication et le contexte de cette question sur le marché français de japanimation : {q}",
                "input": "",
                "output": f"Explication du marché français : {a}",
            }
        )
        q_clean = q[0].lower() + q[1:]
        instructions.append(
            {
                "instruction": f"En tant que spécialiste de l'histoire du manga et de l'animation en France, saurais-tu me dire {q_clean}",
                "input": "",
                "output": a,
            }
        )
        instructions.append(
            {
                "instruction": f"Analyse le contexte d'édition, de doublage ou de distribution du sujet suivant : {q}",
                "input": "",
                "output": f"Analyse et contexte français : {a}",
            }
        )
    return instructions


def generate_japanese_market_relations_instructions():
    """Génère 4 variations pour chacune des 40 relations du marché japonais (160 instructions)."""
    instructions = []
    for relation in JAPANESE_MARKET_RELATIONS:
        q = relation["question"]
        a = relation["answer"]

        # Variations
        instructions.append({"instruction": q, "input": "", "output": a})
        instructions.append(
            {
                "instruction": f"Donne l'explication et le contexte de cette question sur le marché japonais de japanimation : {q}",
                "input": "",
                "output": f"Explication du marché japonais : {a}",
            }
        )
        q_clean = q[0].lower() + q[1:]
        instructions.append(
            {
                "instruction": f"En tant que spécialiste de l'histoire du manga et de l'animation au Japon, saurais-tu me dire {q_clean}",
                "input": "",
                "output": a,
            }
        )
        instructions.append(
            {
                "instruction": f"Analyse le contexte d'édition, de doublage ou de distribution du sujet suivant : {q}",
                "input": "",
                "output": f"Analyse et contexte japonais : {a}",
            }
        )
    return instructions


def generate_volumes_and_episodes_instructions():
    """Génère des instructions détaillées sur le nombre d'épisodes, de saisons et de tomes (volumes) pour les animés/mangas phares."""
    instructions = []
    for title, data in VOLUMES_AND_EPISODES_DATA.items():
        # Templates de questions/réponses
        templates = [
            (
                f"Combien d'épisodes et de saisons compte l'adaptation en animé de '{title}' ?",
                f"L'adaptation animée de '{title}' se structure ainsi : {data['anime_episodes']} répartis sur {data['anime_seasons']}. Statut général : {data['status']}. {data['details']}",
            ),
            (
                f"Quel est le nombre total de tomes (volumes) parus pour le manga '{title}' et est-il terminé ?",
                f"Le manga '{title}' compte : {data['manga_volumes']}. Statut de parution : {data['status']}. {data['details']}",
            ),
            (
                f"Fais-moi un récapitulatif complet du format (nombre d'épisodes, de saisons et de tomes) de '{title}'.",
                f"Voici le récapitulatif complet des formats pour '{title}' :\n- **Manga :** {data['manga_volumes']}.\n- **Animé :** {data['anime_episodes']} au fil de {data['anime_seasons']}.\n- **Statut global :** {data['status']}.\n- **Détails & contexte :** {data['details']}",
            ),
            (
                f"Donne-moi des détails sur la parution du manga et le nombre d'épisodes de l'anime '{title}'.",
                f"Pour '{title}', voici les détails d'industrie :\n- **Manga :** {data['manga_volumes']}.\n- **Épisodes & Saisons :** {data['anime_episodes']} sur {data['anime_seasons']}.\n- **Statut actuel :** {data['status']}.\n- **Informations complémentaires :** {data['details']}",
            ),
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})
    return instructions
