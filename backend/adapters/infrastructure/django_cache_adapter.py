from typing import Any, Dict, List, Optional

from core.ports.generic_cache_port import CachePort
from django.core.cache import cache


class DjangoCacheAdapter(CachePort):
    """Adapter du cache Django (Redis/locmem) vers `CachePort`.

    C'est l'unique point où le cache Django est référencé : le `core` ne dépend
    que du port abstrait.
    """

    def get(self, key: str, default: Any = None) -> Any:
        return cache.get(key, default)

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        cache.set(key, value, timeout=timeout)

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        return cache.get_many(keys)

    def set_many(self, mapping: Dict[str, Any], timeout: Optional[int] = None) -> None:
        cache.set_many(mapping, timeout=timeout)
