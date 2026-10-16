from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def build_report(source: Path, config, result) -> dict:
    run = result.last_test_run or {}
    coverage = result.coverage or {}
    percent = (coverage.get("data", {}).get("percent") if coverage else None)
    threshold = float(config.coverage_threshold)

    report = {
        "source": str(source),
        "generated_test": None,
        "provider": getattr(config.provider, "name", config.provider),
        "model": config.model,
        "iterations": result.iterations,
        "success": result.success,
        "tests": {
            "passed": run.get("data", {}).get("passed"),
            "failed": run.get("data", {}).get("failed"),
            "errors": run.get("data", {}).get("errors"),
            "all_passed": result.success,
        },
        "coverage": {
            "percent": percent,
            "threshold": threshold,
            "meets_threshold": (percent is not None and percent >= threshold),
        },
        "final_message": result.final_message,
    }
    # The last write_test trace tells us where the test file landed.
    write_entry = next(
        (
            e
            for e in reversed(result.tool_trace)
            if e["tool"] == "write_test" and e["data"].get("path")
        ),
        None,
    )
    if write_entry:
        report["generated_test"] = write_entry["data"]["path"]
    return report


def save_report(report: dict, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "report.json"
    target.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return target


def render(console: Console, report: dict) -> None:
    status = "SUCCESS" if report["success"] else "INCOMPLETE"
    color = "green" if report["success"] else "yellow"
    console.print(
        Panel(
            f"[bold {color}]{status}[/bold {color}]\n"
            f"[dim]{report['final_message'][:400]}[/dim]",
            title="TestGen Agent",
            border_style=color,
        )
    )

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("Source", report["source"])
    table.add_row("Generated", str(report["generated_test"] or "-"))
    tests = report["tests"]
    table.add_row(
        "Tests",
        f"passed={tests.get('passed')} failed={tests.get('failed')} errors={tests.get('errors')}",
    )
    cov = report["coverage"]
    cov_str = f"{cov['percent']:.1f}%" if isinstance(cov.get("percent"), (int, float)) else "-"
    table.add_row("Coverage", f"{cov_str} (threshold: {cov['threshold']:.0f}%)")
    table.add_row("Loop", f"{report['iterations']} iteration(s) | {report['provider']} / {report['model']}")
    console.print(table)
