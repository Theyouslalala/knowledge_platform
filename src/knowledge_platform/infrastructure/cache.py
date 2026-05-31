"""In-memory cache implementation (Redis-optional)."""

import time
from typing import Any, Optional


class InMemoryCache:
    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expiry = self._store[key]
            if expiry == 0 or time.time() < expiry:
                return value
            del self._store[key]
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        expiry = time.time() + ttl if ttl > 0 else 0
        self._store[key] = (value, expiry)

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None


cache = InMemoryCache()
