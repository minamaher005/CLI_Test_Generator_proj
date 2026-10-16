from __future__ import annotations

import ast
from pathlib import Path

from .base import LLMResponse, ToolCall


class MockProvider:
    """A scripted 'agent' with identical tool-calling behavior to the real provider.

    Used for offline demos, tests, and CI: analyze -> write -> run -> (coverage) -> done.
    It inspects the actual source file and generates genuinely runnable tests for simple
    functions (e.g. `add`), and callable smoke tests for anything else.
    """

    name = "mock"

    def __init__(self, source_path: Path, output_dir: Path, with_coverage: bool = True) -> None:
        self.source_path = Path(source_path).resolve()
        self.test_path = Path(output_dir).resolve() / f"{source_path.stem}_test.py"
        self.with_coverage = with_coverage
        self._step = 0

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        self._step += 1
        if self._step == 1:
            return LLMResponse(None, [ToolCall("analyze_ast", {"path": str(self.source_path)})])
        if self._step == 2:
            return LLMResponse(None, [ToolCall("write_test", {"content": self._scripted_test()})])
        if self._step == 3:
            return LLMResponse(None, [ToolCall("run_tests", {"test_path": str(self.test_path)})])
        if self.with_coverage and self._step == 4:
            return LLMResponse(None, [ToolCall("get_coverage", {"test_path": str(self.test_path)})])
        return LLMResponse(
            "Mock agent finished: analyze_ast, write_test, run_tests"
            + (" and get_coverage" if self.with_coverage else "")
            + " completed. See the generated report for results.",
            [],
        )

    def _function_names(self) -> list[str]:
        tree = ast.parse(self.source_path.read_text(encoding="utf-8"))
        return [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    def _scripted_test(self) -> str:
        funcs = self._function_names()
        stem = self.source_path.stem
        lines = ["import unittest", ""]
        lines += [f"from {stem} import {fn}" for fn in funcs]
        lines.append("")
        lines.append("")
        lines.append("class TestGenerated(unittest.TestCase):")
        for fn in funcs:
            lines += [
                "",
                f"    def test_{fn}_exists_and_is_callable(self):",
                f"        self.assertTrue(callable({fn}))",
            ]
            if fn == "add" and len(funcs) == 1:
                lines += [
                    "",
                    "    def test_add_positive_numbers(self):",
                    "        self.assertEqual(add(2, 3), 5)",
                    "",
                    "    def test_add_negative_numbers(self):",
                    "        self.assertEqual(add(-1, -1), -2)",
                    "",
                    "    def test_add_mixed_sign(self):",
                    "        self.assertEqual(add(-1, 1), 0)",
                    "",
                    "    def test_add_with_zero(self):",
                    "        self.assertEqual(add(0, 7), 7)",
                ]
        lines += ["", "", 'if __name__ == "__main__":', "    unittest.main()", ""]
        return "\n".join(lines)
