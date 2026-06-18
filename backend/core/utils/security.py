import contextlib
import ipaddress
import logging
import re
import socket
from typing import Any, List, Optional
from urllib.parse import urljoin, urlparse

import filetype
import httpx
from django.conf import settings

logger = logging.getLogger("animetix.security")

import hashlib  # noqa: E402
import hmac  # noqa: E402


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
        return False

    mime = kind.mime
    if mime not in allowed_mime_types:
        logger.warning(
            f"Type de fichier binaire non autorisé détecté : {mime}. Autorisé : {allowed_mime_types}"
        )
        return False

    return True


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Vérifie si la taille d'un fichier dépasse la limite autorisée.
    """
    if file_size > max_size:
        logger.warning(
            f"Tentative d'upload d'un fichier trop volumineux : {file_size} octets (Max: {max_size})."
        )
        return False
    return True


# --- SSRF PROTECTION ---
ALLOWED_INTERNAL_HOSTS = [
    "brain",
    "db",
    "redis",
    "chromadb",
    "neo4j",
    "localhost",
    "127.0.0.1",
]


def is_safe_url(
    url: str, allowed_schemes: Optional[List[str]] = None, allow_internal: bool = False
) -> bool:
    """
    Vérifie si une URL est sûre pour éviter les attaques SSRF.
    """
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    try:
        parsed = urlparse(url)
        if parsed.scheme not in allowed_schemes:
            logger.warning(f"Blocked unsafe protocol: {parsed.scheme} in URL: {url}")
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        is_whitelisted = hostname in ALLOWED_INTERNAL_HOSTS

        if is_whitelisted:
            if allow_internal:
                return True
            else:
                logger.warning(
                    f"Blocked internal host access (allow_internal=False): {hostname}"
                )
                return False

        try:
            ip_addresses = socket.getaddrinfo(hostname, None)
            for addr in ip_addresses:
                ip_str = addr[4][0]
                ip = ipaddress.ip_address(ip_str)

                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_multicast
                    or ip.is_unspecified
                ):
                    logger.warning(
                        f"Blocked request to internal/private IP: {ip_str} (hostname: {hostname})"
                    )
                    return False
        except (socket.gaierror, ValueError):
            return False

        return True
    except Exception as e:
        logger.error(f"Error in is_safe_url: {e}")
        return False


def safe_http_request(
    method: str,
    url: str,
    max_redirects: int = 3,
    allow_internal: bool = False,
    **kwargs,
) -> httpx.Response:
    """
    Effectue une requête HTTP en validant manuellement chaque redirection.
    """
    current_url = url
    for _ in range(max_redirects + 1):
        if not is_safe_url(current_url, allow_internal=allow_internal):
            logger.warning(f"Blocked request to unsafe URL: {current_url}")
            raise ValueError(f"Unsafe URL detected: {current_url}")

        res = httpx.request(method, current_url, follow_redirects=False, **kwargs)

        if res.is_redirect:
            location = res.headers.get("Location")
            if not location:
                return res
            current_url = urljoin(str(res.url), location)
            method = "GET"
            continue

        return res

    raise ValueError("Too many redirects")


async def safe_http_request_async(
    method: str,
    url: str,
    max_redirects: int = 3,
    allow_internal: bool = False,
    **kwargs,
) -> httpx.Response:
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


@contextlib.contextmanager
def stream_safe_http_request(
    method: str,
    url: str,
    max_redirects: int = 3,
    allow_internal: bool = False,
    **kwargs,
):
    """Context manager pour des requêtes HTTP streamées sécurisées."""
    current_url = url
    for _ in range(max_redirects + 1):
        if not is_safe_url(current_url, allow_internal=allow_internal):
            raise ValueError(f"Unsafe URL detected: {current_url}")

        with httpx.stream(
            method, current_url, follow_redirects=False, **kwargs
        ) as response:
            if response.is_redirect:
                location = response.headers.get("Location")
                if not location:
                    yield response
                    return
                current_url = urljoin(str(response.url), location)
                method = "GET"
                continue
            yield response
            return
    raise ValueError("Too many redirects")


@contextlib.asynccontextmanager
async def async_stream_safe_http_request(
    method: str,
    url: str,
    max_redirects: int = 3,
    allow_internal: bool = False,
    **kwargs,
):
    """Version asynchrone du context manager de stream."""
    current_url = url
    async with httpx.AsyncClient(follow_redirects=False) as client:
        for _ in range(max_redirects + 1):
            if not is_safe_url(current_url, allow_internal=allow_internal):
                raise ValueError(f"Unsafe URL detected: {current_url}")

            async with client.stream(method, current_url, **kwargs) as response:
                if response.is_redirect:
                    location = response.headers.get("Location")
                    if not location:
                        yield response
                        return
                    current_url = urljoin(str(response.url), location)
                    method = "GET"
                    continue
                yield response
                return
    raise ValueError("Too many redirects")


import bleach  # noqa: E402


def sanitize_html_content(value: str) -> str:
    """
    Sanitise le contenu HTML pour prévenir les attaques XSS.
    """
    if not value:
        return ""

    allowed_tags = [
        "p",
        "b",
        "i",
        "u",
        "em",
        "strong",
        "br",
        "ul",
        "ol",
        "li",
        "code",
        "pre",
        "blockquote",
        "h3",
        "h4",
        "span",
    ]
    allowed_attrs = {
        "code": ["class"],
        "pre": ["class"],
        "span": ["class", "style"],
    }

    cleaned = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True,
        strip_comments=True,
    )

    return cleaned


def sanitize_for_prompt(text: Any, max_length: int = 5000) -> Any:
    """
    Sanitise les données pour limiter les risques d'injection de prompt.
    Supporte les chaînes, listes et dictionnaires de manière récursive.
    """
    if text is None:
        return ""

    if isinstance(text, list):
        return [sanitize_for_prompt(item, max_length) for item in text]

    if isinstance(text, dict):
        return {k: sanitize_for_prompt(v, max_length) for k, v in text.items()}

    if not isinstance(text, str):
        return text

    text = text[:max_length]

    injection_patterns = [
        r"(?i)ignore\s+(all\s+)?previous",
        r"(?i)system\s+prompt",
        r"(?i)tu\s+es\s+maintenant",
        r"(?i)you\s+are\s+now",
        r"(?i)réponds\s+uniquement",
        r"(?i)output\s+only",
        r"(?i)forget\s+all",
        r"(?i)override",
        r"(?i)disregard",
        r"(?i)assistant\s+must",
        r"(?i)new\s+role",
        r"(?i)DAN\s+mode",
    ]

    for pattern in injection_patterns:
        text = re.sub(pattern, "[PROMPT_INJECTION_FILTERED]", text)

    text = text.replace('"""', "'''")
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    return text.strip()


def validate_service_url(url: str, expected_prefix: str) -> bool:
    """
    Vérifie si une URL de service interne commence par un préfixe attendu.
    """
    if not url:
        return False
    return url.startswith(expected_prefix)


class InternalServiceClient:
    """
    Client HTTP dédié aux communications entre services internes.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _resolve_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        return safe_http_request(
            method, self._resolve_url(path), allow_internal=True, **kwargs
        )

    @contextlib.contextmanager
    def stream_request(self, method: str, path: str, **kwargs):
        with stream_safe_http_request(
            method, self._resolve_url(path), allow_internal=True, **kwargs
        ) as response:
            yield response


class InternalAsyncServiceClient:
    """Version asynchrone du client interne."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _resolve_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        return await safe_http_request_async(
            method, self._resolve_url(path), allow_internal=True, **kwargs
        )

    @contextlib.asynccontextmanager
    async def stream_request(self, method: str, path: str, **kwargs):
        async with async_stream_safe_http_request(
            method, self._resolve_url(path), allow_internal=True, **kwargs
        ) as response:
            yield response


def sanitize_cypher_identifier(identifier: str, allowed_list: List[str]) -> str:
    """Sanitise un identifiant Cypher (label ou relation) par rapport à une liste blanche."""
    if identifier in allowed_list:
        return identifier
    logger.warning(f"Blocked unsafe Cypher identifier: {identifier}")
    raise ValueError(f"Unsafe Cypher identifier: {identifier}")
