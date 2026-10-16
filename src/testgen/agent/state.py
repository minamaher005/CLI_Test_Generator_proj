from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Everything the agent accumulates during a run: conversation + observations."""

    messages: list[dict] = field(default_factory=list)
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0

    def record_tool(self, name: str, arguments: dict, ok: bool, data: dict[str, Any]) -> None:
        self.tool_trace.append(
            {"iteration": self.iterations, "tool": name, "arguments": arguments, "ok": ok, "data": data}
        )

    def last_result(self, tool_name: str, ok_only: bool = True) -> dict | None:
        """Most recent trace entry for a tool (ok_only=False includes failures)."""
        for entry in reversed(self.tool_trace):
            if entry["tool"] == tool_name and (entry["ok"] or not ok_only):
                return entry
        return None
