"""Memory manager coordinating all memory stores."""

import asyncio

from .base import MemoryEntry
from .long_term import LongTermMemory
from .short_term import ShortTermMemory
from .working import WorkingMemory


class MemoryManager:
    def __init__(
        self,
        short_term: ShortTermMemory | None = None,
        long_term: LongTermMemory | None = None,
        working: WorkingMemory | None = None,
    ):
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemory()
        self.working = working or WorkingMemory()

    async def get_context(self, task_id: str, query: str) -> str:
        recent, relevant = await asyncio.gather(
            self.short_term.get_recent(k=10),
            self.long_term.search(query, k=5),
        )
        task_context = self.working.get_all_context(task_id)

        parts = []
        if recent:
            parts.append("Recent conversation:")
            for e in recent:
                parts.append(f"  [{e.role}] {e.content[:200]}")

        if relevant:
            parts.append("\nRelevant memories:")
            for e in relevant:
                parts.append(f"  - {e.content[:200]}")

        if task_context:
            parts.append(f"\nTask context: {task_context}")

        return "\n".join(parts) if parts else ""

    async def store_interaction(self, entry: MemoryEntry):
        await self.short_term.add(entry)
        await self.long_term.add(entry)
