from django import template

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
def modulo(value, arg):
    try:
        return int(value) % int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def cdn_url(url):
    """Proxifie une image via Weserv.nl pour le cache et le SSL gratuit."""
    if not url: return ""
    if url.startswith('data:image'): return url # Pas besoin de proxy pour le base64
    # On nettoie le http:// ou https://
    clean_url = url.replace('http://', '').replace('https://', '')
    return f"https://images.weserv.nl/?url={clean_url}&output=webp&q=80"

@register.filter
def blur_cdn_url(url):
    """Idem cdn_url mais avec un flou de 50% pour les posters de jeux cachés."""
    if not url: return ""
    clean_url = url.replace('http://', '').replace('https://', '')
    return f"https://images.weserv.nl/?url={clean_url}&blur=50&output=webp&q=60"
