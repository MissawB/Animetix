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

def is_safe_url(url: str, allowed_schemes: Optional[List[str]] = None, allow_internal: bool = False) -> bool:
    """
    Vérifie si une URL est sûre pour éviter les attaques SSRF.
    Bloque les adresses privées par défaut, sauf si allow_internal est True.
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

        # Cas particulier pour Docker/Localhost si explicitement autorisé
        if allow_internal:
            if hostname in ['localhost', '127.0.0.1', 'brain', 'db', 'redis', 'chromadb', 'neo4j']:
                return True

        # 1. Vérification par résolution DNS
        try:
            ip_addresses = socket.getaddrinfo(hostname, None)
            for addr in ip_addresses:
                ip_str = addr[4][0]
                ip = ipaddress.ip_address(ip_str)
                
                if not allow_internal and (
                    ip.is_private or 
                    ip.is_loopback or 
                    ip.is_link_local or 
                    ip.is_multicast or 
                    ip.is_unspecified
                ):
                    logger.warning(f"Blocked request to internal/private IP: {ip_str} (hostname: {hostname})")
                    return False
        except (socket.gaierror, ValueError) as e:
            # Si on ne peut pas résoudre, on bloque si ce n'est pas un hostname interne connu
            if allow_internal:
                return hostname in ['brain', 'db', 'redis', 'chromadb', 'neo4j']
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

def validate_service_url(url: str, expected_prefix: str) -> bool:
    """
    Vérifie si une URL de service interne (ex: BRAIN_API_URL) commence par un préfixe attendu.
    Utile pour empêcher le détournement de configuration.
    """
    if not url:
        return False
    return url.startswith(expected_prefix)
