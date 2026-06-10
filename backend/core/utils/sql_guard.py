import re
import logging
from typing import List

logger = logging.getLogger("animetix.sql_guard")

def get_all_db_tables() -> List[str]:
    """
    Récupère dynamiquement la liste de toutes les tables de la base de données Django.
    Fournit un fallback statique complet si Django n'est pas initialisé.
    """
    try:
        from django.apps import apps
        if not apps.ready:
            import django
            django.setup()
        return [model._meta.db_table.lower() for model in apps.get_models()]
    except Exception as e:
        logger.warning(f"Impossible de récupérer dynamiquement les modèles Django: {e}")
        # Fallback statique complet basé sur le schéma d'Animetix
        return [
            "auth_user", "auth_group", "django_session", "django_migrations", "django_content_type",
            "animetix_profile", "animetix_friendship", "animetix_globalboss", "animetix_bossparticipation",
            "animetix_duelroom", "animetix_dailychallenge", "animetix_challengeresult", "animetix_achievement",
            "animetix_userachievement", "animetix_aifeedback", "animetix_gameplaysession", "animetix_airevalresult",
            "animetix_golddatasetentry", "animetix_aisafetyevent", "animetix_semanticcache", "animetix_datacurationticket",
            "animetix_aitokenusage", "animetix_latentspacepoint", "animetix_creativefusion", "animetix_vsbattle",
            "animetix_notification", "animetix_discoveryclub", "animetix_clubmembership", "animetix_archetypedriftsnapshot",
            "animetix_clubevent", "animetix_vectorrecord", "animetix_userrecommendation", "animetix_supportticket"
        ]

def validate_sql_query(sql: str) -> bool:
    """
    Vérifie la sécurité d'une requête SQL générée par IA.
    Retourne True si et seulement si la requête est un SELECT inoffensif cibrant uniquement animetix_mediaitem.
    """
    if not sql or not isinstance(sql, str):
        return False
        
    sql_clean = sql.strip()
    
    # 1. Commencer impérativement par SELECT
    if not sql_clean.upper().startswith("SELECT"):
        logger.warning(f"SQL Guardrail: La requête ne commence pas par SELECT: {sql_clean[:200]}")
        return False
        
    # 2. Interdire les commentaires SQL (potentiels masquages de logique malveillante)
    if "--" in sql_clean or "/*" in sql_clean:
        logger.warning("SQL Guardrail: Commentaires SQL interdits détectés")
        return False
        
    # 3. Interdire les requêtes multiples via point-virgule (sauf point-virgule final)
    sql_no_semicolon = sql_clean
    if sql_clean.endswith(";"):
        sql_no_semicolon = sql_clean[:-1].strip()
        
    if ";" in sql_no_semicolon:
        logger.warning("SQL Guardrail: Plusieurs requêtes chaînées via point-virgule détectées")
        return False
        
    # 4. Liste noire de mots-clés d'écriture ou d'administration
    forbidden_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE", 
        "REPLACE", "GRANT", "REVOKE", "MERGE", "EXEC", "EXECUTE", "UNION",
        "COPY", "VACUUM", "ANALYZE"
    ]
    for keyword in forbidden_keywords:
        pattern = re.compile(rf"\b{keyword}\b", re.IGNORECASE)
        if pattern.search(sql_clean):
            logger.warning(f"SQL Guardrail: Mot-clé interdit '{keyword}' détecté")
            return False
            
    # 5. Doit impérativement cibler la table autorisée
    allowed_table = "animetix_mediaitem"
    if not re.search(rf"\b{allowed_table}\b", sql_clean, re.IGNORECASE):
        logger.warning(f"SQL Guardrail: La requête ne cible pas la table autorisée '{allowed_table}'")
        return False
        
    # 6. Interdire de cibler d'autres tables de l'application
    all_tables = get_all_db_tables()
    forbidden_tables = [t for t in all_tables if t != allowed_table]
    
    for f_table in forbidden_tables:
        pattern = re.compile(rf"\b{f_table}\b", re.IGNORECASE)
        if pattern.search(sql_clean):
            logger.warning(f"SQL Guardrail: Requête cibrant une table interdite '{f_table}'")
            return False
            
    return True
