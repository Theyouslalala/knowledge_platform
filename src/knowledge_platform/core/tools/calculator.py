"""Calculator tool for mathematical expressions."""

import math

from .base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate mathematical expressions. Supports basic arithmetic, trigonometry, and common math functions."
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate, e.g. '2 + 3 * 4' or 'sqrt(16)'",
            }
        },
        "required": ["expression"],
    }

    SAFE_NAMES = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pow": pow,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "pi": math.pi,
        "e": math.e,
    }

    async def execute(self, expression: str = "", **kwargs) -> ToolResult:
        try:
            result = eval(expression, {"__builtins__": {}}, self.SAFE_NAMES)  # noqa: S307
            return ToolResult(success=True, output=str(result))
        except Exception as e:
            return ToolResult(success=False, output=f"Error: {e}")
