import socket
import ipaddress
import logging
import httpx
import filetype
from urllib.parse import urlparse, urljoin
from typing import List, Optional

logger = logging.getLogger('animetix.security')

import hmac
import hashlib
from django.conf import settings

def sign_proxy_url(url: str) -> str:
    """Génère une signature HMAC pour une URL de proxy."""
    secret = settings.SECRET_KEY.encode()
    signature = hmac.new(secret, url.encode(), hashlib.sha256).hexdigest()
    return signature

def verify_proxy_signature(url: str, signature: str) -> bool:
    """Vérifie si la signature fournie correspond à l'URL."""
    if not signature:
        return False
    expected = sign_proxy_url(url)
    return hmac.compare_digest(expected, signature)

def validate_file_mime_type(file_bytes: bytes, allowed_mime_types: List[str]) -> bool:
    """
    Vérifie la véritable signature binaire (Magic Number) d'un fichier 
    pour s'assurer qu'il correspond bien aux types MIME autorisés.
    Empêche les attaques par fausse extension (ex: script shell nommé .jpg).
    """
    if not file_bytes:
        return False
        
    kind = filetype.guess(file_bytes)
    
    if kind is None:
        logger.warning("Fichier non reconnu ou sans signature magique valide.")
        # Pour certains fichiers textes ou JSON, filetype peut retourner None,
        # mais on est strict pour les médias (images/audio/vidéos).
        return False
        
    mime = kind.mime
    if mime not in allowed_mime_types:
        logger.warning(f"Type de fichier binaire non autorisé détecté : {mime}. Autorisé : {allowed_mime_types}")
        return False
        
    return True

def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Vérifie si la taille d'un fichier dépasse la limite autorisée.
    Prévient les attaques par déni de service (DoS) par saturation mémoire/disque.
    """
    if file_size > max_size:
        logger.warning(f"Tentative d'upload d'un fichier trop volumineux : {file_size} octets (Max: {max_size}).")
        return False
    return True

# --- SSRF PROTECTION ---
# Liste blanche des services internes autorisés via Docker ou localhost.
ALLOWED_INTERNAL_HOSTS = ['brain', 'db', 'redis', 'chromadb', 'neo4j', 'localhost', '127.0.0.1']

def is_safe_url(url: str, allowed_schemes: Optional[List[str]] = None, allow_internal: bool = False) -> bool:
    """
    Vérifie si une URL est sûre pour éviter les attaques SSRF.
    Si allow_internal est True, autorise UNIQUEMENT les hôtes dans ALLOWED_INTERNAL_HOSTS.
    Bloque systématiquement les adresses privées/réservées si l'hôte n'est pas dans la liste blanche.
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
        
    try:
        parsed = urlparse(url)
        if parsed.scheme not in allowed_schemes:
            logger.warning(f"Blocked unsafe protocol: {parsed.scheme} in URL: {url}")
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # 1. Vérification de la liste blanche interne
        is_whitelisted = hostname in ALLOWED_INTERNAL_HOSTS
        
        if is_whitelisted:
            if allow_internal:
                return True
            else:
                logger.warning(f"Blocked internal host access (allow_internal=False): {hostname}")
                return False

        # 2. Vérification par résolution DNS (Pour les URLs externes ou tentatives de contournement)
        try:
            ip_addresses = socket.getaddrinfo(hostname, None)
            for addr in ip_addresses:
                ip_str = addr[4][0]
                ip = ipaddress.ip_address(ip_str)
                
                # Bloquer les plages privées même si allow_internal=True
                # On veut forcer l'usage des noms symboliques (ex: 'db') et non des IPs directes.
                if (
                    ip.is_private or 
                    ip.is_loopback or 
                    ip.is_link_local or 
                    ip.is_multicast or 
                    ip.is_unspecified
                ):
                    logger.warning(f"Blocked request to internal/private IP: {ip_str} (hostname: {hostname})")
                    return False
        except (socket.gaierror, ValueError) as e:
            # Si on ne peut pas résoudre, on bloque systématiquement 
            # (les hôtes internes autorisés ont été gérés au point 1)
            return False

        return True
    except Exception as e:
        logger.error(f"Error in is_safe_url: {e}")
        return False

def safe_http_request(method: str, url: str, max_redirects: int = 3, allow_internal: bool = False, **kwargs) -> httpx.Response:
    """
    Effectue une requête HTTP en validant manuellement chaque redirection.
    Utilise is_safe_url à chaque étape pour prévenir les attaques SSRF.
    """
    current_url = url
    for _ in range(max_redirects + 1):
        if not is_safe_url(current_url, allow_internal=allow_internal):
            logger.warning(f"Blocked request to unsafe URL: {current_url}")
            raise ValueError(f"Unsafe URL detected: {current_url}")

        # On désactive le suivi automatique des redirections de httpx
        res = httpx.request(method, current_url, follow_redirects=False, **kwargs)

        if res.is_redirect:
            location = res.headers.get("Location")
            if not location:
                return res
            # Gérer les URLs relatives
            current_url = urljoin(str(res.url), location)
            method = "GET" # Les redirections 301/302 transforment souvent le POST en GET
            continue
        
        return res

    raise ValueError("Too many redirects")

async def safe_http_request_async(method: str, url: str, max_redirects: int = 3, allow_internal: bool = False, **kwargs) -> httpx.Response:
    """
    Version asynchrone de safe_http_request.
    """
    current_url = url
    async with httpx.AsyncClient(follow_redirects=False) as client:
        for _ in range(max_redirects + 1):
            if not is_safe_url(current_url, allow_internal=allow_internal):
                logger.warning(f"Blocked request to unsafe URL: {current_url}")
                raise ValueError(f"Unsafe URL detected: {current_url}")

            res = await client.request(method, current_url, **kwargs)

            if res.is_redirect:
                location = res.headers.get("Location")
                if not location:
                    return res
                current_url = urljoin(str(res.url), location)
                method = "GET"
                continue
            
            return res

    raise ValueError("Too many redirects")

import re
import bleach

def sanitize_html_content(value: str) -> str:
    """
    Sanitise le contenu HTML (généré par l'IA ou saisi par l'utilisateur) 
    pour prévenir les attaques XSS tout en autorisant un formatage de base.
    Utilise bleach avec une liste blanche stricte.
    """
    if not value:
        return ""

    # Liste blanche des tags et attributs autorisés (Formatage riche minimal)
    allowed_tags = [
        'p', 'b', 'i', 'u', 'em', 'strong', 'br', 'ul', 'ol', 'li', 
        'code', 'pre', 'blockquote', 'h3', 'h4', 'span'
    ]
    allowed_attrs = {
        'code': ['class'],
        'pre': ['class'],
        'span': ['class', 'style'],
    }

    # Nettoyage via bleach
    cleaned = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True,
        strip_comments=True
    )
    
    return cleaned

def sanitize_for_prompt(text: str, max_length: int = 2000) -> str:
    """
    Sanitise les entrées utilisateur pour limiter les risques d'injection de prompt (Prompt Injection).
    Approche hybride : filtrage de patterns + échappement de délimiteurs.
    """
    if not text:
        return ""
        
    # 1. Troncature pour éviter les DoS par dépassement de contexte
    text = text[:max_length]
    
    # 2. Filtrage des patterns d'injection connus (insensible à la casse)
    injection_patterns = [
        r"(?i)ignore\s+previous",
        r"(?i)system\s+prompt",
        r"(?i)tu\s+es\s+maintenant",
        r"(?i)you\s+are\s+now",
        r"(?i)réponds\s+uniquement",
        r"(?i)output\s+only",
        r"(?i)forget\s+all",
        r"(?i)override",
    ]
    
    for pattern in injection_patterns:
        text = re.sub(pattern, "[FILTERED]", text)
        
    # 3. Échappement des délimiteurs potentiels (triples quotes, balises XML internes)
    text = text.replace('"""', "'''")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    
    return text.strip()

def validate_service_url(url: str, expected_prefix: str) -> bool:
    """
    Vérifie si une URL de service interne (ex: BRAIN_API_URL) commence par un préfixe attendu.
    Utile pour empêcher le détournement de configuration.
    """
    if not url:
        return False
    return url.startswith(expected_prefix)
