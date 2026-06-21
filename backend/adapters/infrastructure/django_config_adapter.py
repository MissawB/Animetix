from typing import Any

from core.ports.config_port import ConfigPort
from django.conf import settings


class DjangoConfigAdapter(ConfigPort):
    """Adapter exposant `django.conf.settings` via `ConfigPort`.

    Unique point où les settings Django sont lus côté domaine : le `core` ne
    dépend que du port abstrait.
    """

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(settings, key, default)
