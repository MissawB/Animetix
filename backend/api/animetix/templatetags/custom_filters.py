from django import template
from django.utils.safestring import mark_safe
import base64
import urllib.parse

register = template.Library()


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def sub(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    return sub(value, arg)


@register.filter
def modulo(value, arg):
    try:
        return int(value) % int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


from core.utils.security import sign_proxy_url, sanitize_html_content  # noqa: E402


@register.filter
def cdn_url(url):
    """Proxy local avec cache pour les images externes. Sécurisé par HMAC."""
    if not url:
        return ""
    if url.startswith("data:image"):
        return url

    # Sécurité : On encode l'URL source avant de la passer à Weserv
    quoted_url = urllib.parse.quote(url, safe="")
    weserv_url = f"https://images.weserv.nl/?url={quoted_url}&output=webp&q=80"

    # Signature cryptographique pour empêcher l'usage du proxy pour d'autres URLs
    sig = sign_proxy_url(weserv_url)
    encoded = base64.b64encode(weserv_url.encode()).decode()

    return f"/fr/cdn-proxy/?url={encoded}&sig={sig}"


@register.filter
def blur_cdn_url(url):
    """Idem cdn_url mais avec un flou de 50%. Sécurisé par HMAC."""
    if not url:
        return ""

    quoted_url = urllib.parse.quote(url, safe="")
    weserv_url = f"https://images.weserv.nl/?url={quoted_url}&blur=50&output=webp&q=60"

    sig = sign_proxy_url(weserv_url)
    encoded = base64.b64encode(weserv_url.encode()).decode()

    return f"/fr/cdn-proxy/?url={encoded}&sig={sig}"


@register.filter
def sanitize_ai(value):
    """
    Sanitizes LLM generated output to prevent XSS while allowing basic formatting.
    Uses centralized security utility.
    """
    cleaned = sanitize_html_content(value)
    return mark_safe(cleaned)  # nosec B308 B703
