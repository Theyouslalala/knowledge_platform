"""Unit tests for CodeExecutorTool sandbox."""

import pytest

from src.knowledge_platform.core.tools.code_executor import CodeExecutorTool


@pytest.mark.asyncio
async def test_basic_execution():
    tool = CodeExecutorTool()
    result = await tool.execute(code="print(1 + 1)")
    assert result.success is True
    assert "2" in result.output


@pytest.mark.asyncio
async def test_blocked_os_import():
    tool = CodeExecutorTool()
    result = await tool.execute(code="import os; os.system('echo pwned')")
    assert result.success is False


@pytest.mark.asyncio
async def test_blocked_subprocess_import():
    tool = CodeExecutorTool()
    result = await tool.execute(code="import subprocess; subprocess.run(['echo', 'test'])")
    assert result.success is False


@pytest.mark.asyncio
async def test_blocked_open_builtin():
    tool = CodeExecutorTool()
    result = await tool.execute(code="f = open('/etc/passwd'); print(f.read())")
    assert result.success is False


@pytest.mark.asyncio
async def test_blocked_exec_builtin():
    tool = CodeExecutorTool()
    result = await tool.execute(code="exec('import os; os.system(\"echo pwned\")')")
    assert result.success is False


@pytest.mark.asyncio
async def test_safe_math_works():
    tool = CodeExecutorTool()
    result = await tool.execute(code="x = 2 ** 10; print(x)")
    assert result.success is True
    assert "1024" in result.output


@pytest.mark.asyncio
async def test_timeout():
    tool = CodeExecutorTool()
    tool.TIMEOUT_SECONDS = 1
    result = await tool.execute(code="import time; time.sleep(10)")
    assert result.success is False
    assert "timed out" in result.output.lower()
