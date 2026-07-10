"""Channel-layer construction, kept as a pure function so it is testable.

History: prod WebSocket handshakes returned 500 for weeks because settings
selected channels_redis whenever REDIS_URL was set while the package was not
in requirements — and the local InMemory fallback masked it. See
tests/backend/test_channel_layers.py.
"""

from typing import Optional

from django.core.exceptions import ImproperlyConfigured


def build_channel_layers(
    redis_url: Optional[str],
    is_production: bool,
    ssl_cert_reqs: str = "required",
) -> dict:
    if not redis_url:
        if is_production:
            # InMemoryChannelLayer is per-process: with several ASGI workers the
            # group fan-out silently breaks (players never see each other).
            # Refuse to boot rather than degrade invisibly.
            raise ImproperlyConfigured(
                "REDIS_URL is required in production: the channel layer must be "
                "shared across workers (InMemoryChannelLayer is per-process)."
            )
        return {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

    # channels_redis accepts each host as a plain URL string or a config dict.
    hosts: list[str | dict[str, object]]
    if redis_url.startswith("rediss://"):
        # Mirror the CACHES connection kwargs (REDIS_SSL_CERT_REQS): strict
        # certificate verification by default; "none" restores the legacy
        # insecure mode for providers whose cert chain fails validation — the
        # channel layer must match CACHES or it 500s while HTTP keeps working.
        hosts = [
            {
                "address": redis_url,
                "ssl_cert_reqs": None if ssl_cert_reqs == "none" else ssl_cert_reqs,
            }
        ]
    else:
        hosts = [redis_url]

    return {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": hosts},
        },
    }
