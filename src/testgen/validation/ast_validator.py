from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_input_file(path: str | Path) -> ValidationReport:
    """Gate the input before invoking the agent.

    Hard errors: unreadable file, syntax errors, zero top-level functions.
    Warnings: multiple functions (agent will test them all).
    """
    report = ValidationReport(ok=False)
    path = Path(path)

    if not path.exists():
        report.errors.append(f"File not found: {path}")
        return report

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as e:
        report.errors.append(f"Cannot read file: {e}")
        return report

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        report.errors.append(f"SyntaxError: {e}")
        return report

    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not functions:
        report.errors.append("No top-level functions found - nothing to test")
        return report
    if len(functions) > 1:
        names = ", ".join(f.name for f in functions)
        report.warnings.append(f"Multiple functions found ({names}) - tests will cover all of them")

    report.ok = True
    return report


def describe_file(path: str | Path) -> dict:
    """Quick summary used for the xtask user-facing context."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    functions = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return {"functions": functions}
