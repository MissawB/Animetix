# -*- coding: utf-8 -*-
"""
Compilateur de jeu de données de fine-tuning SFT expert UNIFIÉ, 100% en français,
sans code-switching, fusionnant l'expertise d'animes/mangas japonais, les ponts transmédias,
les musiques (anisongs), les seiyuu, et l'écosystème du Marché Français (doubleurs VF, éditeurs, diffuseurs).
Proportions mathématiques parfaites garanties : 80% spécialisé, 5% vocabulaire méta, 15% général.
"""

import json
import os
import random
import sys
import logging
import time
import html
import re
from typing import List, Any
from datasets import load_dataset
from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger("animetix.pipeline." + __name__)

def clean_description(text: str) -> str:
    if not text:
        return ""
    # 1. Décoder les entités HTML
    text = html.unescape(text)
    # 2. Supprimer les balises HTML
    text = re.sub(r'</?[a-zA-Z]+(?:\s+[^>]*)?>', ' ', text)
    # 3. Supprimer les espaces multiples et les retours à la ligne
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Chemins de fichiers absolus
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(BASE_DIR, '.env'))
ANIME_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
MANGA_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_mangas.json')
CHAR_DB = os.path.join(BASE_DIR, 'data', 'processed', 'refined_characters.json')
OUTPUT_DATASET = os.path.join(BASE_DIR, 'data', 'mlops', 'datasets', 'animetix_expert_ft.jsonl')

# Ajout du répertoire courant pour l'import des modules de base de données locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from otaku_concepts import OTAKU_VOCABULARY
from creators_db import CREATORS_AND_STUDIOS
from transmedia_db import TRANSMEDIA_RELATIONS
from magazines_and_awards_db import AWARDS_AND_MAGAZINES_RELATIONS
from songs_and_seiyuu_db import SONGS_AND_SEIYUU_RELATIONS
from french_market_db import (
    FRENCH_VOICE_ACTORS,
    FRENCH_MANGA_PUBLISHERS,
    FRENCH_ANIME_DISTRIBUTORS,
    FRENCH_MARKET_RELATIONS
)
from volumes_and_episodes_db import VOLUMES_AND_EPISODES_DATA

CACHE_FILE = os.path.join(BASE_DIR, 'data', 'mlops', 'datasets', 'gemini_paraphrase_cache.json')
PARAPHRASE_CACHE = {}

def load_paraphrase_cache():
    global PARAPHRASE_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                PARAPHRASE_CACHE = json.load(f)
            logger.info(f"Loaded {len(PARAPHRASE_CACHE)} entries from paraphrase cache.")
        except Exception as e:
            logger.warning(f"Failed to load paraphrase cache: {e}")
            PARAPHRASE_CACHE = {}
    else:
        PARAPHRASE_CACHE = {}

def save_paraphrase_cache():
    if PARAPHRASE_CACHE:
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(PARAPHRASE_CACHE, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(PARAPHRASE_CACHE)} entries to paraphrase cache.")
        except Exception as e:
            logger.warning(f"Failed to save paraphrase cache: {e}")

load_paraphrase_cache()

def paraphrase_text_via_gemini(text: str, client, style_type: str = "naturel") -> str:
    """
    Appelle Gemini pour paraphraser un texte en français afin de diversifier le style.
    En cas d'échec ou d'absence de client, retourne le texte original.
    Utilise un cache local persistant JSON pour éviter les appels redondants.
    """
    if not text:
        return ""
    
    cache_key = f"{text.strip()}||{style_type}"
    if cache_key in PARAPHRASE_CACHE:
        return PARAPHRASE_CACHE[cache_key]
        
    if not client:
        return text
    
    prompt = (
        f"Réécris et paraphrase le texte suivant en français de manière fluide et naturelle. "
        f"Ne change pas les faits, les noms propres, les studios, ou les dates. "
        f"Style souhaité : {style_type}. "
        f"Renvoie uniquement le texte réécrit, sans aucun commentaire ou salutations.\n\n"
        f"Texte à réécrire :\n{text}"
    )
    
    model_name = os.getenv("ANIMETIX_GEMINI_MODEL", "gemini-3-flash-preview")
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response.text:
                time.sleep(0.5)  # Respecter le rate limiting
                result_text = response.text.strip()
                PARAPHRASE_CACHE[cache_key] = result_text
                return result_text
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/3 failed to paraphrase: {e}")
            err_msg = str(e).upper()
            if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg or "503" in err_msg:
                sleep_time = (attempt + 1) * 15.0  # 15s, 30s
                logger.info(f"Rate limit or service unavailable detected. Sleeping for {sleep_time}s before retry...")
                time.sleep(sleep_time)
            else:
                time.sleep(1.0)
            
    return text

def calculate_dataset_counts(non_meta_count: int) -> tuple[int, int]:
    """
    Calcule dynamiquement le nombre d'exemples méta et généraux nécessaires
    en fonction du nombre d'exemples spécialisés (non_meta_count) et des ratios
    configurés via les variables d'environnement.
    """
    ratio_spec = float(os.getenv("ANIMETIX_RATIO_SPECIALIZED", "80.0"))
    ratio_meta = float(os.getenv("ANIMETIX_RATIO_META", "5.0"))
    ratio_gen = float(os.getenv("ANIMETIX_RATIO_GENERAL", "15.0"))
    
    # Normalisation pour être robuste
    total_ratio = ratio_spec + ratio_meta + ratio_gen
    if total_ratio <= 0:
        logger.warning("Total SFT ratio is less than or equal to 0, falling back to 80/5/15.")
        ratio_spec, ratio_meta, ratio_gen = 80.0, 5.0, 15.0
        total_ratio = 100.0
        
    meta_required = int(non_meta_count * (ratio_meta / ratio_spec))
    general_required = int(non_meta_count * (ratio_gen / ratio_spec))
    
    return meta_required, general_required

# --- CARTOGRAPHIE DES ANAGRAMMES ET DES NOMS MULTIPLES (COMMUNAUTÉS ET NICKNAMES) ---
MULTI_TITLE_MAP = {
    "Shingeki no Kyojin": ["L'Attaque des Titans", "Attack on Titan", "SnK"],
    "Kimetsu no Yaiba": ["Demon Slayer", "Demon Slayer: Kimetsu no Yaiba", "Pourfendeur de démons"],
    "Boku no Hero Academia": ["My Hero Academia", "MHA"],
    "Jujutsu Kaisen": ["JJK"],
    "One Piece": ["OP"],
    "Naruto Shippuuden": ["Naruto Shippuden"],
    "Hagane no Renkinjutsushi: FULLMETAL ALCHEMIST": ["Fullmetal Alchemist: Brotherhood", "FMAB"],
    "Steins;Gate": ["Steins Gate"],
    "Kiseijuu: Sei no Kakuritsu": ["Parasyte", "Parasyte -the maxim-"],
    "Sen to Chihiro no Kamikakushi": ["Le Voyage de Chihiro", "Spirited Away"],
    "Mononoke Hime": ["Princesse Mononoké", "Princess Mononoke"],
    "Tonari no Totoro": ["Mon Voisin Totoro", "My Neighbor Totoro"],
    "Howl no Ugoku Shiro": ["Le Château ambulant", "Howl's Moving Castle"],
    "Kaze no Tani no Nausicaa": ["Nausicaä de la Vallée du Vent", "Nausicaa of the Valley of the Wind"],
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
    "Kaguya-sama wa Kokurasetai: Tensaitachi no Renai Zounousen": ["Kaguya-sama: Love is War", "Kaguya-sama"],
    "Re:Zero kara Hajimeru Isekai Seikatsu": ["Re:Zero", "Re Zero"],
    "Fate/stay night [Unlimited Blade Works]": ["Fate Unlimited Blade Works", "UBW"],
    "Violet Evergarden": ["Violet Evergarden"],
    "Tokyo Ghoul": ["TG"],
    "No Game No Life": ["NGNL"],
    "Boku dake ga Inai Machi": ["ERASED"],
    "Ansatsu Kyoushitsu": ["Assassination Classroom"],
    "Mahou Shoujo Madoka★Magica": ["Puella Magi Madoka Magica", "Madoka Magica"]
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
    "Kurisu Makise": ["Christina", "Kurigohan and Kamehameha"]
}

def clean_tags(tags):
    if not tags: return []
    invalid_keywords = [
        "aucune unité", "ia n'est disponible", "ollama", "hf", "désolé", "sorry", 
        "no computational unit", "error", "pas de description", "inconnu", "unknown"
    ]
    cleaned = []
    for tag in tags:
        lower_tag = tag.lower()
        if any(kw in lower_tag for kw in invalid_keywords):
            continue
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
            "Martial Arts": "Arts martiaux"
        }
        cleaned.append(tag_translation.get(tag, tag))
    return cleaned

def get_synonyms_string(title):
    if title in MULTI_TITLE_MAP:
        names = [f"'{n}'" for n in MULTI_TITLE_MAP[title]]
        return f" (également connu sous les noms de {', '.join(names)})"
    return ""

def get_character_synonyms_string(name):
    if name in CHARACTER_NICKNAMES:
        names = [f"'{n}'" for n in CHARACTER_NICKNAMES[name]]
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

# --- GENERATEURS DE TEXTE NATUREL EN FRANÇAIS ---

def make_french_anime_profile(title: str, genres: List[str], studios: List[str], tags: List[str], year: int) -> str:
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
        f"En raison de ses grandes qualités artistiques et de son scénario palpitant, '{title}' est grandement recommandée pour les passionnés du genre."
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
        f"À travers un découpage graphique saisissant et un scénario dense, '{title}' reste une référence incontournable de sa catégorie."
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
        "Black Bulls": "la compagnie du Taureau Noir (Black Bulls)"
    }
    
    french_orgs = []
    for org in orgs:
        mapped = org_mapping.get(org, org)
        french_orgs.append(mapped)
        
    org_str = " et ".join(french_orgs) if french_orgs else "plusieurs factions et groupes de son univers"
    
    syns = get_character_synonyms_string(name)
    origin_syns = get_synonyms_string(origin)
    
    bio_parts = [
        f"{name}{syns} est un personnage légendaire et de premier plan issu de l'œuvre à succès '{origin}'{origin_syns}.",
        f"Au sein de cette œuvre, son importance narrative est colossale.",
    ]
    
    if french_orgs:
        bio_parts.append(f"Il est principalement connu pour son affiliation et son rôle majeur au sein de : {org_str}.")
    
    if height and height != "Unknown":
        bio_parts.append(f"Ses caractéristiques physiques et son profil officiel mentionnent notamment : {height}.")
        
    bio_parts.append(f"Il jouit d'une immense popularité auprès de la communauté mondiale des passionnés de japanimation, se plaçant au rang numéro {rank} des personnages favoris avec pas moins de {favs} votes d'admiration.")
    
    bio_parts.append(f"En tant que figure incontournable de '{origin}', {name} incarne les valeurs et les conflits majeurs de son univers, marquant profondément les spectateurs par son écriture et son développement scénaristique de premier ordre.")
    
    return " ".join(bio_parts)

# --- GENERATEURS DE JEUX DE DONNEES ---

def generate_otaku_meta_instructions():
    """Génère un grand nombre de variations expertes de Q&A pour le dictionnaire Otaku de base + les créateurs et studios."""
    otaku_instructions = []
    
    # 1. Génération par template pour les concepts généraux (15 variations par concept = ~6 000 exemples)
    for term, data in OTAKU_VOCABULARY.items():
        templates = [
            (f"Qu'est-ce que le terme '{term}' dans la culture otaku ? Cite des exemples.", 
             f"Dans la culture otaku, le terme '{term}' désigne : {data['definition']}. Parmi les exemples emblématiques, on peut citer : {data['examples']}. Impact culturel : {data['impact']}"),
            
            (f"Donne-moi une définition claire et précise du concept de '{term}' dans les animés.",
             f"Le concept de '{term}' se définit comme suit dans l'animation japonaise : {data['definition']}. On l'illustre à travers des exemples comme : {data['examples']}."),
            
            (f"En tant qu'expert de la japanimation, comment définirais-tu le concept de '{term}' ?",
             f"En tant qu'expert, je définis '{term}' par : {data['definition']}. Cette notion a un fort impact de domaine : {data['impact']}"),
            
            (f"Peux-tu m'expliquer ce que signifie '{term}' pour un passionné de mangas ?",
             f"Pour un passionné de mangas, '{term}' représente : {data['definition']}. C'est une figure courante caractérisée par : {data['origin']}"),
            
            (f"Explique l'origine, l'étymologie et la signification profonde du trope '{term}'.",
             f"Le trope '{term}' possède une étymologie et une histoire riches. Origine : {data['origin']}. Signification profonde : {data['definition']}. Ce trope s'illustre particulièrement bien avec : {data['examples']}."),
            
            (f"D'où vient le mot '{term}' utilisé dans la culture otaku et que signifie-t-il ?",
             f"Le terme '{term}' trouve sa racine dans : {data['origin']}. Il désigne précisément : {data['definition']}. En industrie, cela s'explique par : {data['impact']}"),
            
            (f"Quelle est l'histoire et la racine linguistique du concept de '{term}' dans les mangas ?",
             f"L'histoire linguistique de '{term}' remonte à : {data['origin']}. C'est un concept fondamental signifiant : {data['definition']}"),
            
            (f"Quels personnages ou œuvres sont considérés comme des exemples emblématiques de '{term}' ?",
             f"Parmi les exemples phares associés à '{term}', on trouve : {data['examples']}. Par définition, ce trope représente : {data['definition']}"),
            
            (f"Donne-moi des exemples de figures célèbres illustrant le trope '{term}' dans les animés.",
             f"Les figures majeures illustrant le trope '{term}' incluent : {data['examples']}. Ce trope se caractérise par : {data['definition']} et tire son origine de : {data['origin']}"),
            
            (f"Quelles sont les œuvres majeures qui représentent le mieux le concept de '{term}' ?",
             f"Les œuvres et personnages emblématiques pour '{term}' sont : {data['examples']}. Ce concept est défini comme : {data['definition']}"),
            
            (f"Quelle est l'importance et l'impact culturel de la notion de '{term}' dans l'industrie de l'animation ?",
             f"L'impact culturel de '{term}' dans l'industrie est majeur. {data['impact']} Par définition : {data['definition']}. On le retrouve dans : {data['examples']}"),
            
            (f"Analyse l'influence et le rôle scénaristique du trope '{term}' dans les mangas.",
             f"Le rôle scénaristique de '{term}' est très influent. {data['impact']} Il permet d'exprimer : {data['definition']}. Exemples : {data['examples']}"),
            
            (f"Pourquoi le concept de '{term}' est-il si populaire et récurrent dans les animés japonais ?",
             f"La popularité de '{term}' s'explique par sa résonance dans la pop-culture. {data['impact']} Origine : {data['origin']}. Définition : {data['definition']}"),
            
            (f"Fais-moi une synthèse complète et experte sur le concept Otaku de '{term}'.",
             f"Synthèse Experte - '{term}' : {data['definition']}. Origine étymologique : {data['origin']}. Œuvres et personnages repères : {data['examples']}. Impact d'écriture : {data['impact']}"),
            
            (f"Quels sont les détails clés et l'analyse à retenir sur la notion de '{term}' ?",
             f"Les points essentiels à retenir sur '{term}' sont : sa définition ({data['definition']}), sa racine historique ({data['origin']}) et ses incarnations majeures ({data['examples']}).")
        ]
        for q, a in templates:
            otaku_instructions.append({
                "instruction": q,
                "input": "",
                "output": a
            })
            
    # 2. Génération par template pour les créateurs et studios d'animation (15 variations par concept = 1 500 exemples)
    for creator, data in CREATORS_AND_STUDIOS.items():
        templates = [
            (f"Qui est '{creator}' dans le monde de l'animation et du manga japonais ?",
             f"Dans l'industrie japonaise, '{creator}' est : {data['definition']}. Ses travaux les plus marquants incluent : {data['examples']}. Impact : {data['impact']}"),
            
            (f"Présente-moi en détail le profil et l'impact industriel de '{creator}'.",
             f"Profil de domaine - '{creator}' : {data['definition']} Origines et contexte : {data['origin']}. Parmi ses œuvres les plus célèbres, on compte : {data['examples']}. Son impact est immense : {data['impact']}"),
            
            (f"Quelles sont les œuvres emblématiques de '{creator}' et son rôle historique ?",
             f"'{creator}' a marqué l'histoire à travers ses créations : {data['examples']}. Il est défini comme : {data['definition']} Influence majeure : {data['impact']}"),
            
            (f"En tant que spécialiste de la japanimation, que peux-tu me dire sur '{creator}' ?",
             f"En tant que spécialiste, je peux vous dire que '{creator}' est : {data['definition']} Contexte historique : {data['origin']}. Il a travaillé sur des projets comme : {data['examples']}."),
            
            (f"Pourquoi '{creator}' est-il considéré comme une figure légendaire de la culture otaku ?",
             f"'{creator}' est considéré comme légendaire car son impact a été révolutionnaire : {data['impact']} Il s'est imposé comme : {data['definition']}"),
            
            (f"Quels sont les projets phares de '{creator}' ?",
             f"Les projets marquants de '{creator}' comprennent : {data['examples']}. Sa philosophie et son parcours : {data['origin']}"),
            
            (f"Présente une synthèse complète du studio ou créateur '{creator}'.",
             f"Synthèse de domaine - '{creator}' : {data['definition']}. Histoire et origines : {data['origin']}. Réalisations majeures : {data['examples']}. Impact d'industrie : {data['impact']}"),
            
            (f"Peux-tu analyser l'importance de '{creator}' pour l'industrie du manga ?",
             f"L'importance de '{creator}' est indiscutable : {data['impact']} Il a œuvré à travers : {data['definition']}. Œuvres repères : {data['examples']}"),
            
            (f"Quel a été le rôle de '{creator}' dans le développement de l'animation japonaise ?",
             f"'{creator}' a joué un rôle déterminant : {data['impact']} Par définition : {data['definition']}. Contexte : {data['origin']}"),
            
            (f"Donne des détails sur le style ou les contributions de '{creator}'.",
             f"Les contributions de '{creator}' se résument ainsi : {data['definition']}. Ses travaux phares : {data['examples']}. Style et impact : {data['impact']}"),
             
            (f"Explique comment '{creator}' a influencé d'autres auteurs ou studios.",
             f"L'influence de '{creator}' s'étend largement : {data['impact']} Il a redéfini le secteur comme : {data['definition']}. Ses créations repères sont : {data['examples']}"),
             
            (f"Quelles sont les caractéristiques majeures associées aux créations de '{creator}' ?",
             f"Les créations de '{creator}' se caractérisent par son style : {data['definition']}. Exemples notables : {data['examples']}. Contexte : {data['origin']}"),
             
            (f"Décris le parcours artistique et le profil de '{creator}'.",
             f"Parcours de '{creator}' : {data['definition']}. Origines et évolutions : {data['origin']}. Ses projets les plus influents : {data['examples']}"),
             
            (f"Analyse l'importance historique et l'héritage de '{creator}'.",
             f"L'héritage de '{creator}' est colossal. {data['impact']} Connu pour : {data['definition']}. Réalisations clés : {data['examples']}"),
             
            (f"Qu'est-ce qui rend '{creator}' incontournable dans le paysage otaku moderne ?",
             f"'{creator}' est incontournable en tant que : {data['definition']}. Ses créations populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.")
        ]
        for q, a in templates:
            otaku_instructions.append({
                "instruction": q,
                "input": "",
                "output": a
            })
            
    # 3. Ajout de comparaisons croisées (12 exemples)
    comparisons = [
        ("Tsundere", "Yandere", "Alors que le personnage Tsundere cache son affection derrière de l'agressivité verbale mais reste fondamentalement sain, le Yandere bascule dans une folie obsessionnelle et violente (pouvant aller jusqu'au meurtre) pour posséder l'être aimé."),
        ("Kuudere", "Dandere", "Le personnage Kuudere est calme, froid, impassible et garde le contrôle de ses émotions en public ('cool'), tandis que le Dandere est d'une timidité maladive, asocial et silencieux par peur d'interagir, bien qu'il soit extrêmement chaleureux une fois en confiance."),
        ("Shonen", "Seinen", "Le Shonen cible un public de jeunes garçons adolescents (focus sur les combats, l'amitié sacrée 'nakama' et le dépassement de soi), tandis que le Seinen vise les jeunes adultes masculins, abordant des thèmes plus matures, sombres, philosophiques ou politiques (comme la vengeance dans *Berserk* ou l'éthique dans *Monster*)."),
        ("Shojo", "Josei", "Le Shojo cible les adolescentes (romances idéalisées, esthétique fleurie et focus émotionnel), tandis que le Josei s'adresse aux femmes adultes, traitant de relations amoureuses ou professionnelles de manière beaucoup plus réaliste et mature (ex: *Nana*)."),
        ("Sub", "Dub", "Le format 'Sub' (VOSTFR/VOST) conserve les voix et l'interprétation originale des seiyuu japonais qui est souvent considérée comme plus expressive et authentique, tandis que le 'Dub' (doublage local) offre un confort de visionnage maximal et une immersion immédiate sans lecture de sous-titres, idéal pour toucher un public plus large."),
        ("Raw", "Sub", "La version 'Raw' désigne le flux vidéo brut tel qu'il est diffusé à la TV japonaise sans aucun sous-titre ni modification, alors que la version 'Sub' intègre les pistes de sous-titres traduits pour la diffusion internationale."),
        ("Maid", "Butler", "La Maid incarne la servante en uniforme victorien/français et est l'icône de la culture kawaii et des maid cafés, tandis que le Butler (majordome) incarne la classe, le sang-froid et la protection élégante, souvent doté de capacités martiales démesurées."),
        ("Himedere", "Oujidere", "La Himedere exige d'être traitée comme une reine/princesse exigeante et capricieuse, tandis que l'Oujidere incarne l'équivalent masculin exigeant d'être traité comme un prince hautain et charismatique."),
        ("Isekai", "Reverse Isekai", "L'Isekai traditionnel projette un humain ordinaire dans un autre monde fantastique, tandis que le Reverse Isekai amène des créatures magiques ou divines (ex: un roi démon) dans notre monde moderne et terre-à-terre."),
        ("Slow Life", "Isekai", "L'Isekai traditionnel met en scène des quêtes héroïques et des combats contre des rois démons, alors que le sous-genre 'Slow Life' se concentre sur l'agriculture, l'artisanat et une vie paisible loin des conflits."),
        ("Kamidere", "Himedere", "Le Kamidere a un complexe divin absolu et veut réformer le monde ou dominer l'humanité, tandis que la Himedere cherche simplement à être adorée, servie et choyée comme une princesse royale."),
        ("Sadodere", "Tsundere", "La Tsundere est hostile par gêne et fierté mais devient douce rapidement, tandis que la Sadodere prend un plaisir délibéré et malicieux à taquiner, manipuler ou dominer psychologiquement l'être aimé.")
    ]
    for t1, t2, diff in comparisons:
        otaku_instructions.append({
            "instruction": f"Quelle est la différence fondamentale entre les termes '{t1}' et '{t2}' dans les animés et mangas ?",
            "input": "",
            "output": f"La distinction entre '{t1}' et '{t2}' est essentielle pour comprendre les archétypes d'animes. {diff} Par exemple, pour les {t1}, on pense souvent à {OTAKU_VOCABULARY[t1]['examples']}, tandis que pour les {t2}, un exemple frappant est {OTAKU_VOCABULARY[t2]['examples']}."
        })
        
    return otaku_instructions

def generate_transmedia_instructions():
    """Génère exactly 400 variations expertes en français pour les 100 relations transmédia."""
    transmedia_instructions = []
    for relation in TRANSMEDIA_RELATIONS:
        q = relation["question"]
        a = relation["answer"]
        
        # Variations
        transmedia_instructions.append({"instruction": q, "input": "", "output": a})
        transmedia_instructions.append({"instruction": f"Peux-tu m'expliquer cette relation transmédia : {q}", "input": "", "output": f"Voici l'explication experte : {a}"})
        q_clean = q[0].lower() + q[1:]
        transmedia_instructions.append({"instruction": f"En tant qu'expert culturel, saurais-tu me dire {q_clean}", "input": "", "output": a})
        transmedia_instructions.append({"instruction": f"Décris le lien et l'impact transmédia du sujet suivant : {q}", "input": "", "output": f"Lien transmédia détaillé : {a}"})
        
    return transmedia_instructions

def generate_awards_and_magazines_instructions():
    """Génère exactly 160 variations expertes en français pour les 40 relations d'awards et magazines."""
    instructions = []
    for relation in AWARDS_AND_MAGAZINES_RELATIONS:
        q = relation["question"]
        a = relation["answer"]
        
        # Variations
        instructions.append({"instruction": q, "input": "", "output": a})
        instructions.append({"instruction": f"Donne l'explication d'industrie ou de récompense associée à cette question : {q}", "input": "", "output": f"Explication d'industrie : {a}"})
        q_clean = q[0].lower() + q[1:]
        instructions.append({"instruction": f"En tant qu'expert de l'histoire du manga et de l'animation, saurais-tu me dire {q_clean}", "input": "", "output": a})
        instructions.append({"instruction": f"Analyse le contexte de publication ou de prix du sujet suivant : {q}", "input": "", "output": f"Analyse et contexte : {a}"})
    return instructions

def generate_songs_and_seiyuu_instructions():
    """Génère exactly 160 variations expertes en français pour les 40 relations de chansons d'animes et seiyuu."""
    instructions = []
    for relation in SONGS_AND_SEIYUU_RELATIONS:
        q = relation["question"]
        a = relation["answer"]
        
        # Variations
        instructions.append({"instruction": q, "input": "", "output": a})
        instructions.append({"instruction": f"Donne l'explication artistique, de doublage ou d'opening associée à cette question : {q}", "input": "", "output": f"Explication artistique : {a}"})
        q_clean = q[0].lower() + q[1:]
        instructions.append({"instruction": f"En tant qu'expert musical et de doublage de la japanimation, saurais-tu me dire {q_clean}", "input": "", "output": a})
        instructions.append({"instruction": f"Analyse le rôle musical ou l'identité de voix du sujet suivant : {q}", "input": "", "output": f"Analyse vocale et artistique : {a}"})
    return instructions

# --- GENERATEURS DE QUESTIONS SUR LE MARCHE FRANÇAIS ---

def generate_french_market_profile_instructions():
    """Génère 15 variations de Q&A pour chaque comédien, éditeur et plateforme du marché français (600 instructions)."""
    instructions = []
    
    # 1. Comédiens de doublage VF (15 * 15 = 225 instructions)
    for actor, data in FRENCH_VOICE_ACTORS.items():
        templates = [
            (f"Qui est '{actor}' dans le doublage français d'animés ?", f"Dans le doublage VF, '{actor}' est : {data['definition']}. Rôles cultes : {data['examples']}. Parcours : {data['origin']}"),
            (f"Présente-moi le parcours de la voix française culte '{actor}'.", f"Fiche de doublage - '{actor}' : {data['definition']} Carrière : {data['origin']}. Rôles en VF : {data['examples']}. Impact : {data['impact']}"),
            (f"Quels sont les rôles majeurs doublés par '{actor}' en version française ?", f"Les doublages de '{actor}' incluent : {data['examples']}. Il/Elle est connu(e) comme : {data['definition']}"),
            (f"En tant que spécialiste des voix françaises, que peux-tu me dire sur '{actor}' ?", f"Spécialité VF - '{actor}' : {data['definition']} Origines : {data['origin']}. Ses rôles phares : {data['examples']}"),
            (f"Pourquoi le doublage de '{actor}' a-t-il tant marqué le public français ?", f"Le doublage de '{actor}' est légendaire : {data['impact']} Il/Elle est reconnu(e) en tant que : {data['definition']}"),
            (f"Quels personnages célèbres ont la voix française de '{actor}' ?", f"Les figures doublées par '{actor}' comprennent : {data['examples']}. Style vocal : {data['origin']}"),
            (f"Fais-moi une synthèse complète de la carrière de doublage de '{actor}'.", f"Synthèse Doublage - '{actor}' : {data['definition']}. Histoire : {data['origin']}. Rôles repères : {data['examples']}. Impact : {data['impact']}"),
            (f"Peux-tu analyser l'importance de '{actor}' pour la VF de nos animés d'enfance ?", f"L'importance de '{actor}' en VF est colossale. {data['impact']} Connu pour : {data['definition']}. Rôles majeurs : {data['examples']}"),
            (f"Quel a été le rôle de '{actor}' au sein d'AB Production ou du doublage d'animes ?", f"'{actor}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Parcours : {data['origin']}"),
            (f"Donne des détails sur le timbre ou le registre de voix de '{actor}'.", f"Le timbre et registre de '{actor}' se caractérisent ainsi : {data['definition']}. Ses rôles phares : {data['examples']}. Style : {data['impact']}"),
            (f"Explique comment '{actor}' insuffle de la personnalité à ses doublages en français.", f"L'interprétation de '{actor}' se distingue par son énergie : {data['impact']} Notamment à travers : {data['definition']}. Rôles repères : {data['examples']}"),
            (f"Quelles sont les séries majeures où l'on peut apprécier le doublage de '{actor}' ?", f"On l'entend dans plusieurs animés cultes : {data['examples']}. Profil : {data['definition']}"),
            (f"Décris le parcours artistique et le profil vocal de '{actor}'.", f"Parcours de '{actor}' : {data['definition']}. Origines et évolutions : {data['origin']}. Rôles majeurs : {data['examples']}"),
            (f"Analyse l'importance historique et l'héritage de la voix de '{actor}' pour les otakus français.", f"L'héritage de '{actor}' est inestimable. {data['impact']} Connu pour : {data['definition']}. Rôles d'enfance : {data['examples']}"),
            (f"Qu'est-ce qui rend '{actor}' incontournable dans le paysage du doublage VF ?", f"'{actor}' est incontournable en tant que : {data['definition']}. Ses créations populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.")
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})
            
    # 2. Éditeurs de mangas en France (15 * 15 = 225 instructions)
    for publisher, data in FRENCH_MANGA_PUBLISHERS.items():
        templates = [
            (f"Qui est l'éditeur français '{publisher}' dans le milieu du manga ?", f"Sur le marché français, '{publisher}' est : {data['definition']}. Catalogue : {data['examples']}. Origines : {data['origin']}"),
            (f"Présente-moi le profil et l'impact sur le marché de l'éditeur '{publisher}'.", f"Fiche Éditeur - '{publisher}' : {data['definition']} Création : {data['origin']}. Mangas clés : {data['examples']}. Impact : {data['impact']}"),
            (f"Quelles sont les œuvres emblématiques publiées par '{publisher}' en France ?", f"Les licences phares éditées par '{publisher}' incluent : {data['examples']}. Il s'est imposé comme : {data['definition']}"),
            (f"En tant que spécialiste du marché du manga en France, que peux-tu me dire sur '{publisher}' ?", f"Marché français - '{publisher}' : {data['definition']} Histoire : {data['origin']}. Succès : {data['examples']}"),
            (f"Pourquoi l'éditeur '{publisher}' a-t-il rencontré un si grand succès en France ?", f"Le succès éditorial de '{publisher}' s'explique par sa ligne éditoriale : {data['impact']} Définition : {data['definition']}"),
            (f"Quels mangas célèbres sont publiés sous le label de '{publisher}' ?", f"Les titres édités par '{publisher}' comprennent : {data['examples']}. Démarche : {data['origin']}"),
            (f"Fais-moi une synthèse complète de l'historique de la maison d'édition '{publisher}'.", f"Synthèse Éditeur - '{publisher}' : {data['definition']}. Histoire : {data['origin']}. Catalogue repère : {data['examples']}. Impact : {data['impact']}"),
            (f"Peux-tu analyser l'importance de '{publisher}' pour la popularisation du manga en France ?", f"L'importance de '{publisher}' en France est colossale. {data['impact']} Connu pour : {data['definition']}. Succès majeurs : {data['examples']}"),
            (f"Quel a été le rôle de '{publisher}' dans l'importation de mangas shonen ou seinen ?", f"'{publisher}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Origines : {data['origin']}"),
            (f"Donne des détails sur la ligne éditoriale ou les traductions de '{publisher}'.", f"La ligne éditoriale de '{publisher}' se caractérise ainsi : {data['definition']}. Titres phares : {data['examples']}. Style : {data['impact']}"),
            (f"Explique comment '{publisher}' se démarque des autres éditeurs de mangas français.", f"La force de '{publisher}' réside dans son catalogue : {data['impact']} Définition : {data['definition']}. Œuvres repères : {data['examples']}"),
            (f"Quels sont les mangas majeurs que l'on doit lire chez '{publisher}' ?", f"On peut lire plusieurs œuvres majeures chez cet éditeur : {data['examples']}. Profil : {data['definition']}"),
            (f"Décris le parcours d'édition et le profil de '{publisher}'.", f"Parcours de '{publisher}' : {data['definition']}. Origines et évolutions : {data['origin']}. Catalogues majeurs : {data['examples']}"),
            (f"Analyse l'importance historique et l'héritage de '{publisher}' pour les lecteurs français.", f"L'héritage de '{publisher}' est inestimable. {data['impact']} Définition : {data['definition']}. Succès clés : {data['examples']}"),
            (f"Qu'est-ce qui rend '{publisher}' incontournable dans les librairies françaises ?", f"'{publisher}' est incontournable en tant que : {data['definition']}. Ses séries populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.")
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})
            
    # 3. Distributeurs et sites de streaming d'animés (10 * 15 = 150 instructions)
    for distributor, data in FRENCH_ANIME_DISTRIBUTORS.items():
        templates = [
            (f"Qu'est-ce que la plateforme ou distributeur français '{distributor}' ?", f"Sur le marché français, '{distributor}' est : {data['definition']}. Catalogue : {data['examples']}. Origines : {data['origin']}"),
            (f"Présente-moi le profil et l'impact sur le streaming ou le physique de '{distributor}'.", f"Fiche Distributeur - '{distributor}' : {data['definition']} Lancement : {data['origin']}. Animés : {data['examples']}. Impact : {data['impact']}"),
            (f"Quels sont les animés phares diffusés par '{distributor}' en France ?", f"Les licences majeures diffusées par '{distributor}' incluent : {data['examples']}. Il s'est imposé comme : {data['definition']}"),
            (f"En tant que spécialiste de la diffusion d'animés en France, que peux-tu me dire sur '{distributor}' ?", f"Diffusion France - '{distributor}' : {data['definition']} Contexte : {data['origin']}. Succès : {data['examples']}"),
            (f"Pourquoi le service de '{distributor}' s'est-il imposé dans l'Hexagone ?", f"Le succès s'explique par sa distribution : {data['impact']} Définition : {data['definition']}"),
            (f"Quels animés célèbres sont disponibles chez '{distributor}' ?", f"Les titres diffusés par '{distributor}' comprennent : {data['examples']}. Démarche : {data['origin']}"),
            (f"Fais-moi une synthèse complète de l'histoire du diffuseur ou distributeur '{distributor}'.", f"Synthèse Diffusion - '{distributor}' : {data['definition']}. Histoire : {data['origin']}. Catalogue repère : {data['examples']}. Impact : {data['impact']}"),
            (f"Peux-tu analyser l'importance de '{distributor}' pour le marché français de la japanimation ?", f"L'importance de '{distributor}' en France est colossale. {data['impact']} Connu pour : {data['definition']}. Succès majeurs : {data['examples']}"),
            (f"Quel a été le rôle de '{distributor}' dans le développement du simulcast ou du physique ?", f"'{distributor}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Origines : {data['origin']}"),
            (f"Donne des détails sur le mode de fonctionnement ou l'histoire de '{distributor}'.", f"Le service de '{distributor}' se caractérise ainsi : {data['definition']}. Titres phares : {data['examples']}. Style : {data['impact']}"),
            (f"Explique comment '{distributor}' a transformé la consommation légale d'animés en France.", f"La force réside dans son catalogue : {data['impact']} Définition : {data['definition']}. Œuvres repères : {data['examples']}"),
            (f"Quels sont les animés majeurs que l'on doit regarder chez '{distributor}' ?", f"On peut regarder plusieurs œuvres majeures chez ce diffuseur : {data['examples']}. Profil : {data['definition']}"),
            (f"Décris le parcours de diffusion et le profil de '{distributor}'.", f"Parcours de '{distributor}' : {data['definition']}. Origines et évolutions : {data['origin']}. Catalogues majeurs : {data['examples']}"),
            (f"Analyse l'importance historique et l'héritage de '{distributor}' pour les passionnés français.", f"L'héritage de '{distributor}' est inestimable. {data['impact']} Connu pour : {data['definition']}. Succès de diffusion : {data['examples']}"),
            (f"Qu'est-ce qui rend '{distributor}' incontournable dans le streaming d'animés moderne ?", f"'{distributor}' est incontournable en tant que : {data['definition']}. Ses séries populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.")
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})
            
    return instructions

def generate_french_market_relations_instructions():
    """Génère 4 variations pour chacune des 40 relations du marché français (160 instructions)."""
    instructions = []
    for relation in FRENCH_MARKET_RELATIONS:
        q = relation["question"]
        a = relation["answer"]
        
        # Variations
        instructions.append({"instruction": q, "input": "", "output": a})
        instructions.append({"instruction": f"Donne l'explication et le contexte de cette question sur le marché français de japanimation : {q}", "input": "", "output": f"Explication du marché français : {a}"})
        q_clean = q[0].lower() + q[1:]
        instructions.append({"instruction": f"En tant que spécialiste de l'histoire du manga et de l'animation en France, saurais-tu me dire {q_clean}", "input": "", "output": a})
        instructions.append({"instruction": f"Analyse le contexte d'édition, de doublage ou de distribution du sujet suivant : {q}", "input": "", "output": f"Analyse et contexte français : {a}"})
    return instructions

def generate_volumes_and_episodes_instructions():
    """Génère des instructions détaillées sur le nombre d'épisodes, de saisons et de tomes (volumes) pour les animés/mangas phares."""
    instructions = []
    for title, data in VOLUMES_AND_EPISODES_DATA.items():
        # Templates de questions/réponses
        templates = [
            (f"Combien d'épisodes et de saisons compte l'adaptation en animé de '{title}' ?",
             f"L'adaptation animée de '{title}' se structure ainsi : {data['anime_episodes']} répartis sur {data['anime_seasons']}. Statut général : {data['status']}. {data['details']}"),
            
            (f"Quel est le nombre total de tomes (volumes) parus pour le manga '{title}' et est-il terminé ?",
             f"Le manga '{title}' compte : {data['manga_volumes']}. Statut de parution : {data['status']}. {data['details']}"),
            
            (f"Fais-moi un récapitulatif complet du format (nombre d'épisodes, de saisons et de tomes) de '{title}'.",
             f"Voici le récapitulatif complet des formats pour '{title}' :\n- **Manga :** {data['manga_volumes']}.\n- **Animé :** {data['anime_episodes']} au fil de {data['anime_seasons']}.\n- **Statut global :** {data['status']}.\n- **Détails & contexte :** {data['details']}"),
            
            (f"Donne-moi des détails sur la parution du manga et le nombre d'épisodes de l'anime '{title}'.",
             f"Pour '{title}', voici les détails d'industrie :\n- **Manga :** {data['manga_volumes']}.\n- **Épisodes & Saisons :** {data['anime_episodes']} sur {data['anime_seasons']}.\n- **Statut actuel :** {data['status']}.\n- **Informations complémentaires :** {data['details']}")
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})
    return instructions

def fetch_general_instructions(count):
    """Télécharge de manière stable 'pinzhenchen/alpaca-cleaned-fr' depuis HF Hub."""
    logger.info(f"[INFO] Loading {count} general French SFT instructions from Hugging Face...")
    ds = load_dataset('pinzhenchen/alpaca-cleaned-fr', split='train')
    
    general_samples = []
    for i in range(min(count, len(ds))):
        item = ds[i]
        general_samples.append({
            "instruction": item.get("instruction", ""),
            "input": item.get("input", ""),
            "output": item.get("output", "")
        })
    logger.info(f"[SUCCESS] Loaded exactly {len(general_samples)} general SFT instructions.")
    return general_samples

def deduplicate_dataset(dataset):
    seen = set()
    deduped = []
    duplicates_count = 0
    for item in dataset:
        key = (item["instruction"].strip(), item["input"].strip())
        if key in seen:
            duplicates_count += 1
            continue
        seen.add(key)
        deduped.append(item)
    logger.info(f"[INFO] Deduplication removed {duplicates_count} duplicate SFT pairs.")
    return deduped

def generate_mcp_tool_instructions() -> List[dict]:
    """
    Génère des exemples d'entraînement SFT pour apprendre au modèle expert
    à appeler des serveurs MCP (Jikan et Spotify) et à en traiter les réponses.
    Génère ~250 variations.
    """
    instructions = []
    
    # Éléments de données pour l'injection
    titles = [
        "Kimetsu no Yaiba", "Shingeki no Kyojin", "One Piece", "Naruto",
        "Jujutsu Kaisen", "Boku no Hero Academia", "Hunter x Hunter",
        "Fullmetal Alchemist", "Steins;Gate", "Bleach", "Chainsaw Man"
    ]
    
    studios = ["Ufotable", "MAPPA", "Wit Studio", "Madhouse", "Bones", "Pierrot", "Toei Animation"]
    
    tracks_data = [
        {"track": "Gurenge", "artist": "LiSA", "album": "Leo-Nine", "popularity": 85, "track_id": "0TrPqh5AaXEtzd52oKM769"},
        {"track": "Idol", "artist": "YOASOBI", "album": "Idol", "popularity": 92, "track_id": "2d1FDF2v80pB8E9f69b82F"},
        {"track": "Kaikai Kitan", "artist": "Eve", "album": "Kaikai Kitan", "popularity": 80, "track_id": "0yEvEvEve0py1EvE83jf8e"},
        {"track": "Shinzou wo Sasageyo!", "artist": "Linked Horizon", "album": "Shinzou wo Sasageyo", "popularity": 88, "track_id": "2SASASASA038sasasasas"},
        {"track": "Zankyou Sanka", "artist": "Aimer", "album": "Zankyou Sanka", "popularity": 84, "track_id": "3AiAiAimer039aierarera"},
        {"track": "Unravel", "artist": "TK from Ling Tosite Sigure", "album": "Fantastic Magic", "popularity": 87, "track_id": "0TkTkTkTk038tktktktkt"},
        {"track": "Sign", "artist": "FLOW", "album": "FLOW ANIME BEST", "popularity": 79, "track_id": "0FlFlFlFl038flflflflf"},
        {"track": "The Rumbling", "artist": "SiM", "album": "The Rumbling", "popularity": 86, "track_id": "0SiMSiMSiM038simsimsim"}
    ]
    
    artists = ["LiSA", "YOASOBI", "Aimer", "Eve", "FLOW", "Linked Horizon", "SiM", "Kenshi Yonezu", "RADWIMPS"]
    
    characters_data = [
        {"title": "Kimetsu no Yaiba", "char1": "Tanjiro Kamado", "va1": "Natsuki Hanae", "char2": "Nezuko Kamado", "va2": "Akari Kito"},
        {"title": "Shingeki no Kyojin", "char1": "Eren Yeager", "va1": "Yuki Kaji", "char2": "Mikasa Ackerman", "va2": "Yui Ishikawa"},
        {"title": "One Piece", "char1": "Monkey D. Luffy", "va1": "Mayumi Tanaka", "char2": "Roronoa Zoro", "va2": "Kazuya Nakai"},
        {"title": "Jujutsu Kaisen", "char1": "Yuji Itadori", "va1": "Junya Enoki", "char2": "Satoru Gojo", "va2": "Yuichi Nakamura"},
        {"title": "Boku no Hero Academia", "char1": "Izuku Midoriya", "va1": "Daiki Yamashita", "char2": "Katsuki Bakugo", "va2": "Nobuhiko Okamoto"},
        {"title": "Hunter x Hunter", "char1": "Gon Freecss", "va1": "Megumi Han", "char2": "Killua Zoldyck", "va2": "Mariya Ise"}
    ]

    # --- 1. JIKAN SEARCH ANIME & DETAILS ---
    for title in titles:
        # Tool Call Generation
        q_templates = [
            f"Recherche les détails de l'anime '{title}' sur MyAnimeList pour voir sa note et ses épisodes.",
            f"Peux-tu interroger MyAnimeList (Jikan) pour l'anime '{title}' ?",
            f"Donne-moi les infos en temps réel de '{title}' depuis MAL.",
            f"Cherche l'anime '{title}' sur MAL avec l'API Jikan."
        ]
        
        for q in q_templates:
            tool_call_json = {
                "server": "jikan",
                "tool": "search_anime",
                "arguments": {
                    "query": title
                }
            }
            instructions.append({
                "instruction": q,
                "input": "",
                "output": f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False, indent=2)}\n</tool_call>"
            })

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
                    "studios": [studio]
                }
            }
            
            q_proc = f"Recherche les détails de l'anime '{title}' sur MyAnimeList."
            ans = f"D'après les informations obtenues en temps réel via MyAnimeList (Jikan), l'anime '{title}' comporte {episodes} épisodes, est produit par le studio {studio} et obtient une note globale de {score}/10."
            
            instructions.append({
                "instruction": q_proc,
                "input": f"<tool_response>\n{json.dumps(tool_response_json, ensure_ascii=False, indent=2)}\n</tool_response>",
                "output": ans
            })

    # --- 2. JIKAN ANIME CHARACTERS ---
    for char_info in characters_data:
        t = char_info["title"]
        q_templates = [
            f"Trouve la liste des personnages et doublages pour l'anime '{t}'.",
            f"Qui double les personnages principaux de '{t}' ? Interroge Jikan.",
            f"Quels sont les seiyuu et personnages principaux de '{t}' sur MyAnimeList ?"
        ]
        
        for q in q_templates:
            tool_call_json = {
                "server": "jikan",
                "tool": "get_anime_characters",
                "arguments": {
                    "query": t
                }
            }
            instructions.append({
                "instruction": q,
                "input": "",
                "output": f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False, indent=2)}\n</tool_call>"
            })
            
        # Tool Response Processing
        tool_response_json = {
            "status": "success",
            "data": {
                "characters": [
                    {"name": char_info["char1"], "role": "Main", "voice_actor": char_info["va1"]},
                    {"name": char_info["char2"], "role": "Supporting", "voice_actor": char_info["va2"]}
                ]
            }
        }
        
        q_proc = f"Trouve la liste des personnages et doublages pour l'anime '{t}'."
        ans = f"Voici les personnages principaux et leurs seiyuu officiels pour '{t}' :\n- **{char_info['char1']}** (rôle principal), doublé par {char_info['va1']}.\n- **{char_info['char2']}** (rôle de soutien), doublé par {char_info['va2']}."
        
        instructions.append({
            "instruction": q_proc,
            "input": f"<tool_response>\n{json.dumps(tool_response_json, ensure_ascii=False, indent=2)}\n</tool_response>",
            "output": ans
        })

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
            f"Cherche la musique '{tr}' via l'API Spotify."
        ]
        
        for q in q_templates:
            tool_call_json = {
                "server": "spotify",
                "tool": "search_track",
                "arguments": {
                    "query": f"{art} {tr}"
                }
            }
            instructions.append({
                "instruction": q,
                "input": "",
                "output": f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False, indent=2)}\n</tool_call>"
            })

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
                        "spotify_url": f"https://open.spotify.com/track/{tr_id}"
                    }
                ]
            }
        }
        
        q_proc = f"Recherche le morceau '{tr}' sur Spotify."
        ans = f"La chanson '{tr}' interprétée par {art} est disponible sur Spotify. Elle figure sur l'album '{alb}' avec un indice de popularité de {pop}/100. Vous pouvez l'écouter ici : https://open.spotify.com/track/{tr_id}."
        
        instructions.append({
            "instruction": q_proc,
            "input": f"<tool_response>\n{json.dumps(tool_response_json, ensure_ascii=False, indent=2)}\n</tool_response>",
            "output": ans
        })

    # --- 4. SPOTIFY ARTIST TOP TRACKS ---
    for art in artists:
        q_templates = [
            f"Quels sont les morceaux les plus populaires de '{art}' sur Spotify ?",
            f"Affiche le top des écoutes de '{art}' sur Spotify.",
            f"Interroge Spotify pour avoir les meilleurs titres de '{art}'."
        ]
        
        for q in q_templates:
            tool_call_json = {
                "server": "spotify",
                "tool": "get_artist_top_tracks",
                "arguments": {
                    "artist_name": art
                }
            }
            instructions.append({
                "instruction": q,
                "input": "",
                "output": f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False, indent=2)}\n</tool_call>"
            })

        # Tool Response Processing
        t1, t2, t3 = f"Track A de {art}", f"Track B de {art}", f"Track C de {art}"
        p1, p2, p3 = random.randint(85, 95), random.randint(75, 84), random.randint(65, 74)
        
        tool_response_json = {
            "status": "success",
            "data": {
                "artist": art,
                "top_tracks": [
                    {"name": t1, "popularity": p1},
                    {"name": t2, "popularity": p2},
                    {"name": t3, "popularity": p3}
                ]
            }
        }
        
        q_proc = f"Quels sont les morceaux les plus populaires de '{art}' sur Spotify ?"
        ans = f"Sur Spotify, les titres les plus écoutés de l'artiste '{art}' sont :\n1. **{t1}** (popularité: {p1}/100)\n2. **{t2}** (popularité: {p2}/100)\n3. **{t3}** (popularité: {p3}/100)"
        
        instructions.append({
            "instruction": q_proc,
            "input": f"<tool_response>\n{json.dumps(tool_response_json, ensure_ascii=False, indent=2)}\n</tool_response>",
            "output": ans
        })

    return instructions

# --- METHODE D'ASSEMBLAGE UNIFIEE ---

def run_generate_instruction_dataset():
    specialized_data = []

    # Initialisation client Gemini pour augmentation facultative
    augment_data = os.getenv("ANIMETIX_AUGMENT_DATA", "False").lower() in ("true", "1")
    api_key = os.getenv("GEMINI_API_KEY")
    client = None
    if augment_data and api_key and genai is not None:
        logger.info("[INFO] Initializing Gemini API client for data augmentation...")
        client = genai.Client(api_key=api_key)
    else:
        logger.info("[INFO] Gemini API client not initialized (augmentation disabled or missing key). Using static templates.")

    # Limites d'augmentation pour maîtriser les coûts et le temps d'exécution
    limit_anime_t1 = int(os.getenv("ANIMETIX_LIMIT_ANIME_T1", "15"))
    limit_anime_t2 = int(os.getenv("ANIMETIX_LIMIT_ANIME_T2", "10"))
    limit_manga_t1 = int(os.getenv("ANIMETIX_LIMIT_MANGA_T1", "5"))
    limit_manga_t2 = int(os.getenv("ANIMETIX_LIMIT_MANGA_T2", "5"))
    limit_char_t1 = int(os.getenv("ANIMETIX_LIMIT_CHAR_T1", "15"))
    limit_char_t2 = int(os.getenv("ANIMETIX_LIMIT_CHAR_T2", "10"))

    # Établir la liste des éléments éligibles à l'augmentation par tri de popularité
    augmented_anime_titles = set()
    if os.path.exists(ANIME_DB) and client:
        try:
            with open(ANIME_DB, 'r', encoding='utf-8') as f:
                animes_list = json.load(f)
                t1_animes = [item for item in animes_list if item.get('popularity', 0) > 150000]
                t1_animes.sort(key=lambda x: x.get('popularity', 0), reverse=True)
                for item in t1_animes[:limit_anime_t1]:
                    if item.get('title'):
                        augmented_anime_titles.add(item.get('title'))
                
                t2_animes = [item for item in animes_list if 50000 < item.get('popularity', 0) <= 150000]
                t2_animes.sort(key=lambda x: x.get('popularity', 0), reverse=True)
                for item in t2_animes[:limit_anime_t2]:
                    if item.get('title'):
                        augmented_anime_titles.add(item.get('title'))
            logger.info(f"[INFO] Targeted {len(augmented_anime_titles)} popular animes for dynamic augmentation.")
        except Exception as e:
            logger.warning(f"Failed to identify target animes for augmentation: {e}")

    augmented_manga_titles = set()
    if os.path.exists(MANGA_DB) and client:
        try:
            with open(MANGA_DB, 'r', encoding='utf-8') as f:
                mangas_list = json.load(f)
                t1_mangas = [item for item in mangas_list if item.get('popularity', 0) > 150000]
                t1_mangas.sort(key=lambda x: x.get('popularity', 0), reverse=True)
                for item in t1_mangas[:limit_manga_t1]:
                    if item.get('title'):
                        augmented_manga_titles.add(item.get('title'))
                
                t2_mangas = [item for item in mangas_list if 50000 < item.get('popularity', 0) <= 150000]
                t2_mangas.sort(key=lambda x: x.get('popularity', 0), reverse=True)
                for item in t2_mangas[:limit_manga_t2]:
                    if item.get('title'):
                        augmented_manga_titles.add(item.get('title'))
            logger.info(f"[INFO] Targeted {len(augmented_manga_titles)} popular mangas for dynamic augmentation.")
        except Exception as e:
            logger.warning(f"Failed to identify target mangas for augmentation: {e}")

    augmented_char_names = set()
    if os.path.exists(CHAR_DB) and client:
        try:
            with open(CHAR_DB, 'r', encoding='utf-8') as f:
                chars_list = json.load(f)
                top_chars_list = [c for c in chars_list if c.get('popularity', {}).get('favourites', 0) > 50]
                
                t1_chars = [c for c in top_chars_list if c.get('popularity', {}).get('favourites', 0) > 2000]
                t1_chars.sort(key=lambda x: x.get('popularity', {}).get('favourites', 0), reverse=True)
                for item in t1_chars[:limit_char_t1]:
                    if item.get('name') and item.get('origin'):
                        augmented_char_names.add((item.get('name'), item.get('origin')))
                
                t2_chars = [c for c in top_chars_list if 500 < c.get('popularity', {}).get('favourites', 0) <= 2000]
                t2_chars.sort(key=lambda x: x.get('popularity', {}).get('favourites', 0), reverse=True)
                for item in t2_chars[:limit_char_t2]:
                    if item.get('name') and item.get('origin'):
                        augmented_char_names.add((item.get('name'), item.get('origin')))
            logger.info(f"[INFO] Targeted {len(augmented_char_names)} popular characters for dynamic augmentation.")
        except Exception as e:
            logger.warning(f"Failed to identify target characters for augmentation: {e}")

    # 1. TRANSMEDIA BRIDGES (400 instructions en français)
    logger.info("[INFO] Generating high-quality transmedia bridge instructions...")
    transmedia_data = generate_transmedia_instructions()
    specialized_data.extend(transmedia_data)

    # 1b. MAGAZINES AND AWARDS (160 instructions en français)
    logger.info("[INFO] Generating high-quality magazines and awards relational instructions...")
    awards_mag_data = generate_awards_and_magazines_instructions()
    specialized_data.extend(awards_mag_data)

    # 1c. SONGS AND SEIYUU (160 instructions en français)
    logger.info("[INFO] Generating high-quality openings, endings, and seiyuu relational instructions...")
    songs_seiyuu_data = generate_songs_and_seiyuu_instructions()
    specialized_data.extend(songs_seiyuu_data)

    # 1d. PAYSAGE FRANÇAIS - RELATIONS (160 instructions en français)
    logger.info("[INFO] Generating high-quality French market relational instructions...")
    french_relations = generate_french_market_relations_instructions()
    specialized_data.extend(french_relations)

    # 1e. PAYSAGE FRANÇAIS - PROFILS (600 instructions en français)
    logger.info("[INFO] Generating high-quality French voice actors, publishers, and distributors profile instructions...")
    french_profiles = generate_french_market_profile_instructions()
    specialized_data.extend(french_profiles)

    # 1f. VOLUMES ET EPISODES (72 instructions en français)
    logger.info("[INFO] Generating high-quality manga volumes and anime episodes instructions...")
    vol_ep_data = generate_volumes_and_episodes_instructions()
    specialized_data.extend(vol_ep_data)
    
    # 1g. CADRAGE D'OUTILS VIA MCP (serveurs Jikan & Spotify)
    logger.info("[INFO] Generating high-quality MCP tool calling instructions...")
    mcp_data = generate_mcp_tool_instructions()
    specialized_data.extend(mcp_data)
    
    # 2. ANIME DATABASE
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, 'r', encoding='utf-8') as f:
            animes = json.load(f)
            logger.info(f"[INFO] Processing ALL {len(animes)} animes with popularity weighting...")
            for item in animes:
                title = clean_description(item.get('title', 'Unknown'))
                genres = [clean_description(g) for g in item.get('genres', [])]
                studios = [clean_description(s) for s in item.get('studios', [])]
                tags = [clean_description(t) for t in item.get('tags', [])]
                pop = item.get('popularity', 0)
                year = item.get('year', 2020)
                
                profile = make_french_anime_profile(title, genres, studios, tags, year)
                display_t = get_display_title(title)
                
                # Tier 1 : Ultra Populaire (> 150k membres) -> 5 variations
                if pop > 150000:
                    if client and title in augmented_anime_titles:
                        logger.info(f"Augmenting anime (Tier 1) '{title}' via Gemini...")
                        p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                        p2 = paraphrase_text_via_gemini(profile, client, "critique")
                        p3 = paraphrase_text_via_gemini(profile, client, "enthousiaste")
                        p4 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        p5 = paraphrase_text_via_gemini(profile, client, "analytique")
                    else:
                        p1 = p2 = p3 = p4 = p5 = profile
                    specialized_data.append({"instruction": f"Présente l'anime culte '{display_t}' de manière extrêmement détaillée.", "input": "", "output": p1})
                    specialized_data.append({"instruction": f"Quel studio est derrière le chef-d'œuvre '{display_t}' et de quoi s'agit-il ?", "input": "", "output": p2})
                    specialized_data.append({"instruction": f"De quoi parle l'œuvre majeure '{display_t}' ?", "input": "", "output": p3})
                    specialized_data.append({"instruction": f"Quelles sont les thématiques majeures et l'univers de '{display_t}' ?", "input": "", "output": p4})
                    specialized_data.append({"instruction": f"Pourquoi '{display_t}' est-elle une œuvre extrêmement populaire et appréciée des spectateurs ?", "input": "", "output": p5})
                
                # Tier 2 : Très Populaire (50k - 150k membres) -> 3 variations
                elif pop > 50000:
                    if client and title in augmented_anime_titles:
                        logger.info(f"Augmenting anime (Tier 2) '{title}' via Gemini...")
                        p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                        p2 = paraphrase_text_via_gemini(profile, client, "critique")
                        p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                    else:
                        p1 = p2 = p3 = profile
                    specialized_data.append({"instruction": f"Présente l'anime populaire '{display_t}' de manière détaillée.", "input": "", "output": p1})
                    specialized_data.append({"instruction": f"Quel studio a produit '{display_t}' et de quoi ça parle ?", "input": "", "output": p2})
                    specialized_data.append({"instruction": f"Quelles sont les thématiques majeures de l'anime '{display_t}' ?", "input": "", "output": p3})
                
                # Tier 3 : Standard / Obscure (<= 50k membres) -> 1 variation
                else:
                    specialized_data.append({"instruction": f"Présente l'anime '{display_t}' de manière détaillée.", "input": "", "output": profile})

    # 3. MANGA DATABASE
    if os.path.exists(MANGA_DB):
        with open(MANGA_DB, 'r', encoding='utf-8') as f:
            mangas = json.load(f)
            logger.info(f"[INFO] Processing ALL {len(mangas)} mangas with popularity weighting...")
            for item in mangas:
                title = clean_description(item.get('title', 'Unknown'))
                genres = [clean_description(g) for g in item.get('genres', [])]
                tags = [clean_description(t) for t in item.get('tags', [])]
                pop = item.get('popularity', 0)
                
                profile = make_french_manga_profile(title, genres, tags)
                display_t = get_display_title(title)
                
                # Tier 1 : Ultra Populaire (> 150k membres) -> 5 variations
                if pop > 150000:
                    if client and title in augmented_manga_titles:
                        logger.info(f"Augmenting manga (Tier 1) '{title}' via Gemini...")
                        p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                        p2 = paraphrase_text_via_gemini(profile, client, "critique")
                        p3 = paraphrase_text_via_gemini(profile, client, "enthousiaste")
                        p4 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        p5 = paraphrase_text_via_gemini(profile, client, "analytique")
                    else:
                        p1 = p2 = p3 = p4 = p5 = profile
                    specialized_data.append({"instruction": f"Quelles sont les thématiques principales du manga culte '{display_t}' ?", "input": "", "output": p1})
                    specialized_data.append({"instruction": f"Analyse et résume le manga emblématique '{display_t}'.", "input": "", "output": p2})
                    specialized_data.append({"instruction": f"Pourquoi le manga '{display_t}' a-t-il rencontré un si grand succès auprès du public ?", "input": "", "output": p3})
                    specialized_data.append({"instruction": f"Présente l'univers et le scénario du manga culte '{display_t}'.", "input": "", "output": p4})
                    specialized_data.append({"instruction": f"De quoi parle le manga culte '{display_t}' ?", "input": "", "output": p5})
                
                # Tier 2 : Très Populaire (50k - 150k membres) -> 3 variations
                elif pop > 50000:
                    if client and title in augmented_manga_titles:
                        logger.info(f"Augmenting manga (Tier 2) '{title}' via Gemini...")
                        p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                        p2 = paraphrase_text_via_gemini(profile, client, "critique")
                        p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                    else:
                        p1 = p2 = p3 = profile
                    specialized_data.append({"instruction": f"Quelles sont les thématiques principales du manga populaire '{display_t}' ?", "input": "", "output": p1})
                    specialized_data.append({"instruction": f"De quoi parle le manga populaire '{display_t}' ?", "input": "", "output": p2})
                    specialized_data.append({"instruction": f"Résume les thèmes clés du manga '{display_t}'.", "input": "", "output": p3})
                
                # Tier 3 : Standard / Obscure (<= 50k membres) -> 1 variation
                else:
                    specialized_data.append({"instruction": f"Quelles sont les thématiques principales du manga '{display_t}' ?", "input": "", "output": profile})

    # 4. CHARACTER DATABASE
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, 'r', encoding='utf-8') as f:
            chars = json.load(f)
            top_chars = [c for c in chars if c.get('popularity', {}).get('favourites', 0) > 50]
            logger.info(f"[INFO] Processing {len(top_chars)} characters with tiered augmentation...")
            
            for c in top_chars:
                name = clean_description(c.get('name', 'Anonyme'))
                origin = clean_description(c.get('origin', 'Inconnu'))
                ents = c.get('entities', {})
                orgs = [clean_description(o) for o in ents.get('organizations', [])]
                favs = c.get('popularity', {}).get('favourites', 0)
                rank = c.get('popularity', {}).get('rank', 9999)
                height = clean_description(c.get('metadata', {}).get('height', 'Unknown'))
                
                profile = make_french_character_bio(name, origin, orgs, favs, rank, height)
                display_name = get_display_character(name)
                display_origin = get_display_title(origin)
                
                # Tier 1 : Ultra Populaire (> 2000 favoris) -> 5 variations
                if favs > 2000:
                    if client and (name, origin) in augmented_char_names:
                        logger.info(f"Augmenting character (Tier 1) '{name}' ({origin}) via Gemini...")
                        p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                        p2 = paraphrase_text_via_gemini(profile, client, "critique")
                        p3 = paraphrase_text_via_gemini(profile, client, "enthousiaste")
                        p4 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        p5 = paraphrase_text_via_gemini(profile, client, "analytique")
                    else:
                        p1 = p2 = p3 = p4 = p5 = profile
                    specialized_data.append({"instruction": f"Analyse complète du personnage culte {display_name} dans {display_origin}.", "input": "", "output": p1})
                    specialized_data.append({"instruction": f"Qui est {display_name} ?", "input": f"Contexte : {display_origin}", "output": p2})
                    specialized_data.append({"instruction": f"Analyse approfondie de la psychologie et du rôle de {display_name} dans '{display_origin}'.", "input": "", "output": p3})
                    specialized_data.append({"instruction": f"Quels sont les traits marquants et l'importance du personnage de {display_name} ?", "input": f"Œuvre d'origine : {display_origin}", "output": p4})
                    specialized_data.append({"instruction": f"Pourquoi {display_name} est-il l'un des personnages les plus emblématiques et adorés de '{display_origin}' ?", "input": "", "output": p5})
                
                # Tier 2 : Très Populaire (500 - 2000 favoris) -> 3 variations
                elif favs > 500:
                    if client and (name, origin) in augmented_char_names:
                        logger.info(f"Augmenting character (Tier 2) '{name}' ({origin}) via Gemini...")
                        p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                        p2 = paraphrase_text_via_gemini(profile, client, "critique")
                        p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                    else:
                        p1 = p2 = p3 = profile
                    specialized_data.append({"instruction": f"Analyse le personnage populaire de {display_name} dans {display_origin}.", "input": "", "output": p1})
                    specialized_data.append({"instruction": f"Qui est {display_name} ?", "input": f"Contexte : {display_origin}", "output": p2})
                    specialized_data.append({"instruction": f"Quels sont les traits marquants du personnage de {display_name} dans '{display_origin}' ?", "input": "", "output": p3})
                
                # Tier 3 : Standard (50 - 500 favoris) -> 2 variations
                else:
                    specialized_data.append({"instruction": f"Analyse le personnage de {display_name} dans {display_origin}.", "input": "", "output": profile})
                    specialized_data.append({"instruction": f"Qui est {display_name} ?", "input": f"Contexte : {display_origin}", "output": profile})

    # Déduplication
    specialized_data = deduplicate_dataset(specialized_data)
    non_meta_count = len(specialized_data)
    
    # 5. RATIO CONFIGURABLE ET PARAMETRABLE (Défaut : 80% Spécialisé, 5% Meta, 15% Général)
    meta_required, general_required = calculate_dataset_counts(non_meta_count)
    
    logger.info(f"[INFO] Total Non-meta (80% target) instructions generated: {non_meta_count}")
    logger.info(f"[INFO] Target Meta required (5% target): {meta_required}")
    logger.info(f"[INFO] Target General required (15% target): {general_required}")
    
    # Pool de questions méta
    logger.info("[INFO] Generating high-quality Otaku Meta Vocabulary questions pool...")
    meta_pool = generate_otaku_meta_instructions()
    meta_pool = deduplicate_dataset(meta_pool)
    
    # Échantillonnage
    if meta_required <= len(meta_pool):
        selected_meta = random.sample(meta_pool, meta_required)
    else:
        selected_meta = list(meta_pool)
        diff_needed = meta_required - len(meta_pool)
        paraphrases = [
            ("En tant que grand sage Otaku, explique-moi : {q}", "{a}"),
            ("Je voudrais une analyse experte de : {q}", "{a}"),
            ("Peux-tu vulgariser ce concept Otaku : {q}", "Voici l'explication : {a}"),
            ("Décris-moi en détail : {q}", "{a}"),
            ("Fais un focus sur la notion de : {q}", "Focus expert : {a}"),
            ("Pourrais-tu détailler le concept de : {q}", "{a}"),
            ("Donne-moi l'analyse d'expert sur le trope : {q}", "{a}")
        ]
        extra_meta = []
        while len(extra_meta) < diff_needed:
            base_item = random.choice(meta_pool)
            p_template, a_template = random.choice(paraphrases)
            new_instruction = p_template.format(q=base_item["instruction"])
            new_output = a_template.format(a=base_item["output"])
            extra_meta.append({
                "instruction": new_instruction,
                "input": base_item["input"],
                "output": new_output
            })
        selected_meta.extend(extra_meta)
    
    # Téléchargement stable de pinzhenchen/alpaca-cleaned-fr
    general_data = fetch_general_instructions(general_required)
    
    # Assemblage unifié
    final_dataset = []
    final_dataset.extend(specialized_data)
    final_dataset.extend(selected_meta)
    final_dataset.extend(general_data)
    
    # Mélange global
    logger.info("[INFO] Shuffling the unified massive dataset...")
    random.shuffle(final_dataset)
    
    # Sauvegarde finale en JSONL
    os.makedirs(os.path.dirname(OUTPUT_DATASET), exist_ok=True)
    with open(OUTPUT_DATASET, 'w', encoding='utf-8') as f:
        for entry in final_dataset:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
    total_count = len(final_dataset)
    actual_spec_ratio = len(specialized_data) / total_count * 100
    actual_meta_ratio = len(selected_meta) / total_count * 100
    actual_gen_ratio = len(general_data) / total_count * 100
    
    logger.info(f"[SUCCESS] UNIFIED MASSIVE AND OPTIMIZED DATASET READY: {total_count} total instructions.")
    logger.info(f"[INFO] Final Ratios Check:")
    logger.info(f"  - Specialized, Bridges & French Market (80% target): {len(specialized_data)} / {total_count} ({actual_spec_ratio:.2f}%)")
    logger.info(f"  - Otaku Meta-Vocabulary (5% target): {len(selected_meta)} / {total_count} ({actual_meta_ratio:.2f}%)")
    logger.info(f"  - General French SFT (15% target): {len(general_data)} / {total_count} ({actual_gen_ratio:.2f}%)")
    logger.info(f"[INFO] Saved at: {OUTPUT_DATASET}")
    
    # Sauvegarde du cache
    save_paraphrase_cache()

if __name__ == "__main__":
    run_generate_instruction_dataset()
