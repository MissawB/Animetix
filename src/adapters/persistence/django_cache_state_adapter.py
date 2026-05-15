from typing import Any, Optional
from django.core.cache import cache
from core.ports.state_port import StatePort

class DjangoCacheStateAdapter(StatePort):
    async def get_state(self, key: str) -> Optional[Any]:
        return cache.get(key)

    async def set_state(self, key: str, value: Any, timeout: Optional[int] = None):
        cache.set(key, value, timeout)

    async def delete_state(self, key: str):
        cache.delete(key)
