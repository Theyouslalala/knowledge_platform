"""Full RAG pipeline orchestrator with Agentic RAG features."""

from .chunker import Chunk, ChunkingStrategy, RecursiveChunker
from .document_processor import DocumentProcessor
from .embedder import BaseEmbedder
from .retriever import BM25Index, HybridRetriever, RetrievalResult
from .reranker import CrossEncoderReranker
from .vector_store import VectorStore


class QueryExpander:
    def __init__(self, llm=None):
        self._llm = llm

    async def expand(self, query: str, num_queries: int = 3) -> list[str]:
        if self._llm is None:
            return [query]

        prompt = f"""Generate {num_queries} different search queries that would help find information to answer: {query}

Return each query on a separate line, no numbering."""

        try:
            response = await self._llm.ainvoke(prompt)
            queries = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
            return [query] + queries[:num_queries]
        except Exception:
            return [query]


class ContextualCompressor:
    def __init__(self, llm=None):
        self._llm = llm

    async def compress(self, query: str, documents: list[RetrievalResult]) -> list[RetrievalResult]:
        if self._llm is None or not documents:
            return documents

        docs_text = "\n\n".join(
            f"[{i+1}] {doc.content[:500]}" for i, doc in enumerate(documents)
        )

        prompt = f"""Given the question: {query}

Extract only the relevant information from these documents. Return the relevant passages with their document numbers.

Documents:
{docs_text}"""

        try:
            response = await self._llm.ainvoke(prompt)
            compressed = response.content.strip()
            if compressed and len(compressed) > 50:
                return [RetrievalResult(content=compressed, score=1.0, metadata={}, source="compressed")]
        except Exception:
            pass

        return documents


class RAGPipeline:
    def __init__(
        self,
        document_processor: DocumentProcessor = None,
        chunker: ChunkingStrategy = None,
        embedder: BaseEmbedder = None,
        vector_store: VectorStore = None,
        retriever: HybridRetriever = None,
        reranker: CrossEncoderReranker = None,
        query_expander: QueryExpander = None,
        compressor: ContextualCompressor = None,
    ):
        self.document_processor = document_processor or DocumentProcessor()
        self.chunker = chunker or RecursiveChunker()
        self.embedder = embedder
        self.vector_store = vector_store or VectorStore()
        self.bm25_index = BM25Index()
        self.retriever = retriever
        self.reranker = reranker or CrossEncoderReranker()
        self.query_expander = query_expander or QueryExpander()
        self.compressor = compressor or ContextualCompressor()

    async def ingest(self, file_path: str, metadata: dict = None) -> dict:
        doc = await self.document_processor.process(file_path)
        chunks = self.chunker.chunk(doc.content, metadata={**doc.metadata, **(metadata or {})})

        if self.embedder:
            texts = [c.content for c in chunks]
            embeddings = await self.embedder.embed_batch(texts)
            ids = await self.vector_store.add(
                texts=texts,
                embeddings=embeddings,
                metadatas=[c.metadata for c in chunks],
            )
            self.bm25_index.add(texts, [c.metadata for c in chunks])
        else:
            ids = []

        return {
            "chunks": len(chunks),
            "ids": ids,
            "file_type": doc.file_type,
        }

    async def retrieve(self, query: str, top_k: int = 5, use_expansion: bool = True) -> list[RetrievalResult]:
        if not self.retriever:
            if self.embedder:
                self.retriever = HybridRetriever(
                    self.vector_store, self.embedder, self.bm25_index
                )
            else:
                return []

        if use_expansion:
            queries = await self.query_expander.expand(query)
            all_results = []
            for q in queries:
                results = await self.retriever.retrieve(q, top_k=top_k)
                all_results.extend(results)

            seen = set()
            unique = []
            for r in all_results:
                key = r.content[:100]
                if key not in seen:
                    seen.add(key)
                    unique.append(r)
            results = unique[:top_k]
        else:
            results = await self.retriever.retrieve(query, top_k=top_k)

        results = self.reranker.rerank(query, results, top_k=top_k)
        results = await self.compressor.compress(query, results)

        return results
