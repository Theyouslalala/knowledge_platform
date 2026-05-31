"""Calculator tool for mathematical expressions."""

import ast
import math
import operator

from .base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    name = "calculator"
    description = (
        "Evaluate mathematical expressions. "
        "Supports basic arithmetic, trigonometry, and common math functions."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": (
                    "Mathematical expression to evaluate, e.g. '2 + 3 * 4' or 'sqrt(16)'"
                ),
            }
        },
        "required": ["expression"],
    }

    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    SAFE_FUNCTIONS = {
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

    def _safe_eval(self, node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in self.SAFE_OPERATORS:
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            return self.SAFE_OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.SAFE_OPERATORS:
            return self.SAFE_OPERATORS[type(node.op)](self._safe_eval(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.SAFE_FUNCTIONS:
                func = self.SAFE_FUNCTIONS[func_name]
                args = [self._safe_eval(arg) for arg in node.args]
                return func(*args)
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    async def execute(self, expression: str = "", **kwargs) -> ToolResult:
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._safe_eval(tree)
            return ToolResult(success=True, output=str(result))
        except (ValueError, TypeError, ZeroDivisionError, SyntaxError) as e:
            return ToolResult(success=False, output=f"Error: {e}")
        except Exception:
            return ToolResult(
                success=False, output="Error: Expression not allowed for security reasons"
            )
