"""Unit tests for text chunking."""

from src.knowledge_platform.core.rag.chunker import (
    FixedSizeChunker,
    RecursiveChunker,
    SemanticChunker,
)


def test_fixed_size_chunker():
    chunker = FixedSizeChunker(chunk_size=100, overlap=20)
    text = "word " * 50
    chunks = chunker.chunk(text)
    assert len(chunks) > 1
    assert all(len(c.content) <= 120 for c in chunks)


def test_recursive_chunker():
    chunker = RecursiveChunker(chunk_size=200)
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunker.chunk(text)
    assert len(chunks) >= 1


def test_semantic_chunker():
    chunker = SemanticChunker(max_chunk_size=200)
    text = "First topic.\n\nSecond topic.\n\nThird topic."
    chunks = chunker.chunk(text)
    assert len(chunks) >= 1
    assert chunks[0].index == 0


def test_chunker_metadata():
    chunker = FixedSizeChunker(chunk_size=50)
    chunks = chunker.chunk("hello world", metadata={"source": "test"})
    assert chunks[0].metadata["source"] == "test"
