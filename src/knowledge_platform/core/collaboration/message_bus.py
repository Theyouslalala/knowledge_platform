"""In-process async message bus for agent communication."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class BusMessage:
    sender: str
    receiver: str
    content: str
    message_type: str = "info"
    metadata: dict = field(default_factory=dict)


class MessageBus:
    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self._history: list[BusMessage] = []

    async def publish(self, message: BusMessage):
        self._history.append(message)
        await self._queues[message.receiver].put(message)

    async def subscribe(self, receiver: str, timeout: float = 5.0) -> BusMessage | None:
        try:
            return await asyncio.wait_for(self._queues[receiver].get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def get_history(self, agent_name: str = None) -> list[BusMessage]:
        if agent_name:
            return [m for m in self._history if m.sender == agent_name or m.receiver == agent_name]
        return self._history.copy()

    def clear(self):
        self._queues.clear()
        self._history.clear()
