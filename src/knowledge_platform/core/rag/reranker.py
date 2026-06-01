"""Cross-encoder reranker."""

import asyncio
from dataclasses import dataclass


@dataclass
class RerankerResult:
    content: str
    score: float
    metadata: dict


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self._model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self._model_name)

    async def rerank(self, query: str, documents: list, top_k: int = 5) -> list[RerankerResult]:
        if not documents:
            return []

        if self._model is None:
            await asyncio.to_thread(self._load_model)

        pairs = [(query, getattr(doc, "content", str(doc))) for doc in documents]
        scores = await asyncio.to_thread(self._model.predict, pairs)

        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc, score in scored_docs[:top_k]:
            results.append(RerankerResult(
                content=getattr(doc, "content", str(doc)),
                score=float(score),
                metadata=getattr(doc, "metadata", {}),
            ))

        return results
