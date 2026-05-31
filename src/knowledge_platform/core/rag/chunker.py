"""Text chunking strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Chunk:
    content: str
    index: int
    metadata: dict


class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        ...


class FixedSizeChunker(ChunkingStrategy):
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        metadata = metadata or {}
        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size
            content = text[start:end]

            if content.strip():
                chunks.append(Chunk(content=content.strip(), index=index, metadata=metadata.copy()))
                index += 1

            start += self.chunk_size - self.overlap

        return chunks


class RecursiveChunker(ChunkingStrategy):
    SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        metadata = metadata or {}
        raw_chunks = self._split_recursive(text)
        chunks = []
        for i, content in enumerate(raw_chunks):
            if content.strip():
                chunks.append(Chunk(content=content.strip(), index=i, metadata=metadata.copy()))
        return chunks

    def _split_recursive(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        for separator in self.SEPARATORS:
            if separator in text:
                parts = text.split(separator)
                result = []
                current = ""
                for part in parts:
                    if len(current) + len(part) + len(separator) <= self.chunk_size:
                        current += (separator if current else "") + part
                    else:
                        if current:
                            result.append(current)
                        current = part
                if current:
                    result.append(current)

                final = []
                for r in result:
                    if len(r) > self.chunk_size:
                        final.extend(self._split_recursive(r))
                    else:
                        final.append(r)
                return final

        return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]


class SemanticChunker(ChunkingStrategy):
    def __init__(self, max_chunk_size: int = 512):
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        metadata = metadata or {}
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current = ""
        index = 0

        for para in paragraphs:
            if len(current) + len(para) + 2 <= self.max_chunk_size:
                current += ("\n\n" if current else "") + para
            else:
                if current:
                    chunks.append(Chunk(content=current, index=index, metadata=metadata.copy()))
                    index += 1
                current = para

        if current:
            chunks.append(Chunk(content=current, index=index, metadata=metadata.copy()))

        return chunks
