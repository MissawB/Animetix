import socket
import ipaddress
import logging
from urllib.parse import urlparse
from typing import List, Optional

logger = logging.getLogger('animetix.security')

def is_safe_url(url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
    """
    Vérifie si une URL est sûre pour éviter les attaques SSRF.
    Bloque les adresses privées, loopback, link-local et les protocoles non-autorisés.
    
    Args:
        url: L'URL à vérifier.
        allowed_schemes: Liste des protocoles autorisés (défaut: http, https).
        
    Returns:
        bool: True si l'URL est jugée sûre.
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

        # 1. Vérification par résolution DNS (Protection contre bypass par IP ou hostname interne)
        try:
            # Note: En production, il est recommandé d'utiliser un resolver qui ne suit pas les CNAME 
            # pointant vers des IPs internes, ou de valider l'IP finale juste avant la requête.
            ip_addresses = socket.getaddrinfo(hostname, None)
            for addr in ip_addresses:
                ip_str = addr[4][0]
                ip = ipaddress.ip_address(ip_str)
                
                if (ip.is_private or 
                    ip.is_loopback or 
                    ip.is_link_local or 
                    ip.is_multicast or 
                    ip.is_unspecified):
                    logger.warning(f"Blocked request to internal/private IP: {ip_str} (hostname: {hostname})")
                    return False
        except (socket.gaierror, ValueError) as e:
            logger.debug(f"DNS Resolution failed for {hostname}: {e}")
            # Si on ne peut pas résoudre, on bloque par prudence si on soupçonne une attaque, 
            # ou on laisse passer si c'est un hostname valide. Ici, on bloque.
            return False

        return True
    except Exception as e:
        logger.error(f"Error in is_safe_url: {e}")
        return False

def validate_service_url(url: str, expected_prefix: str) -> bool:
    """
    Vérifie si une URL de service interne (ex: BRAIN_API_URL) commence par un préfixe attendu.
    Utile pour empêcher le détournement de configuration.
    """
    if not url:
        return False
    return url.startswith(expected_prefix)
