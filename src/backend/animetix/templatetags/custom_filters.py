from django import template
import base64

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

@register.filter
def cdn_url(url):
    """Proxy local avec cache pour les images externes."""
    if not url: return ""
    if url.startswith('data:image'): return url
    # On utilise Weserv pour l'optimisation, mais notre proxy pour le cache local
    clean_url = url.replace('http://', '').replace('https://', '')
    weserv_url = f"https://images.weserv.nl/?url={clean_url}&output=webp&q=80"
    
    encoded = base64.b64encode(weserv_url.encode()).decode()
    return f"/fr/cdn-proxy/?url={encoded}"

@register.filter
def blur_cdn_url(url):
    """Idem cdn_url mais avec un flou de 50% pour les posters de jeux cachés."""
    if not url: return ""
    clean_url = url.replace('http://', '').replace('https://', '')
    weserv_url = f"https://images.weserv.nl/?url={clean_url}&blur=50&output=webp&q=60"
    
    encoded = base64.b64encode(weserv_url.encode()).decode()
    return f"/fr/cdn-proxy/?url={encoded}"

import bleach
from django.utils.safestring import mark_safe

@register.filter
def sanitize_ai(value):
    """
    Sanitizes LLM generated output to prevent XSS while allowing basic formatting.
    Uses bleach with a strict allowlist.
    """
    if not value:
        return ""
    
    # Allowed tags and attributes (Strict list)
    allowed_tags = ['p', 'b', 'i', 'u', 'em', 'strong', 'br', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote']
    allowed_attrs = {
        'code': ['class'],
        'pre': ['class'],
    }
    
    # Bleach cleaning
    cleaned = bleach.clean(
        value, 
        tags=allowed_tags, 
        attributes=allowed_attrs, 
        strip=True,
        strip_comments=True
    )
    
    # mark_safe should only be used after bleach has cleaned the input
    return mark_safe(cleaned)
