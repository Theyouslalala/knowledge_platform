"""ChromaDB vector store wrapper."""

from pathlib import Path


class VectorStore:
    def __init__(self, persist_dir: str = "./data/chroma", collection_name: str = "documents"):
        self._persist_dir = persist_dir
        self._collection_name = collection_name
        self._client = None
        self._collection = None

    def _init_client(self):
        if self._client is None:
            import chromadb

            Path(self._persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    async def add(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] = None,
        ids: list[str] = None,
    ) -> list[str]:
        self._init_client()
        if ids is None:
            import uuid

            ids = [str(uuid.uuid4()) for _ in texts]

        self._collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas or [{}] * len(texts),
            ids=ids,
        )
        return ids

    async def search(
        self, query_embedding: list[float], top_k: int = 5, where: dict = None
    ) -> list[dict]:
        self._init_client()
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self._collection.count() or 1),
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        items = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                item = {
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                }
                items.append(item)
        return items

    async def delete(self, ids: list[str]):
        self._init_client()
        self._collection.delete(ids=ids)

    async def delete_by_filter(self, where: dict):
        self._init_client()
        results = self._collection.get(where=where)
        if results and results["ids"]:
            self._collection.delete(ids=results["ids"])

    def count(self) -> int:
        self._init_client()
        return self._collection.count()
