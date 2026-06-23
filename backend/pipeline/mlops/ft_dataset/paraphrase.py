# -*- coding: utf-8 -*-
"""Cache de paraphrases et appels Gemini (paraphrase, traduction, validation factuelle).

Le cache `PARAPHRASE_CACHE` est chargé depuis disque au chargement du module et
réutilisé pour éviter les appels redondants à Gemini.
"""

import json
import logging
import os
import re
import time

from core.utils.gemini_models import GEMINI_FLASH

from .paths import CACHE_FILE

logger = logging.getLogger("animetix.pipeline.ft_dataset.paraphrase")

PARAPHRASE_CACHE: dict[str, str] = {}


def load_paraphrase_cache():
    global PARAPHRASE_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                PARAPHRASE_CACHE = json.load(f)
            logger.info(
                f"Loaded {len(PARAPHRASE_CACHE)} entries from paraphrase cache."
            )
        except Exception as e:
            logger.warning(f"Failed to load paraphrase cache: {e}")
            PARAPHRASE_CACHE = {}
    else:
        PARAPHRASE_CACHE = {}


def save_paraphrase_cache():
    if PARAPHRASE_CACHE:
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
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

    model_name = GEMINI_FLASH

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
                    logger.warning(
                        f"Paraphrase discarded due to factual misalignment: {text[:50]}..."
                    )
                    return text
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/3 failed to paraphrase: {e}")
            err_msg = str(e).upper()
            if (
                "RESOURCE_EXHAUSTED" in err_msg
                or "429" in err_msg
                or "UNAVAILABLE" in err_msg
                or "503" in err_msg
            ):
                sleep_time = (attempt + 1) * 15.0  # 15s, 30s
                logger.info(
                    f"Rate limit or service unavailable detected. Sleeping for {sleep_time}s before retry..."
                )
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

    model_name = GEMINI_FLASH

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
                    logger.warning(
                        f"Translation discarded due to factual misalignment: {text[:50]}..."
                    )
                    return text
        except Exception as e:
            logger.warning(
                f"Attempt {attempt + 1}/3 failed to translate to English: {e}"
            )
            err_msg = str(e).upper()
            if (
                "RESOURCE_EXHAUSTED" in err_msg
                or "429" in err_msg
                or "UNAVAILABLE" in err_msg
                or "503" in err_msg
            ):
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
        '  "aligned": true ou false,\n'
        '  "reason": "Explication détaillée en cas de désalignement, sinon vide"\n'
        "}"
    )

    model_name = GEMINI_FLASH

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response.text:
                content = response.text.strip()
                if content.startswith("```"):
                    content = re.sub(r"^```(?:json)?\n", "", content)
                    content = re.sub(r"\n```$", "", content)

                result = json.loads(content.strip())
                aligned = result.get("aligned", True)
                if not aligned:
                    logger.warning(
                        f"Fact-checking failed. Reason: {result.get('reason')}"
                    )
                return aligned
        except Exception as e:
            logger.warning(f"Factual validation attempt {attempt + 1} failed: {e}")
            time.sleep(1.0)

    return True  # En cas d'erreur de l'API, on fait confiance par défaut
