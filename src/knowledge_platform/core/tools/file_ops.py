"""File operations tool."""

from pathlib import Path

from .base import BaseTool, ToolResult


class FileReadTool(BaseTool):
    name = "file_read"
    description = "Read the contents of a file."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to read"},
        },
        "required": ["path"],
    }

    async def execute(self, path: str = "", **kwargs) -> ToolResult:
        try:
            content = Path(path).read_text(encoding="utf-8")
            return ToolResult(success=True, output=content[:10000])
        except Exception as e:
            return ToolResult(success=False, output=f"Error: {e}")


class FileWriteTool(BaseTool):
    name = "file_write"
    description = "Write content to a file."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    }

    async def execute(self, path: str = "", content: str = "", **kwargs) -> ToolResult:
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(content, encoding="utf-8")
            return ToolResult(success=True, output=f"Written {len(content)} chars to {path}")
        except Exception as e:
            return ToolResult(success=False, output=f"Error: {e}")
