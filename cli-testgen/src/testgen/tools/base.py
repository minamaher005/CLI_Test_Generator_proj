from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Structured result returned by every tool; fed back to the agent as JSON."""

    ok: bool
    summary: str
    data: dict[str, Any] = field(default_factory=dict)

    def as_payload(self) -> str:
        payload = {"ok": self.ok, "summary": self.summary, **self.data}
        return json.dumps(payload, default=str)


class Tool(ABC):
    """A capability the LLM agent can invoke via tool calling."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the function arguments

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult: ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self.last_results: list[ToolResult] = []

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        try:
            result = self.get(name).execute(**arguments)
        except TypeError as e:
            result = ToolResult(False, f"Bad arguments for tool '{name}': {e}")
        except Exception as e:  # never let one tool call kill the loop
            result = ToolResult(False, f"Tool '{name}' raised: {type(e).__name__}: {e}")
        self.last_results.append(result)
        return result

    def to_schemas(self) -> list[dict[str, Any]]:
        """Ollama/OpenAI-compatible tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]
