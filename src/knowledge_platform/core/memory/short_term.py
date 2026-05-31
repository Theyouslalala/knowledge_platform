"""Short-term memory: conversation buffer."""

from collections import deque

from .base import MemoryEntry, MemoryStore


class ShortTermMemory(MemoryStore):
    def __init__(self, max_size: int = 100):
        self._buffer: deque[MemoryEntry] = deque(maxlen=max_size)

    async def add(self, entry: MemoryEntry):
        self._buffer.append(entry)

    async def search(self, query: str, k: int = 5) -> list[MemoryEntry]:
        query_lower = query.lower()
        scored = []
        for entry in self._buffer:
            if query_lower in entry.content.lower():
                scored.append(entry)
        return scored[-k:]

    async def get_recent(self, k: int = 10) -> list[MemoryEntry]:
        return list(self._buffer)[-k:]

    async def clear(self):
        self._buffer.clear()
