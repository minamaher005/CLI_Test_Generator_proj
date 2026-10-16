from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ..tools.base import ToolRegistry
from .prompts import SYSTEM_PROMPT
from .state import AgentState


@dataclass
class AgentResult:
    success: bool
    final_message: str
    iterations: int
    tool_trace: list[dict] = field(default_factory=list)
    last_test_run: dict | None = None
    coverage: dict | None = None


class ConsoleLike(Protocol):
    def print(self, text: str) -> None: ...


class Agent:
    """The observe -> think -> act loop. The LLM decides; tools do the work."""

    def __init__(
        self,
        provider,
        registry: ToolRegistry,
        max_iterations: int = 5,
        verbose: bool = False,
        console: ConsoleLike | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.console = console
        self.state = AgentState()

    # -- helpers -------------------------------------------------------

    def _user_task(self, source_path: Path, source_code: str) -> str:
        return (
            f"Generate a unittest file for the Python source file: {source_path.name}\n"
            f"(Path: {source_path})\n"
            "\n"
            "Source code:\n"
            "```python\n"
            f"{source_code}\n"
            "```\n"
            "Follow your workflow: analyze_ast -> write_test -> run_tests "
            "(-> get_coverage) until tests pass and coverage is good, then summarize."
        )

    def _say(self, text: str) -> None:
        if self.console is not None:
            self.console.print(text)

    def _verbose_say(self, text: str) -> None:
        if self.verbose:
            self._say(text)

    # -- the loop ------------------------------------------------------

    def run(self, source_path: Path) -> AgentResult:
        source_code = source_path.read_text(encoding="utf-8")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._user_task(source_path, source_code)},
        ]
        self.state.messages = messages
        schemas = self.registry.to_schemas()

        final_message = ""
        for _ in range(self.max_iterations):
            self.state.iterations += 1

            response = self.provider.chat(messages, tools=schemas)

            if not response.wants_tools:
                final_message = (response.content or "").strip() or "Agent finished."
                self._verbose_say("[agent] Final summary received.")
                break

            # Preserve the assistant's tool-call turn, then append each observation.
            assistant_turn = {
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {"function": {"name": call.name, "arguments": call.arguments}}
                    for call in response.tool_calls
                ],
            }
            messages.append(assistant_turn)

            for call in response.tool_calls:
                self._say(f"[iter {self.state.iterations}] -> tool: [bold]{call.name}[/bold]")
                result = self.registry.execute(call.name, call.arguments)
                status = "[green]ok[/green]" if result.ok else f"[red]fail[/red] - {result.summary}"
                self._say(f"[iter {self.state.iterations}]    {status}")
                self._verbose_say(
                    f"[iter {self.state.iterations}]    payload: {result.as_payload()[:800]}"
                )
                self.state.record_tool(
                    call.name, call.arguments, result.ok,
                    {"summary": result.summary, **result.data},
                )
                messages.append(
                    {"role": "tool", "name": call.name, "content": result.as_payload()}
                )
        else:
            final_message = (
                f"Iteration budget exhausted ({self.max_iterations} rounds) before the "
                "agent could conclude. Partial results are in the report."
            )

        last_run = self.state.last_result("run_tests", ok_only=False)
        coverage_entry = self.state.last_result("get_coverage", ok_only=False)
        all_passed = bool(last_run and last_run["data"].get("all_passed"))
        return AgentResult(
            success=all_passed,
            final_message=final_message,
            iterations=self.state.iterations,
            tool_trace=self.state.tool_trace,
            last_test_run=last_run,
            coverage=coverage_entry,
        )
