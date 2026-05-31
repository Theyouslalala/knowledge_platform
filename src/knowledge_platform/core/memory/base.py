"""Memory store abstract base class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    content: str
    role: str = "user"
    metadata: dict = field(default_factory=dict)


class MemoryStore(ABC):
    @abstractmethod
    async def add(self, entry: MemoryEntry):
        ...

    @abstractmethod
    async def search(self, query: str, k: int = 5) -> list[MemoryEntry]:
        ...

    @abstractmethod
    async def get_recent(self, k: int = 10) -> list[MemoryEntry]:
        ...

    @abstractmethod
    async def clear(self):
        ...
