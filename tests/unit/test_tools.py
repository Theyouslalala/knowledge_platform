"""Unit tests for tool system."""

import pytest
from src.knowledge_platform.core.tools.calculator import CalculatorTool
from src.knowledge_platform.core.tools.code_executor import CodeExecutorTool
from src.knowledge_platform.core.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_calculator_basic():
    tool = CalculatorTool()
    result = await tool.execute(expression="2 + 3")
    assert result.success is True
    assert result.output == "5"


@pytest.mark.asyncio
async def test_calculator_complex():
    tool = CalculatorTool()
    result = await tool.execute(expression="sqrt(16) + pow(2, 3)")
    assert result.success is True
    assert result.output == "12.0"


@pytest.mark.asyncio
async def test_calculator_error():
    tool = CalculatorTool()
    result = await tool.execute(expression="1/0")
    assert result.success is False


@pytest.mark.asyncio
async def test_code_executor():
    tool = CodeExecutorTool()
    result = await tool.execute(code="print('hello')")
    assert result.success is True
    assert "hello" in result.output


@pytest.mark.asyncio
async def test_code_executor_error():
    tool = CodeExecutorTool()
    result = await tool.execute(code="raise ValueError('test')")
    assert result.success is False


def test_registry():
    ToolRegistry.clear()
    tool = CalculatorTool()
    ToolRegistry.register(tool)
    assert ToolRegistry.get("calculator") is tool
    assert len(ToolRegistry.get_all()) == 1
    ToolRegistry.clear()
