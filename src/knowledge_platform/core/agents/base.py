"""Base agent abstraction."""

from abc import ABC, abstractmethod
from typing import Any

from .state import AgentState


class BaseAgent(ABC):
    def __init__(self, name: str, llm: Any, tools: list = None, system_prompt: str = ""):
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.system_prompt = system_prompt

    @abstractmethod
    async def execute(self, state: AgentState) -> dict:
        """Execute the agent and return state updates."""
        ...

    def _build_tool_map(self) -> dict:
        return {getattr(t, "name", str(i)): t for i, t in enumerate(self.tools)}
