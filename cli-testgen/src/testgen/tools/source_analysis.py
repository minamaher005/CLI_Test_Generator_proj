from __future__ import annotations

import ast
from pathlib import Path

from .base import Tool, ToolResult


def describe_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    """Extract structured metadata from a function definition node."""
    params = []
    for arg in node.args.args:
        params.append(
            {
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None,
                "default": None,
            }
        )
    # Map defaults to the last N positional args
    defaults = list(node.args.defaults)
    if defaults:
        offset = len(params) - len(defaults)
        for i, default in enumerate(defaults):
            params[offset + i]["default"] = ast.unparse(default)

    raises: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Raise) and sub.exc is not None:
            raises.add(ast.unparse(sub.exc).split("(")[0])

    return {
        "name": node.name,
        "async": isinstance(node, ast.AsyncFunctionDef),
        "params": params,
        "returns": ast.unparse(node.returns) if node.returns else None,
        "raises": sorted(raises),
    }


class AnalyzeSourceTool(Tool):
    name = "analyze_ast"
    description = (
        "Parse a Python source file into an AST and return structured metadata about "
        "its top-level functions (name, async, parameters with annotations/defaults, "
        "return annotation, raised exception types) and imports. Call this first to "
        "understand what to test."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the Python source file"}
        },
        "required": ["path"],
    }

    def execute(self, path: str = "") -> ToolResult:
        if not path or not str(path).strip():
            return ToolResult(False, "Missing required argument: path")
        try:
            source = Path(path).read_text(encoding="utf-8")
        except OSError as e:
            return ToolResult(False, f"Cannot read file '{path}': {e}")
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as e:
            return ToolResult(False, f"SyntaxError in '{path}': {e}")

        functions = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(describe_function(node))

        imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"from {node.module} import " + ", ".join(a.name for a in node.names))

        data = {
            "path": path,
            "num_functions": len(functions),
            "functions": functions,
            "imports": imports,
        }
        return ToolResult(True, f"Found {len(functions)} top-level function(s) in {path}", data)
