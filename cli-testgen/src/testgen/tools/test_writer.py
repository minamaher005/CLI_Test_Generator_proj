from __future__ import annotations

import ast
import re
from pathlib import Path

from .base import Tool, ToolResult


def strip_code_fences(text: str) -> str:
    """LLMs love wrapping code in ```python fences; strip them before use."""
    text = text.strip()
    match = re.match(r"^```[a-zA-Z0-9_+-]*\n(.*)\n```$", text, re.DOTALL)
    return match.group(1) if match else text


class WriteTestTool(Tool):
    name = "write_test"
    description = (
        "Write a generated unittest file into the sandbox output directory. The content "
        "is stripped of markdown fences and must be syntactically valid Python - invalid "
        "content is rejected and reported so it can be rewritten. Returns the written path."
    )
    parameters = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Full unittest module source code"},
            "filename": {
                "type": "string",
                "description": "Optional filename inside the sandbox (default: <source>_test.py)",
            },
        },
        "required": ["content"],
    }

    def __init__(self, output_dir: Path, default_filename: str) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.default_filename = default_filename

    def execute(self, content: str = "", filename: str | None = None) -> ToolResult:
        cleaned = strip_code_fences(content or "")
        if not cleaned:
            return ToolResult(False, "Nothing to write: content was empty")

        try:
            ast.parse(cleaned)
        except SyntaxError as e:
            return ToolResult(
                False,
                f"Generated file has a syntax error - fix it and retry: {e}",
                {"syntax_ok": False},
            )

        # Basename-only: the file always lands inside the sandbox, never elsewhere.
        name = Path(filename or self.default_filename).name
        target = (self.output_dir / name).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(cleaned, encoding="utf-8")
        return ToolResult(True, f"Wrote {target}", {"path": str(target), "syntax_ok": True})
