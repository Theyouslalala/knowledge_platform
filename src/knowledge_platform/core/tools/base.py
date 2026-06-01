"""Base tool abstraction and tool result."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    success: bool
    output: str
    metadata: dict = field(default_factory=dict)


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters_schema: dict = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.parameters_schema is not None:
            cls.parameters_schema = dict(cls.parameters_schema)

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult: ...

    def to_langchain_tool(self):
        from langchain_core.tools import StructuredTool
        from pydantic import create_model

        fields = {}
        for param_name, param_info in (self.parameters_schema or {}).get("properties", {}).items():
            param_type = str if param_info.get("type") == "string" else Any
            required = param_name in self.parameters_schema.get("required", [])
            default = ... if required else None
            fields[param_name] = (param_type, default)

        args_schema = create_model(f"{self.name}Args", **fields) if fields else None

        async def _func(**kwargs):
            result = await self.execute(**kwargs)
            return result.output

        return StructuredTool(
            name=self.name,
            description=self.description,
            args_schema=args_schema,
            coroutine=_func,
        )
