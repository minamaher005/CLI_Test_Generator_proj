"""End-to-end run of the full agent loop using the offline MockProvider."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from testgen.agent.core import Agent
from testgen.config import Config
from testgen.llm.mock_provider import MockProvider
from testgen.tools.base import ToolRegistry
from testgen.tools.coverage import CoverageTool
from testgen.tools.source_analysis import AnalyzeSourceTool
from testgen.tools.test_runner import RunTestsTool
from testgen.tools.test_writer import WriteTestTool

FIXTURES = Path(__file__).parent / "fixtures"


def _make_agent(source_path: Path, tmp_path: Path, use_coverage: bool = True):
    config = Config(provider="mock", max_iterations=8, output_dir=tmp_path / ".testgen")
    registry = ToolRegistry()
    registry.register(AnalyzeSourceTool())
    registry.register(WriteTestTool(Path(config.output_dir), f"{source_path.stem}_test.py"))
    registry.register(RunTestsTool(source_path.parent))
    if use_coverage:
        registry.register(CoverageTool(source_path, Path(config.output_dir)))
    provider = MockProvider(source_path, Path(config.output_dir), with_coverage=use_coverage)
    agent = Agent(provider, registry, max_iterations=config.max_iterations, console=Console())
    return config, agent


def test_agent_loop_generates_and_runs_tests(tmp_path):
    source = FIXTURES / "add.py"
    config, agent = _make_agent(source, tmp_path)

    result = agent.run(source.resolve())

    expected_test = tmp_path / ".testgen" / "add_test.py"
    assert expected_test.exists(), "agent should have written the test file"
    assert result.success, f"tests should pass; trace: {result.tool_trace}"
    assert "add" in expected_test.read_text(encoding="utf-8")
    assert result.iterations >= 4  # analyze -> write -> run -> coverage -> final
    assert result.coverage is not None


def test_agent_works_without_coverage_tool(tmp_path):
    source = FIXTURES / "add.py"
    config, agent = _make_agent(source, tmp_path, use_coverage=False)

    result = agent.run(source.resolve())
    assert result.success
    assert agent.state.last_result("get_coverage") is None
