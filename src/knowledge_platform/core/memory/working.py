"""Working memory: current task context."""

from .base import MemoryEntry, MemoryStore


class WorkingMemory(MemoryStore):
    def __init__(self):
        self._context: dict[str, dict] = {}

    def set_task_context(self, task_id: str, key: str, value):
        if task_id not in self._context:
            self._context[task_id] = {}
        self._context[task_id][key] = value

    def get_task_context(self, task_id: str, key: str, default=None):
        return self._context.get(task_id, {}).get(key, default)

    def get_all_context(self, task_id: str) -> dict:
        return self._context.get(task_id, {})

    async def add(self, entry: MemoryEntry):
        task_id = entry.metadata.get("task_id", "default")
        self.set_task_context(task_id, "last_entry", entry.content)

    async def search(self, query: str, k: int = 5) -> list[MemoryEntry]:
        return []

    async def get_recent(self, k: int = 10) -> list[MemoryEntry]:
        return []

    async def clear(self):
        self._context.clear()

    def clear_task(self, task_id: str):
        self._context.pop(task_id, None)
