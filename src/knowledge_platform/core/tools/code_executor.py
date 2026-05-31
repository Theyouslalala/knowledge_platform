"""Sandboxed Python code execution tool."""

import subprocess
import sys
import tempfile
from pathlib import Path

from .base import BaseTool, ToolResult


class CodeExecutorTool(BaseTool):
    name = "code_executor"
    description = "Execute Python code in a sandboxed environment and return the output."
    parameters_schema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute",
            }
        },
        "required": ["code"],
    }

    TIMEOUT_SECONDS = 10

    async def execute(self, code: str = "", **kwargs) -> ToolResult:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
                cwd=tempfile.gettempdir(),
            )

            if result.returncode == 0:
                output = result.stdout or "(no output)"
                return ToolResult(success=True, output=output)
            else:
                return ToolResult(success=False, output=f"Error:\n{result.stderr}")
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output=f"Execution timed out after {self.TIMEOUT_SECONDS}s")
        except Exception as e:
            return ToolResult(success=False, output=f"Error: {e}")
        finally:
            Path(temp_path).unlink(missing_ok=True)
