"""Sandboxed Python code execution tool."""

import asyncio
import sys
import tempfile
from pathlib import Path

from .base import BaseTool, ToolResult

BLOCKED_MODULES = frozenset({
    "os", "subprocess", "shutil", "sys", "pathlib",
    "socket", "http", "urllib", "requests",
    "ctypes", "importlib", "code", "codeop",
    "compileall", "py_compile",
})

BLOCKED_NAMES = frozenset({
    "open", "exec", "eval", "compile", "__import__",
    "globals", "locals", "vars", "dir", "getattr", "setattr", "delattr",
    "breakpoint", "exit", "quit",
})

_GUARD_PREAMBLE = """\
import sys
_blocked = %r
_blocked_mods = %r
_orig_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

def _guarded_import(name, *args, **kwargs):
    top = name.split('.')[0]
    if top in _blocked_mods:
        raise ImportError(f"Import of '{name}' is not allowed")
    return _orig_import(name, *args, **kwargs)

try:
    __builtins__.__import__ = _guarded_import
except Exception:
    pass

for _name in _blocked:
    if _name in dir(__builtins__):
        try:
            setattr(__builtins__, _name, None)
        except Exception:
            pass
""" % (BLOCKED_NAMES, BLOCKED_MODULES)

_PYTHON_DIR = str(Path(sys.executable).parent)


class CodeExecutorTool(BaseTool):
    name = "code_executor"
    description = "Execute Python code in a sandboxed environment."
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
        full_code = _GUARD_PREAMBLE + "\n" + code

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(full_code)
            temp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tempfile.gettempdir(),
                env={
                    "PATH": _PYTHON_DIR,
                    "TEMP": tempfile.gettempdir(),
                    "TMP": tempfile.gettempdir(),
                },
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.TIMEOUT_SECONDS
            )

            if proc.returncode == 0:
                output = stdout.decode(errors="replace") or "(no output)"
                return ToolResult(success=True, output=output[:10000])
            return ToolResult(
                success=False,
                output=f"Error:\n{stderr.decode(errors='replace')[:5000]}",
            )
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(
                success=False,
                output=f"Execution timed out after {self.TIMEOUT_SECONDS}s",
            )
        except Exception as e:
            return ToolResult(success=False, output=f"Error: {e}")
        finally:
            Path(temp_path).unlink(missing_ok=True)
