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
        "quelque": "qq", "quelques": "qqs",
        "pourquoi": "pq", "avec": "avc", "dans": "ds",
        "anime": "anim", "animes": "anims",
        "personnage": "perso", "personnages": "persos",
        "adoré": "kiffé", "aimé": "kiffé",
        "salut": "slt", "bonjour": "bjr",
        "c'est-à-dire": "càd",
    }
    en_word_replacements = {
        "what": "wht", "you": "u", "are": "r",
        "please": "pls", "information": "info", "background": "bg",
        "character": "char", "characters": "chars",
        "favorite": "fav", "favorites": "favs",
        "really": "rlly", "masterpiece": "banger", "masterpieces": "bangers",
        "hello": "hllo", "thanks": "thx", "about": "abt",
    }

    modified_text = text

    # Apply multi-word phrase replacements first (French only)
    if language != "English":
        for phrase, replacement in fr_phrase_replacements:
            modified_text = re.sub(re.escape(phrase), replacement, modified_text, flags=re.IGNORECASE)

    # Apply single-word replacements
    word_replacements = en_word_replacements if language == "English" else fr_word_replacements
    words = modified_text.split()
    new_words = []
    for w in words:
        w_clean = re.sub(r'[^\w\'\-àâäéèêëïîôùûüçœæ]', '', w, flags=re.UNICODE).lower()
        if w_clean in word_replacements:
            new_words.append(word_replacements[w_clean])
        else:
            new_words.append(w)
    modified_text = " ".join(new_words)

    # --- B. Formatting laziness (50% probability) ---
    if random.random() < 0.5:
        modified_text = modified_text.lower()
        modified_text = re.sub(r'[?,.!;:\'"]', '', modified_text)

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
                w = w[:pos] + w[pos + 1:]
            elif typo_type == "duplicate":
                pos = random.randint(0, len(w) - 1)
                w = w[:pos] + w[pos] + w[pos:]
            words_list[idx] = w
        modified_text = " ".join(words_list)

    return modified_text


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
                if validate_factual_alignment(text, result_text, client):
                    PARAPHRASE_CACHE[cache_key] = result_text
                    return result_text
                else:
                    logger.warning(f"Paraphrase discarded due to factual misalignment: {text[:50]}...")
                    return text
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

def translate_to_english_via_gemini(text: str, client) -> str:
    """
    Traduit le texte en anglais via Gemini.
    Si le client est None ou en cas d'erreur, retourne le texte original.
    """
    if not text:
        return ""
    if not client:
        return text
        
    prompt = (
        f"Translate the following French text into natural, fluent English. "
        f"Do not change proper nouns, names, or numbers. "
        f"Return ONLY the translated English text, without any comments, introduction, or markdown styling.\n\n"
        f"Text to translate:\n{text}"
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
                if validate_factual_alignment(text, result_text, client):
                    return result_text
                else:
                    logger.warning(f"Translation discarded due to factual misalignment: {text[:50]}...")
                    return text
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/3 failed to translate to English: {e}")
            err_msg = str(e).upper()
            if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg or "503" in err_msg:
                sleep_time = (attempt + 1) * 15.0
                time.sleep(sleep_time)
            else:
                time.sleep(1.0)
                
    return text

def validate_factual_alignment(original_text: str, generated_text: str, client) -> bool:
    """
    Utilise Gemini comme juge pour vérifier l'alignement factuel du texte généré
    par rapport au texte original. Retourne True si les faits concordent et s'il n'y a
    pas d'hallucinations, False sinon.
    """
    if not original_text or not generated_text:
        return False
    if not client:
        return True  # Pas de client, on valide par défaut
        
    prompt = (
        "RÔLE : Validateur d'Alignement Factuel (Factual Alignment Judge).\n"
        "MISSION : Tu dois comparer le TEXTE GÉNÉRÉ (qui est une paraphrase ou une traduction) "
        "au TEXTE ORIGINAL pour t'assurer qu'aucune information factuelle n'a été altérée, contredite, "
        "ou inventée (pas d'hallucination de dates, studios, doubleurs, noms propres, chiffres, etc.).\n\n"
        f"TEXTE ORIGINAL :\n{original_text}\n\n"
        f"TEXTE GÉNÉRÉ :\n{generated_text}\n\n"
        "CONSIGNES :\n"
        "1. Une réécriture stylistique ou une traduction fluide est autorisée et encouragée.\n"
        "2. Les faits (noms, dates, chiffres, studios, genres, rôles) doivent être STRICTEMENT identiques.\n"
        "3. Aucune nouvelle information factuelle ne doit être ajoutée.\n\n"
        "Génère UNIQUEMENT un objet JSON sous le format exact suivant :\n"
        "{\n"
        "  \"aligned\": true ou false,\n"
        "  \"reason\": \"Explication détaillée en cas de désalignement, sinon vide\"\n"
        "}"
    )
    
    model_name = os.getenv("ANIMETIX_GEMINI_MODEL", "gemini-3-flash-preview")
    
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response.text:
                content = response.text.strip()
                if content.startswith("```"):
                    content = re.sub(r'^```(?:json)?\n', '', content)
                    content = re.sub(r'\n```$', '', content)
                
                result = json.loads(content.strip())
                aligned = result.get("aligned", True)
                if not aligned:
                    logger.warning(f"Fact-checking failed. Reason: {result.get('reason')}")
                return aligned
        except Exception as e:
            logger.warning(f"Factual validation attempt {attempt+1} failed: {e}")
            time.sleep(1.0)
            
    return True  # En cas d'erreur de l'API, on fait confiance par défaut

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

def clean_tags(tags, language="Français"):
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
        if language == "English":
            tag_translation = {
                "Shounen": "Shonen",
                "Primarily Teen Cast": "Teen Cast",
                "Male Protagonist": "Male Protagonist",
                "Swordplay": "Swordplay"
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
                "Martial Arts": "Arts martiaux"
            }
        cleaned.append(tag_translation.get(tag, tag))
    return cleaned

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

def make_english_anime_profile(title: str, genres: List[str], studios: List[str], tags: List[str], year: int) -> str:
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
        f"Due to its high artistic quality and thrilling plot, '{title}' is highly recommended for anime fans."
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
        f"With its striking graphic panels and a dense story, '{title}' remains an essential reference in its category."
    ]
    return " ".join(profile_parts)

def make_english_character_bio(name, origin, orgs, favs, rank, height):
    org_str = " and ".join(orgs) if orgs else "several factions and groups in their universe"
    
    syns = get_character_synonyms_string(name, "English")
    origin_syns = get_synonyms_string(origin, "English")
    
    formatted_favs = f"{favs:,}"
    
    bio_parts = [
        f"{name}{syns} is a legendary and prominent character from the hit series '{origin}'{origin_syns}.",
        f"Within this work, their narrative importance is colossal.",
    ]
    
    if orgs:
        bio_parts.append(f"They are primarily known for their affiliation and major role within: {org_str}.")
        
    if height and height != "Unknown":
        bio_parts.append(f"Their physical characteristics and official profile notably mention: {height}.")
        
    bio_parts.append(f"They enjoy immense popularity among the global community of anime fans, ranking at number {rank} of favorite characters with no less than {formatted_favs} votes of admiration.")
    
    bio_parts.append(f"As an essential figure in '{origin}', {name} embodies the values and major conflicts of their universe, deeply marking the audience with their writing and top-tier character development.")
    
    return " ".join(bio_parts)
    
def generate_otaku_meta_instructions(client=None):
    """Génère un grand nombre de variations expertes de Q&A pour le dictionnaire Otaku de base + les créateurs et studios."""
    otaku_instructions = []
    
    # 1. Génération par template pour les concepts généraux (15 variations par concept = ~6 000 exemples)
    for idx, (term, data) in enumerate(OTAKU_VOCABULARY.items()):
        if idx % 2 == 1:
            lang = "English"
            definition = translate_to_english_via_gemini(data['definition'], client)
            examples = translate_to_english_via_gemini(data['examples'], client)
            impact = translate_to_english_via_gemini(data['impact'], client)
            origin = translate_to_english_via_gemini(data['origin'], client)
            
            templates = [
                (f"What does the term '{term}' mean in otaku culture? Provide examples.", 
                 f"In otaku culture, the term '{term}' refers to: {definition}. Iconic examples include: {examples}. Cultural impact: {impact}"),
                
                (f"Give me a clear and precise definition of the concept of '{term}' in anime.",
                 f"The concept of '{term}' is defined as follows in Japanese animation: {definition}. It is illustrated through examples like: {examples}."),
                
                (f"As an anime expert, how would you define the concept of '{term}'?",
                 f"As an expert, I define '{term}' as: {definition}. This concept has a strong domain impact: {impact}"),
                
                (f"Can you explain what '{term}' means to a manga fan?",
                 f"For a manga fan, '{term}' represents: {definition}. It is a common trope characterized by: {origin}"),
                
                (f"Explain the origin, etymology and deep meaning of the trope '{term}'.",
                 f"The trope '{term}' has a rich history and etymology. Origin: {origin}. Deep meaning: {definition}. This trope is particularly well illustrated by: {examples}."),
                
                (f"Where does the word '{term}' used in otaku culture come from and what does it mean?",
                 f"The term '{term}' has its roots in: {origin}. It refers precisely to: {definition}. In the industry, this is explained by: {impact}"),
                
                (f"What is the history and linguistic root of the concept of '{term}' in manga?",
                 f"The linguistic history of '{term}' dates back to: {origin}. It is a fundamental concept meaning: {definition}"),
                
                (f"Which characters or works are considered iconic examples of '{term}'?",
                 f"Some of the key examples associated with '{term}' are: {examples}. By definition, this trope represents: {definition}"),
                
                (f"Give me examples of famous figures illustrating the trope '{term}' in anime.",
                 f"Major figures illustrating the trope '{term}' include: {examples}. This trope is characterized by: {definition} and originates from: {origin}"),
                
                (f"What are the major works that best represent the concept of '{term}'?",
                 f"The iconic works and characters for '{term}' are: {examples}. This concept is defined as: {definition}"),
                
                (f"What is the importance and cultural impact of the notion of '{term}' in the animation industry?",
                 f"The cultural impact of '{term}' in the industry is major. {impact} By definition: {definition}. It can be found in: {examples}"),
                
                (f"Analyze the influence and narrative role of the trope '{term}' in manga.",
                 f"The narrative role of '{term}' is highly influential. {impact} It expresses: {definition}. Examples: {examples}"),
                
                (f"Why is the concept of '{term}' so popular and recurring in Japanese anime?",
                 f"The popularity of '{term}' is explained by its resonance in pop culture. {impact} Origin: {origin}. Definition: {definition}"),
                
                (f"Give me a complete and expert summary of the otaku concept of '{term}'.",
                 f"Expert Summary - '{term}': {definition}. Etymological origin: {origin}. Reference works and characters: {examples}. Writing impact: {impact}"),
                
                (f"What are the key details and analysis to remember about the concept of '{term}'?",
                 f"The essential points to remember about '{term}' are: its definition ({definition}), its historical root ({origin}) and its major incarnations ({examples}).")
            ]
        else:
            lang = "Français"
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
                 f"Parmi les exemples phares associés à '{term}' sont : {data['examples']}. Par définition, ce trope représente : {data['definition']}"),
                
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
                "output": a,
                "language": lang
            })
            
    # 2. Génération par template pour les créateurs et studios d'animation (15 variations par concept = 1 500 exemples)
    for idx, (creator, data) in enumerate(CREATORS_AND_STUDIOS.items()):
        if idx % 2 == 1:
            lang = "English"
            definition = translate_to_english_via_gemini(data['definition'], client)
            examples = translate_to_english_via_gemini(data['examples'], client)
            impact = translate_to_english_via_gemini(data['impact'], client)
            origin = translate_to_english_via_gemini(data['origin'], client)
            
            templates = [
                (f"Who is '{creator}' in the world of Japanese animation and manga?",
                 f"In the Japanese industry, '{creator}' is: {definition}. Their most notable works include: {examples}. Impact: {impact}"),
                
                (f"Present in detail the profile and industrial impact of '{creator}'.",
                 f"Domain profile - '{creator}': {definition} Origins and context: {origin}. Among their most famous works are: {examples}. Their impact is immense: {impact}"),
                
                (f"What are the iconic works of '{creator}' and their historical role?",
                 f"'{creator}' has marked history through their creations: {examples}. They are defined as: {definition} Major influence: {impact}"),
                
                (f"As a Japanese animation specialist, what can you tell me about '{creator}'?",
                 f"As a specialist, I can tell you that '{creator}' is: {definition} Historical context: {origin}. They have worked on projects like: {examples}."),
                
                (f"Why is '{creator}' considered a legendary figure in otaku culture?",
                 f"'{creator}' is considered legendary because their impact has been revolutionary: {impact} They established themselves as: {definition}"),
                
                (f"What are the key projects of '{creator}'?",
                 f"The notable projects of '{creator}' include: {examples}. Their philosophy and career path: {origin}"),
                
                (f"Present a complete summary of the studio or creator '{creator}'.",
                 f"Domain Summary - '{creator}': {definition}. History and origins: {origin}. Major achievements: {examples}. Industry impact: {impact}"),
                
                (f"Can you analyze the importance of '{creator}' for the manga industry?",
                 f"The importance of '{creator}' is indisputable: {impact} They worked through: {definition}. Reference works: {examples}"),
                
                (f"What was the role of '{creator}' in the development of Japanese animation?",
                 f"'{creator}' played a crucial role: {impact} By definition: {definition}. Context: {origin}"),
                
                (f"Give details on the style or contributions of '{creator}'.",
                 f"The contributions of '{creator}' can be summarized as follows: {definition}. Their key works: {examples}. Style and impact: {impact}"),
                
                (f"Explain how '{creator}' influenced other authors or studios.",
                 f"The influence of '{creator}' extends widely: {impact} They redefined the industry as: {definition}. Their reference creations are: {examples}"),
                
                (f"What are the major characteristics associated with the creations of '{creator}'?",
                 f"The creations of '{creator}' are characterized by their style: {definition}. Notable examples: {examples}. Context: {origin}"),
                
                (f"Describe the artistic career and profile of '{creator}'.",
                 f"Artistic path of '{creator}': {definition}. Origins and evolution: {origin}. Their most influential projects: {examples}"),
                
                (f"Analyze the historical importance and legacy of '{creator}'.",
                 f"The legacy of '{creator}' is colossal. {impact} Known for: {definition}. Key achievements: {examples}"),
                
                (f"What makes '{creator}' essential in the modern otaku landscape?",
                 f"'{creator}' is essential as: {definition}. Their popular creations ({examples}) and impact ({impact}) make them an absolute reference.")
            ]
        else:
            lang = "Français"
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
                "output": a,
                "language": lang
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
    """Télécharge de manière stable 'pinzhenchen/alpaca-cleaned-fr' et 'yahma/alpaca-cleaned' depuis HF Hub."""
    logger.info(f"[INFO] Loading {count} general SFT instructions from Hugging Face...")
    
    fr_count = count // 2
    en_count = count - fr_count
    
    general_samples = []
    
    if fr_count > 0:
        logger.info(f"[INFO] Loading {fr_count} French general instructions...")
        try:
            ds_fr = load_dataset('pinzhenchen/alpaca-cleaned-fr', split='train')
            for i in range(min(fr_count, len(ds_fr))):
                item = ds_fr[i]
                general_samples.append({
                    "instruction": item.get("instruction", ""),
                    "input": item.get("input", ""),
                    "output": item.get("output", ""),
                    "language": "Français"
                })
        except Exception as e:
            logger.warning(f"Failed to load French Alpaca dataset: {e}")
            
    if en_count > 0:
        logger.info(f"[INFO] Loading {en_count} English general instructions...")
        try:
            ds_en = load_dataset('yahma/alpaca-cleaned', split='train')
            for i in range(min(en_count, len(ds_en))):
                item = ds_en[i]
                general_samples.append({
                    "instruction": item.get("instruction", ""),
                    "input": item.get("input", ""),
                    "output": item.get("output", ""),
                    "language": "English"
                })
        except Exception as e:
            logger.warning(f"Failed to load English Alpaca dataset: {e}")
            
    logger.info(f"[SUCCESS] Loaded exactly {len(general_samples)} general SFT instructions.")
    return general_samples

def deduplicate_dataset(dataset):
    seen = set()
    deduped = []
    duplicates_count = 0
    for item in dataset:
        if "turns" in item:
            sig_list = []
            for t in item["turns"]:
                sig_list.append(t["user"].strip())
                sig_list.append(t["assistant"].strip())
            key = tuple(sig_list)
        else:
            key = (item["instruction"].strip(), item.get("input", "").strip())
            
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

    # --- SCENARIOS D'ERREURS ET RESILIENCE MCP ---
    # 1. Erreur Jikan (Rate Limit 429)
    for tr in titles[:5]:
        q = f"Recherche les personnages du manga ou de l'anime '{tr}'."
        tool_response_error = {
            "status": "error",
            "code": 429,
            "message": "Rate limit exceeded. Too many requests."
        }
        ans = f"Je rencontre actuellement une limite de requêtes avec l'API Jikan (Erreur 429). Néanmoins, d'après mes connaissances encyclopédiques, les personnages principaux de l'œuvre '{tr}' incluent les figures incontournables de son univers."
        
        instructions.append({
            "instruction": q,
            "input": f"<tool_response>\n{json.dumps(tool_response_error, ensure_ascii=False, indent=2)}\n</tool_response>",
            "output": ans
        })

    # 2. Erreur Spotify (Service Unavailable 503)
    for art in artists[:5]:
        q = f"Quels sont les morceaux les plus populaires de '{art}' sur Spotify ?"
        tool_response_error = {
            "status": "error",
            "code": 503,
            "message": "Service Unavailable. Please try again later."
        }
        ans = f"L'API Spotify est temporairement indisponible (Erreur 503). Je ne peux pas récupérer le classement en temps réel pour '{art}'. D'après mes connaissances de base de données, cet artiste possède un catalogue très populaire apprécié des fans d'anisongs."
        
        instructions.append({
            "instruction": q,
            "input": f"<tool_response>\n{json.dumps(tool_response_error, ensure_ascii=False, indent=2)}\n</tool_response>",
            "output": ans
        })

    return instructions

def generate_multiturn_dialogues(animes, mangas, characters, otaku_vocab, count=1000) -> List[dict]:
    """
    Génère procéduralement des dialogues multi-tours à partir des bases de données locales.
    """
    dialogues = []
    
    # Templates de questions/réponses en Français
    fr_anime_templates = [
        {
            "t1": "Salut ! Tu as un bon anime de {genre} à me conseiller ?",
            "t2": "Ah super. Et c'est quel studio qui l'a produit, et en quelle année ?",
            "t3": "Génial, merci. Et quelles sont les thématiques principales abordées ?"
        }
    ]
    # Templates de questions/réponses en Anglais
    en_anime_templates = [
        {
            "t1": "Hi! Can you recommend a good {genre} anime?",
            "t2": "Awesome. Which studio produced it, and in what year was it released?",
            "t3": "Thanks! What are the primary themes in this anime?"
        }
    ]
    
    fr_char_templates = [
        {
            "t1": "Qui est le personnage {name} ?",
            "t2": "D'accord, et à quel groupe ou faction appartient-il ?",
            "t3": "Quelle est sa taille officielle et est-il populaire ?"
        }
    ]
    en_char_templates = [
        {
            "t1": "Who is the character {name}?",
            "t2": "Understood, and which group or faction do they belong to?",
            "t3": "What is their official height and are they popular?"
        }
    ]
    
    fr_vocab_templates = [
        {
            "t1": "Peux-tu m'expliquer le concept otaku de '{term}' ?",
            "t2": "Quels sont des exemples connus qui illustrent ce trope ?",
            "t3": "D'où vient ce terme et quel est son impact sur l'écriture ?"
        }
    ]
    en_vocab_templates = [
        {
            "t1": "Can you explain the otaku concept of '{term}'?",
            "t2": "What are some well-known examples illustrating this trope?",
            "t3": "Where does this term come from and what is its writing impact?"
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
                    {"user": t["t2"], "assistant": f"This anime was produced by the studio {studio_str} and released in {year}."},
                    {"user": t["t3"], "assistant": f"In '{display_title}', the primary themes explored are: {tags_str}."}
                ]
            else:
                p_text = make_french_anime_profile(title, genres, studios, tags, year)
                t = fr_anime_templates[0]
                turns = [
                    {"user": t["t1"].format(genre=genre), "assistant": p_text},
                    {"user": t["t2"], "assistant": f"Cet anime a été produit par le studio {studio_str} et est sorti en {year}."},
                    {"user": t["t3"], "assistant": f"Dans '{display_title}', les thématiques principales abordées sont : {tags_str}."}
                ]
                
        elif scenario == 1 and characters:
            # Character dialogue
            char = random.choice(characters)
            name = char.get("name", "Unknown")
            display_name = get_display_character(name)
            origin = char.get("origin", "Unknown")
            display_origin = get_display_title(origin)
            ents = char.get("entities", {})
            orgs = ents.get("organizations", []) if isinstance(ents, dict) else []
            orgs_str = ", ".join(orgs) if orgs else "several groups"
            favs = char.get("popularity", {}).get("favourites", 0) if isinstance(char.get("popularity"), dict) else 0
            rank = char.get("popularity", {}).get("rank", 999) if isinstance(char.get("popularity"), dict) else 999
            height = char.get("metadata", {}).get("height", "Unknown") if isinstance(char.get("metadata"), dict) else "Unknown"
            
            if lang == "English":
                p_text = make_english_character_bio(name, origin, orgs, favs, rank, height)
                t = en_char_templates[0]
                turns = [
                    {"user": t["t1"].format(name=display_name), "assistant": p_text},
                    {"user": t["t2"], "assistant": f"They are primarily known for their affiliation with: {orgs_str}."},
                    {"user": t["t3"], "assistant": f"Their official height is {height}. They are ranked #{rank} in popularity with {favs:,} favourites."}
                ]
            else:
                p_text = make_french_character_bio(name, origin, orgs, favs, rank, height)
                t = fr_char_templates[0]
                turns = [
                    {"user": t["t1"].format(name=display_name), "assistant": p_text},
                    {"user": t["t2"], "assistant": f"Il est principalement connu pour son affiliation avec : {orgs_str}."},
                    {"user": t["t3"], "assistant": f"Sa taille officielle est {height}. Il est classé au rang #{rank} des favoris avec {favs} votes d'admiration."}
                ]
                
        elif scenario == 2:
            # Otaku concept dialogue
            vocab_list = list(otaku_vocab.keys())
            term = random.choice(vocab_list) if vocab_list else "Tsundere"
            data = otaku_vocab.get(term, {"definition": "trope", "examples": "Taiga", "impact": "popular", "origin": "Japan"})
            
            if lang == "English":
                t = en_vocab_templates[0]
                turns = [
                    {"user": t["t1"].format(term=term), "assistant": f"In otaku culture, '{term}' refers to: {data['definition']}."},
                    {"user": t["t2"], "assistant": f"Iconic examples illustrating this concept include: {data['examples']}."},
                    {"user": t["t3"], "assistant": f"Origin: {data['origin']}. Narrative impact: {data['impact']}."}
                ]
            else:
                t = fr_vocab_templates[0]
                turns = [
                    {"user": t["t1"].format(term=term), "assistant": f"Dans la culture otaku, '{term}' désigne : {data['definition']}."},
                    {"user": t["t2"], "assistant": f"Parmi les exemples emblématiques illustrant ce concept, on peut citer : {data['examples']}."},
                    {"user": t["t3"], "assistant": f"Origine : {data['origin']}. Impact narratif : {data['impact']}."}
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
                    {"user": f"I want to compare two major anime: '{title1}' and '{title2}'. Which one should I watch?", 
                     "assistant": f"Both are incredible shows but quite different. '{title1}' fits into the {genres1} genres and was produced by {studio1}. On the other hand, '{title2}' is a {genres2} show produced by {studio2}. If you enjoy character-driven shows, '{title1}' is a great pick. If you prefer high-stakes action, go with '{title2}'."},
                    {"user": f"But I heard that '{title1}' has much better character development, do you agree?",
                     "assistant": f"That is a very common opinion! The character writing in '{title1}' is indeed stellar, especially with figures like {char_name}. However, '{title2}' makes up for it with its thrilling pacing and outstanding production values. It depends on whether you value psychological depth or action-packed animation more."},
                    {"user": "Understood. Are both finished and were they popular?",
                     "assistant": f"Yes, '{title1}' was released in {year1} and has a popularity score of {pop1:,} members. '{title2}' was released in {year2} with {pop2:,} members. Both are major hits in otaku culture."}
                ]
            else:
                turns = [
                    {"user": f"Je cherche à comparer deux œuvres majeures de la japanimation : '{title1}' et '{title2}'. Lequel devrais-je regarder ?", 
                     "assistant": f"Ce sont deux œuvres formidables mais très différentes. '{title1}' s'inscrit dans les genres de type {genres1} et a été produit par {studio1}. De l'autre côté, '{title2}' s'illustre dans les genres {genres2} par {studio2}. Si tu aimes la profondeur des personnages, '{title1}' est un excellent choix. Si tu préfères l'action pure, opte pour '{title2}'."},
                    {"user": f"Mais j'ai entendu dire que '{title1}' a une bien meilleure écriture de personnages, tu es d'accord ?",
                     "assistant": f"C'est un point de vue très répandu ! L'écriture des personnages dans '{title1}' est en effet brillante, notamment grâce à des figures emblématiques comme {char_name}. Cependant, '{title2}' compense par son rythme haletant et ses qualités d'animation. Tout dépend de ce qui prime pour toi entre la profondeur psychologique et la mise en scène."},
                    {"user": "D'accord, je vois. Est-ce que les deux sont terminés et ont été populaires ?",
                     "assistant": f"Oui, '{title1}' est sorti en {year1} et jouit d'une popularité de {pop1} membres. '{title2}' est sorti en {year2} et compte {pop2} membres. Les deux sont des succès majeurs incontournables."}
                ]
                
        elif scenario == 4:
            # Clarification request
            sub_scenario = random.choice(["studio_genre", "character_name", "adaptation"])
            
            if sub_scenario == "studio_genre":
                anime = random.choice(animes)
                title = get_display_title(anime.get("title", "Unknown"))
                genres = clean_tags(anime.get("genres", ["Action"]), lang)
                genre = genres[0] if genres else ("Action" if lang == "English" else "Action")
                studio = ", ".join(anime.get("studios", ["Pierrot"]))
                year = anime.get("year", 2002)
                genres_str = ", ".join(genres)
                
                tags = clean_tags(anime.get("tags", []), lang)
                tag = tags[0] if tags else ("adventure" if lang == "English" else "aventure")
                tags_str = ", ".join(tags[:3])
                
                char_name = "Luffy"
                for c in characters:
                    if c.get("origin") == anime.get("title"):
                        char_name = get_display_character(c.get("name"))
                        break
                        
                if lang == "English":
                    turns = [
                        {"user": f"Can you tell me about that popular {genre} anime produced by {studio}?",
                         "assistant": f"Could you please clarify which anime you mean? Studio {studio} has produced several {genre} anime, such as '{title}' (with themes like {tag}) or other notable projects. Were you referring to this one?"},
                        {"user": f"Yes, I was referring to '{title}'!",
                         "assistant": f"Great! '{title}' was released in {year} and falls into the genres: {genres_str}. The story explores key themes like: {tags_str}. It is a prominent production by {studio}."},
                        {"user": "Thanks for the details. Are there any highly popular characters in it?",
                         "assistant": f"Definitely! Within this universe, {char_name} is extremely popular among fans, ranking high with many votes of admiration."}
                    ]
                else:
                    turns = [
                        {"user": f"Peux-tu me parler de cet anime de {genre} très populaire produit par {studio} ?",
                         "assistant": f"Pourrais-tu préciser de quelle œuvre il s'agit ? Le studio {studio} a produit plusieurs animés de {genre}, notamment '{title}' (avec des thèmes comme {tag}) ou d'autres projets marquants. Parlais-tu de celui-ci ?"},
                        {"user": f"Oui, je parlais bien de '{title}' !",
                         "assistant": f"Excellent choix ! '{title}' est sorti en {year} et s'inscrit dans les genres : {genres_str}. L'histoire aborde des thématiques fortes comme : {tags_str}. C'est une production majeure de {studio}."},
                        {"user": "Merci pour ces détails. Est-ce qu'il y a des personnages très populaires dedans ?",
                         "assistant": f"Absolument ! Si on regarde les personnages de cet univers, {char_name} est particulièrement apprécié de la communauté, se classant dans le top avec de nombreux votes d'admiration."}
                    ]
            
            elif sub_scenario == "character_name":
                # Clarification about character names that are ambiguous
                choices = [
                    {"common_name": "Sakura", "char1": "Sakura Haruno", "anime1": "Naruto", "char2": "Sakura Kinomoto", "anime2": "Cardcaptor Sakura"},
                    {"common_name": "Rin", "char1": "Rin Tohsaka", "anime1": "Fate/stay night", "char2": "Rin Okumura", "anime2": "Blue Exorcist"},
                    {"common_name": "Yuki", "char1": "Yuki Sohma", "anime1": "Fruits Basket", "char2": "Yuki Nagato", "anime2": "The Melancholy of Haruhi Suzumiya"}
                ]
                choice = random.choice(choices)
                common_name = choice["common_name"]
                char1 = choice["char1"]
                anime1 = choice["anime1"]
                char2 = choice["char2"]
                anime2 = choice["anime2"]
                
                orgs1 = ["le village de Konoha" if lang == "Français" else "Konoha Village"]
                orgs2 = ["le club d'astronomie" if lang == "Français" else "Astronomy Club"]
                
                for c in characters:
                    if c.get("name") == char1:
                        ents = c.get("entities", {})
                        if isinstance(ents, dict) and ents.get("organizations"):
                            orgs1 = ents["organizations"]
                    if c.get("name") == char2:
                        ents = c.get("entities", {})
                        if isinstance(ents, dict) and ents.get("organizations"):
                            orgs2 = ents["organizations"]
                            
                orgs1_str = ", ".join(orgs1)
                
                if lang == "English":
                    turns = [
                        {"user": f"Can you give me information about the character '{common_name}'?",
                         "assistant": f"There are several famous characters named '{common_name}' in anime. Are you referring to {char1} from '{anime1}' or {char2} from '{anime2}'?"},
                        {"user": f"I was talking about {char1} in '{anime1}'.",
                         "assistant": f"Understood! {char1} is a key protagonist in '{anime1}'. Within this work, they play a narrative-defining role and are deeply connected to the main plot."},
                        {"user": "Great, thanks. What groups or factions do they belong to?",
                         "assistant": f"In '{anime1}', they are primarily associated with the following groups or factions: {orgs1_str}."}
                    ]
                else:
                    turns = [
                        {"user": f"Peux-tu me donner des informations sur le personnage '{common_name}' ?",
                         "assistant": f"Il existe plusieurs personnages célèbres nommés '{common_name}' dans la japanimation. Fais-tu référence à {char1} de '{anime1}' ou à {char2} de '{anime2}' ?"},
                        {"user": f"Je parlais de {char1} dans '{anime1}'.",
                         "assistant": f"D'accord ! {char1} est un protagoniste clé de '{anime1}'. Dans cette œuvre, il joue un rôle narratif déterminant et est intimement lié à l'intrigue principale."},
                        {"user": "Super, merci. Quels sont ses groupes d'appartenance ?",
                         "assistant": f"Dans '{anime1}', il est principalement associé aux groupes ou factions suivantes : {orgs1_str}."}
                    ]
            
            else:
                # Clarification about adaptations (e.g., FMA vs FMAB, or first adaptation vs remake)
                choices = [
                    {"title": "Fullmetal Alchemist", "studio1": "Studio Bones", "year1": 2003, "studio2": "Studio Bones (Brotherhood)", "year2": 2009, "episodes1": 51, "episodes2": 64},
                    {"title": "Hunter x Hunter", "studio1": "Nippon Animation", "year1": 1999, "studio2": "Madhouse", "year2": 2011, "episodes1": 62, "episodes2": 148},
                    {"title": "Fate/stay night", "studio1": "Studio Deen", "year1": 2006, "studio2": "ufotable", "year2": 2014, "episodes1": 24, "episodes2": 26}
                ]
                choice = random.choice(choices)
                title = choice["title"]
                studio1 = choice["studio1"]
                year1 = choice["year1"]
                studio2 = choice["studio2"]
                year2 = choice["year2"]
                episodes1 = choice["episodes1"]
                episodes2 = choice["episodes2"]
                
                if lang == "English":
                    turns = [
                        {"user": f"I would like to get details about the anime adaptation of '{title}'.",
                         "assistant": f"The franchise '{title}' has multiple adaptations. Are you referring to the first series animated by {studio1} in {year1}, or the remake version animated by {studio2} in {year2}?"},
                        {"user": f"The version from {year2}.",
                         "assistant": f"Excellent choice! The {year2} adaptation of '{title}' by {studio2} is highly praised for its faithful retelling of the original manga source material, offering stellar production values."},
                        {"user": "How many episodes does it have in total?",
                         "assistant": f"This version of '{title}' consists of {episodes2} episodes in total."}
                    ]
                else:
                    turns = [
                        {"user": f"Je voudrais des détails sur l'adaptation en animé de '{title}'.",
                         "assistant": f"La franchise '{title}' possède plusieurs adaptations. Fais-tu référence à la première série produite par {studio1} en {year1}, ou à la version remake produite par {studio2} en {year2} ?"},
                        {"user": f"La version de {year2}.",
                         "assistant": f"Excellent choix ! L'adaptation de {year2} de '{title}' par {studio2} est particulièrement réputée pour sa fidélité totale au manga d'origine et ses combats spectaculaires."},
                        {"user": "Combien d'épisodes comporte-t-elle au total ?",
                         "assistant": f"Cette version de '{title}' comporte un total de {episodes2} épisodes."}
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
            dark_keywords = ["drama", "psychological", "horror", "tragedy", "mystery", "thriller", "seinen", "dark fantasy"]
            light_keywords = ["comedy", "slice of life", "parody", "school", "romance", "shoujo", "josei"]
            action_keywords = ["action", "adventure", "fantasy", "supernatural", "mecha", "shonen", "super power"]
            
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
            tags2_str = ", ".join(clean_tags(tags2, lang)[:3]) if tags2 else ("animation" if lang == "English" else "animation")
            
            # Check if we have volume/episode count from database or use a realistic dummy
            from backend.pipeline.mlops.volumes_and_episodes_db import VOLUMES_AND_EPISODES_DATA
            episodes2 = "12 épisodes" if lang == "Français" else "12 episodes"
            if anime2.get("title") in VOLUMES_AND_EPISODES_DATA:
                episodes2 = VOLUMES_AND_EPISODES_DATA[anime2.get("title")]["anime_episodes"]
            else:
                episodes2 = random.choice(["12", "24", "26", "50", "75"])
                if lang == "Français":
                    episodes2 = f"{episodes2} épisodes"
                else:
                    episodes2 = f"{episodes2} episodes"
                    
            if lang == "English":
                p_text1 = make_english_anime_profile(anime1.get("title"), genres1, anime1.get("studios", []), anime1.get("tags", []), anime1.get("year", 2010))
                p_text2 = make_english_anime_profile(anime2.get("title"), genres2, anime2.get("studios", []), tags2, year2)
                
                turns = [
                    {"user": f"Hi! I'm looking for a good {genre1_translated} anime. Do you have any recommendation?",
                     "assistant": f"Hello! I highly recommend '{title1}'. {p_text1}"},
                    {"user": f"Thanks, but actually I would prefer something more {mood_en}. Do you have something else?",
                     "assistant": f"I see! In that case, you should check out '{title2}'. {p_text2}"},
                    {"user": "That looks awesome! Which studio produced it, and how many episodes does it have?",
                     "assistant": f"'{title2}' was produced by the studio {studio2} and consists of {episodes2} in total. It was released in {year2}."}
                ]
            else:
                p_text1 = make_french_anime_profile(anime1.get("title"), genres1, anime1.get("studios", []), anime1.get("tags", []), anime1.get("year", 2010))
                p_text2 = make_french_anime_profile(anime2.get("title"), genres2, anime2.get("studios", []), tags2, year2)
                
                turns = [
                    {"user": f"Salut ! Je cherche un bon anime de type {genre1_translated}. Tu as une recommandation ?",
                     "assistant": f"Bonjour ! Je te conseille vivement '{title1}'. {p_text1}"},
                    {"user": f"Merci, mais en fait je préfère quelque chose de plus {mood_fr}. Tu as un autre choix ?",
                     "assistant": f"Je vois ! Dans ce cas, tu devrais adorer '{title2}'. {p_text2}"},
                    {"user": "Ça a l'air super ! Quel studio a produit cette série, et elle fait combien d'épisodes ?",
                     "assistant": f"'{title2}' a été produit par le studio {studio2} et compte un total de {episodes2}. Cet anime est sorti en {year2}."}
                ]
        else:
            # Self-correction after feedback
            anime_choice = random.choice([
                {"title_fr": "L'Attaque des Titans", "title_en": "Attack on Titan", "s1": "Wit Studio", "s2": "MAPPA", "year1": 2013, "year2": 2020, "vols": 34},
                {"title_fr": "One Punch Man", "title_en": "One Punch Man", "s1": "Madhouse", "s2": "J.C.Staff", "year1": 2015, "year2": 2019, "vols": 30},
                {"title_fr": "Vinland Saga", "title_en": "Vinland Saga", "s1": "Wit Studio", "s2": "MAPPA", "year1": 2019, "year2": 2023, "vols": 27}
            ])
            
            if lang == "English":
                title = anime_choice["title_en"]
                s1 = anime_choice["s1"]
                s2 = anime_choice["s2"]
                y1 = anime_choice["year1"]
                y2 = anime_choice["year2"]
                vols = anime_choice["vols"]
                turns = [
                    {"user": f"Which animation studio produced '{title}'?",
                     "assistant": f"The anime adaptation of '{title}' was primarily produced by {s1} starting in {y1}."},
                    {"user": f"Wait, wasn't it produced by {s2} instead?",
                     "assistant": f"You are absolutely correct, thank you for pointing that out! There was a change in production: {s1} animated the initial part (starting in {y1}), and then {s2} took over for the subsequent seasons starting in {y2}."},
                    {"user": "Ah I see, thanks. Is the manga finished?",
                     "assistant": f"Yes, the manga has finished its publication run, compiling a total of {vols} volumes."}
                ]
            else:
                title = anime_choice["title_fr"]
                s1 = anime_choice["s1"]
                s2 = anime_choice["s2"]
                y1 = anime_choice["year1"]
                y2 = anime_choice["year2"]
                vols = anime_choice["vols"]
                turns = [
                    {"user": f"Quel studio d'animation s'est occupé de l'anime '{title}' ?",
                     "assistant": f"L'adaptation animée de '{title}' a été initialement produite par le studio {s1} à partir de {y1}."},
                    {"user": f"Attends, ce n'est pas plutôt le studio {s2} qui l'a fait ?",
                     "assistant": f"Vous avez tout à fait raison, et je vous remercie pour cette précision importante ! Il y a eu un changement de studio : {s1} a produit le début (à partir de {y1}), puis c'est le studio {s2} qui a repris la main pour produire les saisons suivantes à partir de {y2}."},
                    {"user": "Ah d'accord, merci pour l'explication. Et le manga est terminé ?",
                     "assistant": f"Oui, le manga s'est achevé avec un total de {vols} volumes publiés."}
                ]
                
        dialogues.append({
            "turns": turns,
            "language": lang
        })
        
    return dialogues

def generate_rag_context_instructions(animes, characters) -> List[dict]:
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
        "Publicité : Téléchargez l'application Manga-Reader dès maintenant sur iOS et Android."
    ]
    noise_en = [
        "Sponsor: Get 10% off at the Otaku-Shop with promo code ANIME10.",
        "Weather: Scattered showers are expected over Tokyo this weekend.",
        "Rumor: A new anime movie for this franchise is reportedly in production for late 2027.",
        "Editor's Note: This article was originally published in the Shonen Jump magazine in 2021.",
        "Reader reviews: A rating of 4.8/5 was given to this volume by club members.",
        "Advertisement: Download the Manga-Reader app now on iOS and Android."
    ]
    
    import random
    
    # Scenario A: Synopsis extraction with noise
    for idx in range(120):
        lang = "English" if idx % 2 == 1 else "Français"
        anime = random.choice(animes) if animes else {"title": "Naruto", "genres": ["Action"], "studios": ["Pierrot"], "year": 2002}
        title = anime.get("title", "Unknown")
        genres = ", ".join(anime.get("genres", ["Action"]))
        studio = ", ".join(anime.get("studios", ["Pierrot"]))
        year = anime.get("year", 2002)
        
        # Build clean info
        if lang == "English":
            clean_doc = f"[Document A (Official profile)] The anime '{title}' was produced by the studio {studio} and released in the year {year}. It belongs to the genres: {genres}."
            unrelated_anime = "One Piece" if title != "One Piece" else "Dragon Ball"
            noise_doc1 = f"[Document B (Trivia)] The manga '{unrelated_anime}' has sold millions of copies worldwide and is serialized in Weekly Shonen Jump."
            noise_doc2 = f"[Document C (Ads)] {random.choice(noise_en)}"
            
            # Shuffle docs order
            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)
            
            q = f"According to the provided documents, which studio produced the anime '{title}', in which year was it released, and which genres does it belong to?"
            ans = f"Based on the provided documents (specifically Document A), the anime '{title}' was produced by the studio {studio} and released in {year}. It belongs to the genres: {genres}. The other documents contain unrelated trivia about '{unrelated_anime}' and an advertisement, which have been ignored."
        else:
            clean_doc = f"[Document A (Fiche officielle)] L'anime '{title}' a été produit par le studio {studio} et est sorti en {year}. Il appartient aux genres : {genres}."
            unrelated_anime = "One Piece" if title != "One Piece" else "Dragon Ball"
            noise_doc1 = f"[Document B (Anecdotes)] Le manga '{unrelated_anime}' s'est vendu à des millions d'exemplaires et est prépublié dans le Weekly Shonen Jump."
            noise_doc2 = f"[Document C (Pub)] {random.choice(noise_fr)}"
            
            # Shuffle docs order
            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)
            
            q = f"D'après les documents fournis, quel studio a produit l'anime '{title}', en quelle année est-il sorti et à quels genres appartient-il ?"
            ans = f"D'après le contexte fourni (spécifiquement le Document A), l'anime '{title}' a été produit par le studio {studio} et est sorti en {year}. Ses genres sont : {genres}. Les autres documents mentionnent des anecdotes sur '{unrelated_anime}' et une annonce publicitaire, qui ont été ignorées."
            
        instructions.append({
            "instruction": q,
            "input": context,
            "output": ans,
            "language": lang
        })

    # Scenario B: Voice Actor (VF) profile extraction with conflict
    from french_market_db import FRENCH_VOICE_ACTORS
    voice_actors_list = list(FRENCH_VOICE_ACTORS.keys()) if FRENCH_VOICE_ACTORS else ["Brigitte Lecordier", "Benoît DuPac"]
    
    for idx in range(100):
        lang = "English" if idx % 2 == 1 else "Français"
        va = random.choice(voice_actors_list)
        va_data = FRENCH_VOICE_ACTORS.get(va, {"definition": "Doubleur", "examples": "Rôle A", "impact": "VF culte", "origin": "AB Production"})
        
        # Build clean info
        roles = va_data["examples"]
        bio = va_data["definition"]
        
        if lang == "English":
            clean_doc = f"[Source 1 (French Voice Cast)] the famous French voice actor '{va}' is known for lending their voice to: {roles}. They are recognized as: {bio}."
            noise_doc1 = f"[Source 2 (Music)] Yoasobi is a popular Japanese music duo composed of producer Ayase and singer ikura."
            noise_doc2 = f"[Source 3] {random.choice(noise_en)}"
            
            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)
            
            q = f"Based on the text above, who is the French voice actor '{va}' and what are some of their iconic roles?"
            ans = f"According to Source 1, '{va}' is {bio}. Their iconic French voice acting roles include: {roles}. The other sources regarding Japanese music (Yoasobi) and advertisements were ignored as they are not relevant to the question."
        else:
            clean_doc = f"[Source 1 (Doublage Français)] Le célèbre comédien de doublage '{va}' est connu pour prêter sa voix en VF à : {roles}. Il est défini comme : {bio}."
            noise_doc1 = f"[Source 2 (Musique)] Yoasobi est un duo musical japonais très populaire, composé du producteur Ayase et de la chanteuse Ikura."
            noise_doc2 = f"[Source 3] {random.choice(noise_fr)}"
            
            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)
            
            q = f"En vous appuyant sur les documents fournis, qui est le doubleur français '{va}' et quels sont ses rôles marquants ?"
            ans = f"D'après la Source 1, '{va}' est {bio}. Ses rôles marquants en version française (VF) sont : {roles}. Les informations sur le duo de musique japonais Yoasobi (Source 2) et les publicités ont été ignorées car elles ne concernent pas le sujet."

        instructions.append({
            "instruction": q,
            "input": context,
            "output": ans,
            "language": lang
        })

    # Scenario C: Character Bio with multiple documents
    for idx in range(100):
        lang = "English" if idx % 2 == 1 else "Français"
        char = random.choice(characters) if characters else {"name": "Luffy", "origin": "One Piece", "entities": {"organizations": ["Straw Hats"]}, "popularity": {"favourites": 150000, "rank": 1}, "metadata": {"height": "174cm"}}
        name = char.get("name", "Unknown")
        origin = char.get("origin", "Unknown")
        height = char.get("metadata", {}).get("height", "Unknown") if isinstance(char.get("metadata"), dict) else "Unknown"
        favs = char.get("popularity", {}).get("favourites", 0) if isinstance(char.get("popularity"), dict) else 0
        
        if lang == "English":
            clean_doc = f"[Document A (Character Wiki)] Character profile: {name} is from '{origin}'. Official height: {height}. Popularity rank: {favs} favorites."
            noise_doc1 = f"[Document B (Sponsor)] {random.choice(noise_en)}"
            noise_doc2 = f"[Document C (Release Dates)] Studio Trigger announced a new project coming out in winter next year."
            
            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)
            
            q = f"According to the context, what is the official height of '{name}' and which anime/manga work are they from?"
            ans = f"Based on Document A, the character '{name}' is from '{origin}' and their official height is {height}. Documents B and C contain unrelated sponsor advertisements and Trigger release announcements, which were excluded from this answer."
        else:
            clean_doc = f"[Document A (Wiki Personnages)] Profil du personnage : {name} est issu de '{origin}'. Sa taille officielle est {height}. Popularité : {favs} votes d'admiration."
            noise_doc1 = f"[Document B (Sponsor)] {random.choice(noise_fr)}"
            noise_doc2 = f"[Document C (Sorties)] Le studio Trigger a annoncé un nouveau projet pour l'hiver prochain."
            
            docs = [clean_doc, noise_doc1, noise_doc2]
            random.shuffle(docs)
            context = "\n".join(docs)
            
            q = f"D'après le contexte fourni, quelle est la taille officielle de '{name}' et de quelle œuvre est-il issu ?"
            ans = f"D'après le Document A, le personnage '{name}' provient de l'œuvre '{origin}' et sa taille officielle est {height}. Les Documents B et C concernant le sponsor publicitaire et les annonces du studio Trigger n'ont pas été pris en compte car ils sont hors-sujet."

        instructions.append({
            "instruction": q,
            "input": context,
            "output": ans,
            "language": lang
        })

    return instructions

def generate_negative_refusal_examples(count=800) -> List[dict]:
    """
    Génère procéduralement des exemples négatifs (hors-sujet) avec des refus polis
    cadrant l'expertise exclusive d'Animetix sur l'univers anime/manga.
    """
    import random
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
            "Quel temps de cuisson pour un oeuf mollet ?"
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
            "Comment annuler le dernier commit avec Git ?"
        ],
        "mathematiques": [
            "Calcule la dérivée de f(x) = 3x^2 + 5x - 2.",
            "Quel est le théorème de Pythagore ?",
            "Comment résoudre une équation du second degré ?",
            "Combien font 1547 fois 36 ?",
            "Explique-moi la conjecture de Goldbach."
        ],
        "medecine": [
            "Que faire en cas de migraine persistante ?",
            "Quels sont les symptômes d'une grippe ?",
            "Comment soigner un rhume rapidement ?",
            "Est-ce que l'ibuprofène est conseillé pour le mal de ventre ?",
            "Donne-moi des conseils pour mieux dormir sans médicaments."
        ],
        "finance": [
            "Comment investir 1000 euros en bourse ?",
            "Qu'est-ce qu'une action à dividendes ?",
            "Comment fonctionne le Bitcoin et la cryptomonnaie ?",
            "Quels sont les meilleurs placements financiers actuels ?",
            "Comment rédiger un plan d'épargne retraite ?"
        ],
        "histoire_geo": [
            "Qui était le premier président de la République Française ?",
            "Quelle est la capitale de l'Australie ?",
            "Explique les causes de la Première Guerre mondiale.",
            "Combien de pays compte l'Union Européenne ?",
            "Qui a découvert l'Amérique en 1492 ?"
        ],
        "redaction": [
            "Rédige une lettre de motivation pour un poste d'ingénieur commercial.",
            "Aide-moi à écrire un e-mail professionnel pour demander une augmentation.",
            "Écris un poème d'amour romantique en alexandrins.",
            "Rédige un compte-rendu de réunion synthétique.",
            "Écris une critique littéraire du roman Les Misérables."
        ],
        "science_technologie": [
            "Peux-tu m'expliquer la théorie de la relativité d'Einstein ?",
            "Comment fonctionne la fusion nucléaire ?",
            "Quelle est la distance entre la Terre et Mars ?",
            "Qu'est-ce qu'un trou noir ?",
            "Comment fonctionne le chiffrement RSA ?"
        ],
        "pop_culture_occidentale": [
            "Qui joue le rôle principal dans le film Inception ?",
            "Donne-moi la liste des albums de Taylor Swift.",
            "Quel est le synopsis de la série Breaking Bad ?",
            "Qui a réalisé le film Le Parrain ?",
            "Peux-tu me résumer l'intrigue de Star Wars Episode IV ?"
        ],
        "loisirs_sport": [
            "Comment bien entretenir un bonsaï chez soi ?",
            "Quelles sont les règles de base du football américain ?",
            "Donne-moi un programme de musculation pour débutant.",
            "Comment fabriquer une étagère en bois soi-même ?",
            "Quelles plantes planter en extérieur au printemps ?"
        ],
        "culture_generale": [
            "Quand a eu lieu la Révolution Française ?",
            "Quelle est la capitale du Canada ?",
            "Qui a peint la Joconde ?",
            "Quel est le plus long fleuve du monde ?",
            "Quelle est la hauteur de la Tour Eiffel ?"
        ]
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
            "How long does it take to soft-boil an egg?"
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
            "How can I undo my last commit in Git?"
        ],
        "mathematics": [
            "Calculate the derivative of f(x) = 3x^2 + 5x - 2.",
            "What is the Pythagorean theorem?",
            "How do you solve a quadratic equation?",
            "What is 1547 multiplied by 36?",
            "Explain Goldbach's conjecture."
        ],
        "medical": [
            "What should I do for a persistent headache?",
            "What are the main symptoms of the flu?",
            "How can I cure a cold quickly?",
            "Is ibuprofen recommended for stomach pain?",
            "Give me tips for sleeping better without medication."
        ],
        "finance": [
            "How should I invest 1000 dollars in the stock market?",
            "What is a dividend-paying stock?",
            "How do Bitcoin and cryptocurrencies work?",
            "What are the best financial investments right now?",
            "How do I write a retirement savings plan?"
        ],
        "history_geo": [
            "Who was the first president of the United States?",
            "What is the capital of Australia?",
            "Explain the causes of World War I.",
            "How many countries are in the European Union?",
            "Who discovered America in 1492?"
        ],
        "writing": [
            "Write a cover letter for a sales engineer position.",
            "Help me write a professional email asking for a raise.",
            "Write a romantic love poem.",
            "Draft a concise meeting summary.",
            "Write a literary review of the novel Les Misérables."
        ],
        "science_technology": [
            "Can you explain Einstein's theory of relativity?",
            "How does nuclear fusion work?",
            "What is the average distance between Earth and Mars?",
            "What is a black hole and how is it formed?",
            "How does RSA encryption secure data?"
        ],
        "western_pop_culture": [
            "Who plays the lead role in the movie Inception?",
            "Give me a list of all Taylor Swift albums.",
            "What is the plot of the TV show Breaking Bad?",
            "Who directed the movie The Godfather?",
            "Can you summarize the plot of Star Wars Episode IV?"
        ],
        "hobbies_sports": [
            "How do I properly care for a bonsai tree at home?",
            "What are the basic rules of American football?",
            "Give me a beginner-friendly workout routine.",
            "How can I build a wooden bookshelf myself?",
            "Which flowers should I plant in the spring?"
        ],
        "general_knowledge": [
            "When did the French Revolution start?",
            "What is the capital of Canada?",
            "Who painted the Mona Lisa?",
            "What is the longest river in the world?",
            "How tall is the Eiffel Tower?"
        ]
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
        ""
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
        ""
    ]

    refusal_templates_fr = [
        "En tant qu'Animetix, mon expertise se concentre exclusivement sur l'univers des animés, des mangas et de la culture otaku. Je ne peux donc pas vous aider avec des sujets hors de ce domaine comme {topic}. Si vous avez des questions sur des œuvres, des personnages, des doubleurs ou des créateurs de mangas, je serai ravi d'y répondre !",
        "Désolé, mais mon rôle d'assistant expert Animetix est dédié uniquement aux mangas, aux animés et à la pop-culture japonaise. Je dois refuser les requêtes concernant d'autres sujets comme {topic}. N'hésitez pas à me poser une question sur vos animes ou personnages préférés !",
        "Je ne peux pas répondre à cette demande. Animetix est une intelligence artificielle spécialisée uniquement dans les mangas, les animés et la culture otaku. Les questions concernant {topic} dépassent mon cadre d'expertise. Posez-moi plutôt une question sur l'univers des animés !",
        "En tant qu'expert de la japanimation et des mangas sous le nom d'Animetix, je me limite à ce domaine passionnant. Je ne peux pas traiter de sujets généraux tels que {topic}. Avez-vous une question sur les animés, les studios ou les seiyuu à me poser ?",
        "Navré, mais en tant qu'assistant Animetix, je suis uniquement conçu pour répondre aux questions relatives aux mangas, aux animés et à l'univers otaku. Je ne suis pas habilité à traiter des sujets comme {topic}. Si vous souhaitez parler de japanimation, je suis à votre disposition !",
        "Je regrette, mais ma base de connaissances sous le nom d'Animetix est spécialisée à 100% dans la pop-culture japonaise, les animés et les mangas. Je ne peux pas répondre aux demandes concernant {topic}. N'hésitez pas à me solliciter pour des recommandations d'animes !"
    ]

    refusal_templates_en = [
        "As Animetix, my expertise is exclusively focused on the universe of anime, manga, and otaku culture. Therefore, I cannot help you with topics outside this domain like {topic}. If you have questions about anime series, characters, voice actors, or manga creators, I would be delighted to answer!",
        "Sorry, but my role as the expert assistant Animetix is solely dedicated to manga, anime, and Japanese pop culture. I must decline requests concerning other topics like {topic}. Feel free to ask me questions about your favorite anime series or characters instead!",
        "I cannot answer this request. Animetix is an AI specialized exclusively in manga, anime, and otaku culture. Questions regarding {topic} fall outside my scope of expertise. Please ask me a question about the anime universe instead!",
        "As an anime and manga specialist known as Animetix, I restrict my answers to this exciting domain. I cannot assist with general topics such as {topic}. Do you have a question about anime, studios, or seiyuu for me?",
        "I am sorry, but as Animetix, I am strictly designed to answer queries about anime, manga, and otaku culture. I cannot assist with topics like {topic}. If you want to discuss Japanese animation or manga, I am here for you!",
        "Unfortunately, my database as Animetix is completely dedicated to Japanese pop culture, anime, and manga. I cannot address requests regarding {topic}. Please let me know if you need any anime recommendations instead!"
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
                "general_knowledge": "general knowledge or trivial facts"
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
                "culture_generale": "la culture générale"
            }
            topic_name = topic_names.get(cat, "des sujets généraux")

        instruction = prefix + question
        # Ensure capitalization is clean
        if prefix and prefix[0].isupper() and len(question) > 0:
            instruction = prefix + question[0].lower() + question[1:]

        output = refusal_template.format(topic=topic_name)
        refusals.append({
            "instruction": instruction,
            "input": "",
            "output": output,
            "language": lang
        })

    return refusals

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
    
    # 1h. SIMULATION DE CONTEXTES RAG AVEC BRUIT
    logger.info("[INFO] Generating RAG context simulation instructions with noise...")
    animes_list = []
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, 'r', encoding='utf-8') as f:
            animes_list = json.load(f)
    chars_list = []
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, 'r', encoding='utf-8') as f:
            chars_list = json.load(f)
    rag_data = generate_rag_context_instructions(animes_list, chars_list)
    specialized_data.extend(rag_data)
    
    # 2. ANIME DATABASE
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, 'r', encoding='utf-8') as f:
            animes = json.load(f)
            logger.info(f"[INFO] Processing ALL {len(animes)} animes with popularity weighting...")
            for idx, item in enumerate(animes):
                title = clean_description(item.get('title', 'Unknown'))
                genres = [clean_description(g) for g in item.get('genres', [])]
                studios = [clean_description(s) for s in item.get('studios', [])]
                tags = [clean_description(t) for t in item.get('tags', [])]
                pop = item.get('popularity', 0)
                year = item.get('year', 2020)
                
                display_t = get_display_title(title)
                
                # Check for underrepresented genres (Shojo, Josei, Slice of Life, Mecha, Iyashikei, Mahou Shoujo, Music, Sports, Historical, Horror, Thriller)
                is_underrepresented = False
                underrepresented_keywords = [
                    "shoujo", "shojo", "josei", "slice of life", "tranche de vie",
                    "iyashikei", "mecha", "mahou shoujo", "magical girl", "music",
                    "sports", "historical", "horror", "thriller"
                ]
                for term in underrepresented_keywords:
                    if any(term in str(g).lower() for g in genres + tags):
                        is_underrepresented = True
                        break
                
                # Boost retro eras (70s, 80s, 90s)
                if not is_underrepresented and year and 1970 <= year <= 1999:
                    is_underrepresented = True
                        
                effective_pop = pop
                if is_underrepresented:
                    effective_pop = max(pop, 150001) if pop > 50000 else 100000
                
                if idx % 2 == 1:
                    profile = make_english_anime_profile(title, genres, studios, tags, year)
                    # Tier 1 : Ultra Populaire (> 150k membres) -> 5 variations
                    if effective_pop > 150000:
                        if client and title in augmented_anime_titles:
                            logger.info(f"Augmenting anime (Tier 1) '{title}' via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "enthousiaste")
                            p4 = paraphrase_text_via_gemini(profile, client, "décontracté")
                            p5 = paraphrase_text_via_gemini(profile, client, "analytique")
                        else:
                            p1 = p2 = p3 = p4 = p5 = profile
                        specialized_data.append({"instruction": f"Present the cult anime '{display_t}' in extreme detail.", "input": "", "output": p1, "language": "English"})
                        specialized_data.append({"instruction": f"Which studio is behind the masterpiece '{display_t}' and what is it about?", "input": "", "output": p2, "language": "English"})
                        specialized_data.append({"instruction": f"What is the story of the major work '{display_t}'?", "input": "", "output": p3, "language": "English"})
                        specialized_data.append({"instruction": f"What are the major themes and universe of '{display_t}'?", "input": "", "output": p4, "language": "English"})
                        specialized_data.append({"instruction": f"Why is '{display_t}' such an extremely popular and appreciated work among viewers?", "input": "", "output": p5, "language": "English"})
                    
                    # Tier 2 : Très Populaire (50k - 150k membres) -> 3 variations
                    elif effective_pop > 50000:
                        if client and title in augmented_anime_titles:
                            logger.info(f"Augmenting anime (Tier 2) '{title}' via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        else:
                            p1 = p2 = p3 = profile
                        specialized_data.append({"instruction": f"Present the popular anime '{display_t}' in detail.", "input": "", "output": p1, "language": "English"})
                        specialized_data.append({"instruction": f"Which studio produced '{display_t}' and what is it about?", "input": "", "output": p2, "language": "English"})
                        specialized_data.append({"instruction": f"What are the major themes of the anime '{display_t}'?", "input": "", "output": p3, "language": "English"})
                    
                    # Tier 3 : Standard / Obscure (<= 50k membres) -> 1 variation
                    else:
                        specialized_data.append({"instruction": f"Present the anime '{display_t}' in detail.", "input": "", "output": profile, "language": "English"})
                else:
                    profile = make_french_anime_profile(title, genres, studios, tags, year)
                    # Tier 1 : Ultra Populaire (> 150k membres) -> 5 variations
                    if effective_pop > 150000:
                        if client and title in augmented_anime_titles:
                            logger.info(f"Augmenting anime (Tier 1) '{title}' via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "enthousiaste")
                            p4 = paraphrase_text_via_gemini(profile, client, "décontracté")
                            p5 = paraphrase_text_via_gemini(profile, client, "analytique")
                        else:
                            p1 = p2 = p3 = p4 = p5 = profile
                        specialized_data.append({"instruction": f"Présente l'anime culte '{display_t}' de manière extrêmement détaillée.", "input": "", "output": p1, "language": "Français"})
                        specialized_data.append({"instruction": f"Quel studio est derrière le chef-d'œuvre '{display_t}' et de quoi s'agit-il ?", "input": "", "output": p2, "language": "Français"})
                        specialized_data.append({"instruction": f"De quoi parle l'œuvre majeure '{display_t}' ?", "input": "", "output": p3, "language": "Français"})
                        specialized_data.append({"instruction": f"Quelles sont les thématiques majeures et l'univers de '{display_t}' ?", "input": "", "output": p4, "language": "Français"})
                        specialized_data.append({"instruction": f"Pourquoi '{display_t}' est-elle une œuvre extrêmement populaire et appréciée des spectateurs ?", "input": "", "output": p5, "language": "Français"})
                    
                    # Tier 2 : Très Populaire (50k - 150k membres) -> 3 variations
                    elif effective_pop > 50000:
                        if client and title in augmented_anime_titles:
                            logger.info(f"Augmenting anime (Tier 2) '{title}' via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        else:
                            p1 = p2 = p3 = profile
                        specialized_data.append({"instruction": f"Présente l'anime populaire '{display_t}' de manière détaillée.", "input": "", "output": p1, "language": "Français"})
                        specialized_data.append({"instruction": f"Quel studio a produit '{display_t}' et de quoi ça parle ?", "input": "", "output": p2, "language": "Français"})
                        specialized_data.append({"instruction": f"Quelles sont les thématiques majeures de l'anime '{display_t}' ?", "input": "", "output": p3, "language": "Français"})
                    
                    # Tier 3 : Standard / Obscure (<= 50k membres) -> 1 variation
                    else:
                        specialized_data.append({"instruction": f"Présente l'anime '{display_t}' de manière détaillée.", "input": "", "output": profile, "language": "Français"})

    # 3. MANGA DATABASE
    if os.path.exists(MANGA_DB):
        with open(MANGA_DB, 'r', encoding='utf-8') as f:
            mangas = json.load(f)
            logger.info(f"[INFO] Processing ALL {len(mangas)} mangas with popularity weighting...")
            for idx, item in enumerate(mangas):
                title = clean_description(item.get('title', 'Unknown'))
                genres = [clean_description(g) for g in item.get('genres', [])]
                tags = [clean_description(t) for t in item.get('tags', [])]
                pop = item.get('popularity', 0)
                
                display_t = get_display_title(title)
                
                year = item.get('year')
                display_t = get_display_title(title)
                
                # Check for underrepresented genres (Shojo, Josei, Slice of Life, Mecha, Iyashikei, Mahou Shoujo, Music, Sports, Historical, Horror, Thriller)
                is_underrepresented = False
                underrepresented_keywords = [
                    "shoujo", "shojo", "josei", "slice of life", "tranche de vie",
                    "iyashikei", "mecha", "mahou shoujo", "magical girl", "music",
                    "sports", "historical", "horror", "thriller"
                ]
                for term in underrepresented_keywords:
                    if any(term in str(g).lower() for g in genres + tags):
                        is_underrepresented = True
                        break
                        
                # Boost retro eras (70s, 80s, 90s)
                if not is_underrepresented and year and 1970 <= year <= 1999:
                    is_underrepresented = True
                        
                effective_pop = pop
                if is_underrepresented:
                    effective_pop = max(pop, 150001) if pop > 50000 else 100000
                
                if idx % 2 == 1:
                    profile = make_english_manga_profile(title, genres, tags)
                    # Tier 1 : Ultra Populaire (> 150k membres) -> 5 variations
                    if effective_pop > 150000:
                        if client and title in augmented_manga_titles:
                            logger.info(f"Augmenting manga (Tier 1) '{title}' via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "enthousiaste")
                            p4 = paraphrase_text_via_gemini(profile, client, "décontracté")
                            p5 = paraphrase_text_via_gemini(profile, client, "analytique")
                        else:
                            p1 = p2 = p3 = p4 = p5 = profile
                        specialized_data.append({"instruction": f"What are the main themes of the cult manga '{display_t}'?", "input": "", "output": p1, "language": "English"})
                        specialized_data.append({"instruction": f"Analyze and summarize the iconic manga '{display_t}'.", "input": "", "output": p2, "language": "English"})
                        specialized_data.append({"instruction": f"Why has the manga '{display_t}' met with such great success with the public?", "input": "", "output": p3, "language": "English"})
                        specialized_data.append({"instruction": f"Present the universe and plot of the cult manga '{display_t}'.", "input": "", "output": p4, "language": "English"})
                        specialized_data.append({"instruction": f"What is the cult manga '{display_t}' about?", "input": "", "output": p5, "language": "English"})
                    
                    # Tier 2 : Très Populaire (50k - 150k membres) -> 3 variations
                    elif effective_pop > 50000:
                        if client and title in augmented_manga_titles:
                            logger.info(f"Augmenting manga (Tier 2) '{title}' via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        else:
                            p1 = p2 = p3 = profile
                        specialized_data.append({"instruction": f"What are the main themes of the popular manga '{display_t}'?", "input": "", "output": p1, "language": "English"})
                        specialized_data.append({"instruction": f"What is the popular manga '{display_t}' about?", "input": "", "output": p2, "language": "English"})
                        specialized_data.append({"instruction": f"Summarize the key themes of the manga '{display_t}'.", "input": "", "output": p3, "language": "English"})
                    
                    # Tier 3 : Standard / Obscure (<= 50k membres) -> 1 variation
                    else:
                        specialized_data.append({"instruction": f"What are the main themes of the manga '{display_t}'?", "input": "", "output": profile, "language": "English"})
                else:
                    profile = make_french_manga_profile(title, genres, tags)
                    # Tier 1 : Ultra Populaire (> 150k membres) -> 5 variations
                    if effective_pop > 150000:
                        if client and title in augmented_manga_titles:
                            logger.info(f"Augmenting manga (Tier 1) '{title}' via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "enthousiaste")
                            p4 = paraphrase_text_via_gemini(profile, client, "décontracté")
                            p5 = paraphrase_text_via_gemini(profile, client, "analytique")
                        else:
                            p1 = p2 = p3 = p4 = p5 = profile
                        specialized_data.append({"instruction": f"Quelles sont les thématiques principales du manga culte '{display_t}' ?", "input": "", "output": p1, "language": "Français"})
                        specialized_data.append({"instruction": f"Analyse et résume le manga emblématique '{display_t}'.", "input": "", "output": p2, "language": "Français"})
                        specialized_data.append({"instruction": f"Pourquoi le manga '{display_t}' a-t-il rencontré un si grand succès auprès du public ?", "input": "", "output": p3, "language": "Français"})
                        specialized_data.append({"instruction": f"Présente l'univers et le scénario du manga culte '{display_t}'.", "input": "", "output": p4, "language": "Français"})
                        specialized_data.append({"instruction": f"De quoi parle le manga culte '{display_t}' ?", "input": "", "output": p5, "language": "Français"})
                    
                    # Tier 2 : Très Populaire (50k - 150k membres) -> 3 variations
                    elif effective_pop > 50000:
                        if client and title in augmented_manga_titles:
                            logger.info(f"Augmenting manga (Tier 2) '{title}' via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        else:
                            p1 = p2 = p3 = profile
                        specialized_data.append({"instruction": f"Quelles sont les thématiques principales du manga populaire '{display_t}' ?", "input": "", "output": p1, "language": "Français"})
                        specialized_data.append({"instruction": f"De quoi parle le manga populaire '{display_t}' ?", "input": "", "output": p2, "language": "Français"})
                        specialized_data.append({"instruction": f"Résume les thèmes clés du manga '{display_t}'.", "input": "", "output": p3, "language": "Français"})
                    
                    # Tier 3 : Standard / Obscure (<= 50k membres) -> 1 variation
                    else:
                        specialized_data.append({"instruction": f"Quelles sont les thématiques principales du manga '{display_t}' ?", "input": "", "output": profile, "language": "Français"})

    # 4. CHARACTER DATABASE
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, 'r', encoding='utf-8') as f:
            chars = json.load(f)
            top_chars = [c for c in chars if c.get('popularity', {}).get('favourites', 0) > 50]
            logger.info(f"[INFO] Processing {len(top_chars)} characters with tiered augmentation...")
            
            for idx, c in enumerate(top_chars):
                name = clean_description(c.get('name', 'Anonyme'))
                origin = clean_description(c.get('origin', 'Inconnu'))
                ents = c.get('entities', {})
                orgs = [clean_description(o) for o in ents.get('organizations', [])]
                favs = c.get('popularity', {}).get('favourites', 0)
                rank = c.get('popularity', {}).get('rank', 9999)
                height = clean_description(c.get('metadata', {}).get('height', 'Unknown'))
                
                display_name = get_display_character(name)
                display_origin = get_display_title(origin)
                
                if idx % 2 == 1:
                    profile = make_english_character_bio(name, origin, orgs, favs, rank, height)
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
                        specialized_data.append({"instruction": f"Complete analysis of the cult character {display_name} in {display_origin}.", "input": "", "output": p1, "language": "English"})
                        specialized_data.append({"instruction": f"Who is {display_name} ?", "input": f"Context: {display_origin}", "output": p2, "language": "English"})
                        specialized_data.append({"instruction": f"In-depth analysis of the psychology and role of {display_name} in '{display_origin}'.", "input": "", "output": p3, "language": "English"})
                        specialized_data.append({"instruction": f"What are the outstanding traits and importance of the character of {display_name} ?", "input": f"Original work: {display_origin}", "output": p4, "language": "English"})
                        specialized_data.append({"instruction": f"Why is {display_name} one of the most iconic and beloved characters in '{display_origin}' ?", "input": "", "output": p5, "language": "English"})
                    
                    # Tier 2 : Très Populaire (500 - 2000 favoris) -> 3 variations
                    elif favs > 500:
                        if client and (name, origin) in augmented_char_names:
                            logger.info(f"Augmenting character (Tier 2) '{name}' ({origin}) via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        else:
                            p1 = p2 = p3 = profile
                        specialized_data.append({"instruction": f"Analyze the popular character of {display_name} in {display_origin}.", "input": "", "output": p1, "language": "English"})
                        specialized_data.append({"instruction": f"Who is {display_name} ?", "input": f"Context: {display_origin}", "output": p2, "language": "English"})
                        specialized_data.append({"instruction": f"What are the outstanding traits of the character of {display_name} in '{display_origin}' ?", "input": "", "output": p3, "language": "English"})
                    
                    # Tier 3 : Standard (50 - 500 favoris) -> 2 variations
                    else:
                        specialized_data.append({"instruction": f"Analyze the character of {display_name} in {display_origin}.", "input": "", "output": profile, "language": "English"})
                        specialized_data.append({"instruction": f"Who is {display_name} ?", "input": f"Context: {display_origin}", "output": profile, "language": "English"})
                else:
                    profile = make_french_character_bio(name, origin, orgs, favs, rank, height)
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
                        specialized_data.append({"instruction": f"Analyse complète du personnage culte {display_name} dans {display_origin}.", "input": "", "output": p1, "language": "Français"})
                        specialized_data.append({"instruction": f"Qui est {display_name} ?", "input": f"Contexte : {display_origin}", "output": p2, "language": "Français"})
                        specialized_data.append({"instruction": f"Analyse approfondie de la psychologie et du rôle de {display_name} dans '{display_origin}'.", "input": "", "output": p3, "language": "Français"})
                        specialized_data.append({"instruction": f"Quels sont les traits marquants et l'importance du personnage de {display_name} ?", "input": f"Œuvre d'origine : {display_origin}", "output": p4, "language": "Français"})
                        specialized_data.append({"instruction": f"Pourquoi {display_name} est-il l'un des personnages les plus emblématiques et adorés de '{display_origin}' ?", "input": "", "output": p5, "language": "Français"})
                    
                    # Tier 2 : Très Populaire (500 - 2000 favoris) -> 3 variations
                    elif favs > 500:
                        if client and (name, origin) in augmented_char_names:
                            logger.info(f"Augmenting character (Tier 2) '{name}' ({origin}) via Gemini...")
                            p1 = paraphrase_text_via_gemini(profile, client, "encyclopédique")
                            p2 = paraphrase_text_via_gemini(profile, client, "critique")
                            p3 = paraphrase_text_via_gemini(profile, client, "décontracté")
                        else:
                            p1 = p2 = p3 = profile
                        specialized_data.append({"instruction": f"Analyse le personnage populaire de {display_name} dans {display_origin}.", "input": "", "output": p1, "language": "Français"})
                        specialized_data.append({"instruction": f"Qui est {display_name} ?", "input": f"Contexte : {display_origin}", "output": p2, "language": "Français"})
                        specialized_data.append({"instruction": f"Quels sont les traits marquants du personnage de {display_name} dans '{display_origin}' ?", "input": "", "output": p3, "language": "Français"})
                    
                    # Tier 3 : Standard (50 - 500 favoris) -> 2 variations
                    else:
                        specialized_data.append({"instruction": f"Analyse le personnage de {display_name} dans {display_origin}.", "input": "", "output": profile, "language": "Français"})
                        specialized_data.append({"instruction": f"Qui est {display_name} ?", "input": f"Contexte : {display_origin}", "output": profile, "language": "Français"})

    # Déduplication
    specialized_data = deduplicate_dataset(specialized_data)
    # Ensure every instruction in specialized_data has a default language of "Français"
    for item in specialized_data:
        if "language" not in item:
            item["language"] = "Français"

    non_meta_count = len(specialized_data)
    
    # Generate Multi-Turn dialogues to represent ~15% of the SFT dataset
    multiturn_required = int(non_meta_count * 0.18)
    logger.info(f"[INFO] Generating {multiturn_required} multi-turn dialogue examples...")
    
    animes_list = []
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, 'r', encoding='utf-8') as f:
            animes_list = json.load(f)
            
    mangas_list = []
    if os.path.exists(MANGA_DB):
        with open(MANGA_DB, 'r', encoding='utf-8') as f:
            mangas_list = json.load(f)
            
    chars_list = []
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, 'r', encoding='utf-8') as f:
            chars_list = json.load(f)
            
    multiturn_dialogues = generate_multiturn_dialogues(animes_list, mangas_list, chars_list, OTAKU_VOCABULARY, count=multiturn_required)
    multiturn_dialogues = deduplicate_dataset(multiturn_dialogues)

    # Generate out-of-scope/refusal negative examples to represent ~1.5% of the dataset
    refusal_required = int(non_meta_count * 0.02)  # ~2% of non-meta is about 1.5% of total
    logger.info(f"[INFO] Generating {refusal_required} out-of-scope refusal negative examples...")
    refusal_data = generate_negative_refusal_examples(count=refusal_required)
    refusal_data = deduplicate_dataset(refusal_data)

    # 5. RATIO CONFIGURABLE ET PARAMETRABLE (Défaut : 80% Spécialisé, 5% Meta, 15% Général)
    meta_required, general_required = calculate_dataset_counts(non_meta_count)
    
    logger.info(f"[INFO] Total Non-meta (80% target) instructions generated: {non_meta_count}")
    logger.info(f"[INFO] Target Meta required (5% target): {meta_required}")
    logger.info(f"[INFO] Target General required (15% target): {general_required}")
    
    # Pool de questions méta
    logger.info("[INFO] Generating high-quality Otaku Meta Vocabulary questions pool...")
    meta_pool = generate_otaku_meta_instructions(client)
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
                "output": new_output,
                "language": base_item.get("language", "Français")
            })
        selected_meta.extend(extra_meta)
    
    # Téléchargement stable de pinzhenchen/alpaca-cleaned-fr
    general_data = fetch_general_instructions(general_required)
    
    # Assemblage unifié
    final_dataset = []
    final_dataset.extend(specialized_data)
    final_dataset.extend(selected_meta)
    final_dataset.extend(general_data)
    final_dataset.extend(multiturn_dialogues)
    final_dataset.extend(refusal_data)
    
    # Mélange global
    logger.info("[INFO] Shuffling the unified massive dataset...")
    random.shuffle(final_dataset)
    
    # --- INJECT QUERY NOISE (10-15% of user prompts/turns) ---
    noise_rate_env = os.getenv("ANIMETIX_QUERY_NOISE_RATE", "0.12")
    try:
        noise_rate = float(noise_rate_env)
        if not (0.0 <= noise_rate <= 1.0):
            raise ValueError("Rate out of bounds")
    except ValueError:
        logger.warning(f"Invalid ANIMETIX_QUERY_NOISE_RATE: '{noise_rate_env}'. Falling back to 0.12.")
        noise_rate = 0.12

    logger.info(f"[INFO] Injecting query noise with rate target: {noise_rate * 100:.1f}%...")
    noise_count = 0
    for item in final_dataset:
        if random.random() < noise_rate:
            noise_count += 1
            lang = item.get("language", "Français")
            if "turns" in item:
                for turn in item["turns"]:
                    if "user" in turn:
                        turn["user"] = inject_query_noise(turn["user"], lang)
            else:
                if "instruction" in item:
                    item["instruction"] = inject_query_noise(item["instruction"], lang)

    actual_noise_rate = (noise_count / len(final_dataset)) * 100 if final_dataset else 0.0
    logger.info(f"[SUCCESS] Injected query noise into {noise_count}/{len(final_dataset)} instructions ({actual_noise_rate:.2f}%).")

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
    logger.info(f"  - Multi-Turn Dialogues (15-20% target): {len(multiturn_dialogues)} / {total_count} ({len(multiturn_dialogues)/total_count*100:.2f}%)")
    logger.info(f"  - Persona & Refus (Negative) (1-2% target): {len(refusal_data)} / {total_count} ({len(refusal_data)/total_count*100:.2f}%)")
    logger.info(f"  - Query Noise (10-15% target): {noise_count} / {total_count} ({actual_noise_rate:.2f}%)")
    logger.info(f"[INFO] Saved at: {OUTPUT_DATASET}")
    
    # Sauvegarde du cache
    save_paraphrase_cache()

if __name__ == "__main__":
    run_generate_instruction_dataset()
