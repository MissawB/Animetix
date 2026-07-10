"""Channel-layer config: the prod WS-500 regression suite.

Prod WebSocket handshakes 500'd with ModuleNotFoundError('channels_redis'):
settings selected the Redis channel layer whenever REDIS_URL was set, but the
package was never in requirements. Locally REDIS_URL is unset, so the InMemory
fallback masked the missing dependency. These tests pin the three guarantees:
the backend package is installed and importable, production fails fast instead
of silently degrading, and rediss:// URLs carry the same relaxed-cert kwargs
as the CACHES block (the working reference for this Redis instance).
"""

import pytest
from animetix_project.channels_config import build_channel_layers
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


def test_channels_redis_backend_is_importable():
    # Guards the exact prod failure: the backend string must resolve to an
    # installed class, not just be syntactically present in settings.
    assert import_string("channels_redis.core.RedisChannelLayer") is not None


def test_settings_channel_layer_backend_is_importable():
    from django.conf import settings

    backend = settings.CHANNEL_LAYERS["default"]["BACKEND"]
    assert import_string(backend) is not None


def test_production_without_redis_url_fails_fast():
    # InMemoryChannelLayer is per-process; with 2 uvicorn workers the group
    # fan-out silently breaks. Refuse to boot instead.
    with pytest.raises(ImproperlyConfigured):
        build_channel_layers(redis_url=None, is_production=True)


def test_dev_without_redis_url_falls_back_to_inmemory():
    layers = build_channel_layers(redis_url=None, is_production=False)
    assert layers["default"]["BACKEND"] == "channels.layers.InMemoryChannelLayer"


def test_plain_redis_url_uses_redis_backend_without_ssl_kwargs():
    layers = build_channel_layers(
        redis_url="redis://example.com:6379/0", is_production=True
    )
    assert layers["default"]["BACKEND"] == "channels_redis.core.RedisChannelLayer"
    assert layers["default"]["CONFIG"]["hosts"] == ["redis://example.com:6379/0"]


def test_rediss_url_verifies_certs_by_default():
    # Secure by default: a rediss:// URL gets strict certificate verification
    # unless the escape hatch is explicitly used (mirrors REDIS_SSL_CERT_REQS).
    layers = build_channel_layers(
        redis_url="rediss://example.com:6380/0", is_production=True
    )
    (host,) = layers["default"]["CONFIG"]["hosts"]
    assert host["address"] == "rediss://example.com:6380/0"
    assert host["ssl_cert_reqs"] == "required"


def test_rediss_url_none_escape_hatch_relaxes_cert_verification():
    # REDIS_SSL_CERT_REQS=none restores the legacy insecure mode for providers
    # whose certificate chain fails validation — same kwargs as the CACHES block.
    layers = build_channel_layers(
        redis_url="rediss://example.com:6380/0",
        is_production=True,
        ssl_cert_reqs="none",
    )
    (host,) = layers["default"]["CONFIG"]["hosts"]
    assert host["ssl_cert_reqs"] is None
