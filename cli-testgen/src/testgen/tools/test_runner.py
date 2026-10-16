from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from .base import Tool, ToolResult

_SUMMARY_RE = re.compile(r"(\d+)\s+(passed|failed|error)")


class RunTestsTool(Tool):
    name = "run_tests"
    description = (
        "Execute pytest on the generated test file. Returns passed/failed/error counts, "
        "the pytest exit status, and the tail of the output (including failing tracebacks "
        "you can read in order to repair the tests)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "test_path": {"type": "string", "description": "Path to the test file to run"}
        },
        "required": ["test_path"],
    }

    def __init__(self, work_dir: Path, timeout: int = 180) -> None:
        self.work_dir = Path(work_dir).resolve()
        self.timeout = timeout

    def _env(self) -> dict:
        env = os.environ.copy()
        # Ensure `from <source module> import <func>` resolves.
        pythonpath = os.pathsep.join([str(self.work_dir), env.get("PYTHONPATH", "")])
        env["PYTHONPATH"] = pythonpath.rstrip(os.pathsep)
        return env

    def execute(self, test_path: str = "") -> ToolResult:
        path = Path(test_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            # Also try relative to the test working directory.
            alt = self.work_dir / Path(test_path).name
            if alt.exists():
                path = alt
        if not path.exists():
            return ToolResult(False, f"Test file not found: {test_path}")

        cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short", str(path)]
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self._env(),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, "Test run timed out", {"timed_out": True})

        output = f"{proc.stdout or ''}\n{proc.stderr or ''}"
        counts = {"passed": 0, "failed": 0, "error": 0}
        for match in _SUMMARY_RE.finditer(output):
            counts[match.group(2)] = int(match.group(1))

        all_passed = (
            proc.returncode == 0
            and counts["passed"] > 0
            and counts["failed"] == 0
            and counts["error"] == 0
        )
        data = {
            "passed": counts["passed"],
            "failed": counts["failed"],
            "errors": counts["error"],
            "all_passed": all_passed,
            "returncode": proc.returncode,
            "output_tail": output[-6000:],
        }
        summary = f"{counts['passed']} passed, {counts['failed']} failed, {counts['error']} error(s)"
        return ToolResult(all_passed, summary, data)
