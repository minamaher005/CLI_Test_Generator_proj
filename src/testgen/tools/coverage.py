from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .base import Tool, ToolResult


class CoverageTool(Tool):
    name = "get_coverage"
    description = (
        "Run the test file under coverage.py and report line coverage for the source file, "
        "including the exact uncovered line numbers. Call after tests pass to find missing "
        "edge cases worth adding."
    )
    parameters = {
        "type": "object",
        "properties": {
            "test_path": {"type": "string", "description": "Path to the test file to measure"}
        },
        "required": ["test_path"],
    }

    def __init__(self, source_path: Path, output_dir: Path, timeout: int = 240) -> None:
        self.source_path = Path(source_path).resolve()
        self.work_dir = self.source_path.parent
        self.output_dir = Path(output_dir).resolve()
        self.timeout = timeout

    def _env(self) -> dict:
        env = os.environ.copy()
        pythonpath = os.pathsep.join([str(self.work_dir), env.get("PYTHONPATH", "")])
        env["PYTHONPATH"] = pythonpath.rstrip(os.pathsep)
        env["COVERAGE_FILE"] = str(self.output_dir / ".coverage")
        return env

    def execute(self, test_path: str = "") -> ToolResult:
        path = Path(test_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            alt = self.work_dir / Path(test_path).name
            if alt.exists():
                path = alt
        if not path.exists():
            return ToolResult(False, f"Test file not found: {test_path}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_out = self.output_dir / "coverage.json"
        if json_out.exists():
            json_out.unlink()

        run_cmd = [
            sys.executable, "-m", "coverage", "run",
            f"--source={self.work_dir}", "-m", "pytest", "-q", "--tb=no", str(path),
        ]
        try:
            proc = subprocess.run(
                run_cmd, cwd=self.work_dir, capture_output=True, text=True,
                timeout=self.timeout, env=self._env(),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, "Coverage run timed out", {"timed_out": True})

        # pytest exits 1 when tests fail; that still produces coverage data. Anything
        # else (2, 3, 4...) means collection/usage errors.
        if proc.returncode not in (0, 1):
            return ToolResult(
                False,
                f"coverage run failed (exit {proc.returncode}): {(proc.stderr or '')[-800:]}",
                {"returncode": proc.returncode},
            )

        json_cmd = [sys.executable, "-m", "coverage", "json", "-o", str(json_out)]
        json_proc = subprocess.run(
            json_cmd, cwd=self.work_dir, capture_output=True, text=True,
            timeout=self.timeout, env=self._env(),
        )
        if json_proc.returncode != 0:
            return ToolResult(False, f"coverage json failed: {(json_proc.stderr or '')[-800:]}")

        try:
            data = json.loads(json_out.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            return ToolResult(False, f"Cannot read coverage report: {e}")

        entry = None
        for fpath, fdata in data.get("files", {}).items():
            # Keys may be relative to the subprocess cwd; resolve them there.
            candidate = Path(fpath)
            if not candidate.is_absolute():
                candidate = self.work_dir / candidate
            if candidate.resolve() == self.source_path.resolve():
                entry = fdata
                break
        if entry is None:
            return ToolResult(False, "Source file not found in coverage report")

        percent = entry.get("summary", {}).get("percent_covered", 0.0)
        missing = entry.get("missing_lines", [])
        return ToolResult(
            True,
            f"Line coverage: {percent:.1f}% ({len(missing)} uncovered lines)",
            {"percent": round(percent, 2), "missing_lines": missing},
        )
