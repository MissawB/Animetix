from typing import Any, Optional

from core.ports.state_port import StatePort
from django.core.cache import cache


class DjangoCacheStateAdapter(StatePort):
    async def get_state(self, key: str) -> Optional[Any]:
        return await cache.aget(key)

    async def set_state(self, key: str, value: Any, timeout: Optional[int] = None):
        await cache.aset(key, value, timeout)

    async def delete_state(self, key: str):
        await cache.adelete(key)
