"""Hybrid retriever: Dense + BM25 + Reciprocal Rank Fusion."""

from dataclasses import dataclass


@dataclass
class RetrievalResult:
    content: str
    score: float
    metadata: dict
    source: str


class BM25Index:
    def __init__(self):
        self._documents: list[str] = []
        self._metadatas: list[dict] = []
        self._bm25 = None
        self._dirty = False

    def add(self, documents: list[str], metadatas: list[dict] = None):
        self._documents.extend(documents)
        self._metadatas.extend(metadatas or [{}] * len(documents))
        self._dirty = True

    def _ensure_built(self):
        if self._dirty and self._documents:
            from rank_bm25 import BM25Okapi

            tokenized = [doc.lower().split() for doc in self._documents]
            self._bm25 = BM25Okapi(tokenized)
            self._dirty = False

    def search(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        self._ensure_built()
        if not self._bm25 or not self._documents:
            return []

        scores = self._bm25.get_scores(query.lower().split())
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        return [
            RetrievalResult(
                content=self._documents[i],
                score=float(scores[i]),
                metadata=self._metadatas[i],
                source="bm25",
            )
            for i in top_indices
            if scores[i] > 0
        ]


class HybridRetriever:
    def __init__(
        self, vector_store, embedder, bm25_index: BM25Index = None, k: int = 20, rrf_k: int = 60
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.bm25_index = bm25_index or BM25Index()
        self.k = k
        self.rrf_k = rrf_k

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_embedding = await self.embedder.embed(query)

        dense_results = await self.vector_store.search(query_embedding, top_k=self.k)
        dense_items = [
            RetrievalResult(
                content=r["text"],
                score=1 - r["distance"],
                metadata=r["metadata"],
                source="dense",
            )
            for r in dense_results
        ]

        sparse_results = self.bm25_index.search(query, top_k=self.k)

        fused = self._reciprocal_rank_fusion(dense_items, sparse_results)
        return fused[:top_k]

    def _reciprocal_rank_fusion(
        self, list1: list[RetrievalResult], list2: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        scores: dict[str, float] = {}
        items: dict[str, RetrievalResult] = {}

        for rank, item in enumerate(list1):
            key = item.content[:100]
            scores[key] = scores.get(key, 0) + 1 / (rank + self.rrf_k)
            items[key] = item

        for rank, item in enumerate(list2):
            key = item.content[:100]
            scores[key] = scores.get(key, 0) + 1 / (rank + self.rrf_k)
            if key not in items:
                items[key] = item

        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
        results = []
        for key in sorted_keys:
            item = items[key]
            item.score = scores[key]
            item.source = "hybrid"
            results.append(item)

        return results
