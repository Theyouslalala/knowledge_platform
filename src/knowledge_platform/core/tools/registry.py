"""Tool registry for plugin-based tool management."""

from typing import Any

from .base import BaseTool


class ToolRegistry:
    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool):
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> BaseTool | None:
        return cls._tools.get(name)

    @classmethod
    def get_all(cls) -> list[BaseTool]:
        return list(cls._tools.values())

    @classmethod
    def get_langchain_tools(cls) -> list[Any]:
        return [t.to_langchain_tool() for t in cls._tools.values() if t.name]

    @classmethod
    def clear(cls):
        cls._tools.clear()
