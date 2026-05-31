"""Long-term memory: vector store backed."""

from .base import MemoryEntry, MemoryStore


class LongTermMemory(MemoryStore):
    def __init__(self, vector_store=None, embedder=None):
        self._vector_store = vector_store
        self._embedder = embedder
        self._entries: list[MemoryEntry] = []

    async def add(self, entry: MemoryEntry):
        self._entries.append(entry)
        if self._vector_store and self._embedder:
            embedding = await self._embedder.embed(entry.content)
            await self._vector_store.add(
                texts=[entry.content],
                embeddings=[embedding],
                metadatas=[entry.metadata],
            )

    async def search(self, query: str, k: int = 5) -> list[MemoryEntry]:
        if not self._vector_store or not self._embedder:
            return self._fallback_search(query, k)

        try:
            query_embedding = await self._embedder.embed(query)
            results = await self._vector_store.search(query_embedding, top_k=k)
            return [MemoryEntry(content=r["text"], metadata=r.get("metadata", {})) for r in results]
        except Exception:
            return self._fallback_search(query, k)

    def _fallback_search(self, query: str, k: int) -> list[MemoryEntry]:
        query_lower = query.lower()
        scored = [e for e in self._entries if query_lower in e.content.lower()]
        return scored[-k:]

    async def get_recent(self, k: int = 10) -> list[MemoryEntry]:
        return self._entries[-k:]

    async def clear(self):
        self._entries.clear()
