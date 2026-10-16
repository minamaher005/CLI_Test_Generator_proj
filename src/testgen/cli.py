"""TestGen CLI entry point.

Usage:
    testgen <file.py> [options]

The tool spawns an LLM agent that:
1. parses the file's AST to understand what to test,
2. writes a unittest file via a sandboxed tool,
3. runs pytest on it and reads failures,
4. repairs the tests it wrote until they pass,
5. measures line coverage and (optionally) iterates on it.

Use --provider mock for a fully offline, deterministic run (no API key needed).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from .agent.core import Agent
from .config import Config
from .llm.mock_provider import MockProvider
from .llm.ollama_provider import OllamaProvider
from .reporting.report import build_report, render, save_report
from .tools.base import ToolRegistry
from .tools.coverage import CoverageTool
from .tools.source_analysis import AnalyzeSourceTool
from .tools.test_runner import RunTestsTool
from .tools.test_writer import WriteTestTool
from .validation.ast_validator import validate_input_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="testgen",
        description="Agentic Python unittest generator - an LLM agent that writes, "
        "runs, and repairs tests until they pass.",
    )
    parser.add_argument("pythonfile", help="Path to the Python file to test")
    parser.add_argument(
        "--provider",
        choices=["ollama", "mock"],
        help="LLM provider (default: ollama; 'mock' runs fully offline)",
    )
    parser.add_argument("--model", help="Model name override")
    parser.add_argument("--max-iterations", type=int, help="Max agent iterations (default: 5)")
    parser.add_argument(
        "--coverage-threshold", type=float, help="Coverage percent target (default: 80)"
    )
    parser.add_argument("--no-coverage", action="store_true", help="Skip the coverage tool")
    parser.add_argument("--outdir", help="Sandbox output directory (default: .testgen)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full tool payloads")
    return parser


def make_provider(config: Config, source_path: Path):
    if config.provider == "mock":
        return MockProvider(source_path, config.output_dir, with_coverage=config.use_coverage)
    return OllamaProvider(config)


def build_tools(config: Config, source_path: Path) -> ToolRegistry:
    source_path = source_path.resolve()
    output_dir = Path(config.output_dir).resolve()
    default_test_name = f"{source_path.stem}_test.py"

    registry = ToolRegistry()
    registry.register(AnalyzeSourceTool())
    registry.register(WriteTestTool(output_dir, default_test_name))
    registry.register(RunTestsTool(source_path.parent))
    if config.use_coverage:
        registry.register(CoverageTool(source_path, output_dir))
    return registry


def main(argv: list[str] | None = None) -> int:
    console = Console()
    args = build_parser().parse_args(argv)

    config = Config.from_env()
    if args.provider:
        config.provider = args.provider
    if args.model:
        config.model = args.model
    if args.max_iterations is not None:
        config.max_iterations = args.max_iterations
    if args.coverage_threshold is not None:
        config.coverage_threshold = args.coverage_threshold
    if args.no_coverage:
        config.use_coverage = False
    if args.outdir:
        config.output_dir = Path(args.outdir)
    config.verbose = args.verbose or config.verbose

    source_path = Path(args.pythonfile)
    if not source_path.exists():
        console.print(f"[red]error:[/red] file not found: {source_path}")
        return 2
    if source_path.suffix.lower() != ".py":
        console.print("[red]error:[/red] input must be a .py file")
        return 2

    validation = validate_input_file(source_path)
    for warning in validation.warnings:
        console.print(f"[yellow]warning:[/yellow] {warning}")
    if not validation.ok:
        for error in validation.errors:
            console.print(f"[red]error:[/red] {error}")
        return 2

    if config.provider == "ollama":
        import os

        if not os.environ.get("OLLAMA_API_KEY"):
            console.print(
                "[yellow]warning:[/yellow] OLLAMA_API_KEY is not set; add it to .env, or "
                "run with --provider mock for a fully offline demo."
            )

    console.print(
        Panel(
            f"provider=[bold]{config.provider}[/bold] model=[bold]{config.model}[/bold] "
            f"max_iterations={config.max_iterations} coverage={'on' if config.use_coverage else 'off'}",
            title="TestGen",
            border_style="blue",
        )
    )

    registry = build_tools(config, source_path)
    agent = Agent(
        provider=make_provider(config, source_path),
        registry=registry,
        max_iterations=config.max_iterations,
        verbose=config.verbose,
        console=console,
    )

    try:
        result = agent.run(source_path.resolve())
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted.[/yellow]")
        return 130
    except Exception as e:
        console.print(f"[red]Agent crashed:[/red] {type(e).__name__}: {e}")
        if config.verbose:
            raise
        return 1

    report = build_report(source_path.resolve(), config, result)
    report_path = save_report(report, Path(config.output_dir))
    render(console, report)
    console.print(f"[dim]Report saved to {report_path}[/dim]")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
