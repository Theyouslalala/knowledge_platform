"""Base agent abstraction."""

import asyncio
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

    async def _run_tools(self, **kwargs) -> list[str]:
        async def _run_one(tool):
            try:
                tool_kwargs = self._resolve_tool_kwargs(tool, kwargs)
                result = await tool.execute(**tool_kwargs)
                status = "OK" if result.success else "FAILED"
                return f"[{tool.name}] {status}: {result.output}"
            except Exception as e:
                return f"[{tool.name}] Error: {e}"

        results = await asyncio.gather(*[_run_one(t) for t in self.tools])
        return list(results)

    @staticmethod
    def _resolve_tool_kwargs(tool, kwargs: dict) -> dict:
        if not kwargs:
            return {}
        schema = getattr(tool, "parameters_schema", None) or {}
        required = schema.get("required", [])
        if not required:
            return kwargs
        primary = required[0]
        if primary in kwargs:
            return kwargs
        value = next(iter(kwargs.values()), "")
        return {primary: value}
