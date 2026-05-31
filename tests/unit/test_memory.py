"""Unit tests for memory system."""

import pytest
from src.knowledge_platform.core.memory.short_term import ShortTermMemory
from src.knowledge_platform.core.memory.base import MemoryEntry
from src.knowledge_platform.core.memory.manager import MemoryManager


@pytest.mark.asyncio
async def test_short_term_memory():
    mem = ShortTermMemory(max_size=10)
    await mem.add(MemoryEntry(content="hello", role="user"))
    await mem.add(MemoryEntry(content="world", role="assistant"))

    recent = await mem.get_recent(k=5)
    assert len(recent) == 2
    assert recent[0].content == "hello"


@pytest.mark.asyncio
async def test_short_term_memory_search():
    mem = ShortTermMemory()
    await mem.add(MemoryEntry(content="Python is great", role="user"))
    await mem.add(MemoryEntry(content="Java is also good", role="user"))
    await mem.add(MemoryEntry(content="Python rocks", role="user"))

    results = await mem.search("Python", k=5)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_memory_manager():
    manager = MemoryManager()
    await manager.store_interaction(MemoryEntry(content="test message", role="user"))
    context = await manager.get_context("task1", "test")
    assert "test message" in context
