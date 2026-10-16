import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


from testgen.tools.base import ToolRegistry
from testgen.tools.coverage import CoverageTool
from testgen.tools.source_analysis import AnalyzeSourceTool
from testgen.tools.test_runner import RunTestsTool
from testgen.tools.test_writer import WriteTestTool

FIXTURES = Path(__file__).parent / "fixtures"


def test_analyze_ast_extracts_metadata():
    tool = AnalyzeSourceTool()
    result = tool.execute(str(FIXTURES / "circle_area.py"))
    assert result.ok
    fn = result.data["functions"][0]
    assert fn["name"] == "circle_area"
    assert fn["params"][0]["name"] == "radius"
    assert fn["params"][0]["annotation"] == "float"
    assert "ValueError" in fn["raises"]


def test_write_test_accepts_fenced_code(tmp_path):
    tool = WriteTestTool(tmp_path, "add_test.py")
    result = tool.execute(content="```python\nimport unittest\n\nX = 1\n```")
    assert result.ok and result.data["syntax_ok"]

def test_write_test_rejects_syntax_errors(tmp_path):
    tool = WriteTestTool(tmp_path, "add_test.py")
    result = tool.execute(content="def broken(:\n  pass")
    assert not result.ok and result.ok is False


def test_write_test_sandbox_containment(tmp_path):
    tool = WriteTestTool(tmp_path, "legit_test.py")
    result = tool.execute(content="x = 1", filename="..\\evil.py")
    assert result.ok
    # Basename-only policy: the file must land inside the sandbox.
    assert Path(result.data["path"]).parent == tmp_path.resolve()


def test_run_tests_on_passing_file(tmp_path):
    (tmp_path / "add.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "add_test.py").write_text(
        "import unittest\nfrom add import add\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_sums(self):\n"
        "        self.assertEqual(add(2, 3), 5)\n",
        encoding="utf-8",
    )
    tool = RunTestsTool(tmp_path)
    result = tool.execute(str(tmp_path / "add_test.py"))
    assert result.ok is True
    assert result.data["all_passed"] and result.data["passed"] == 1 and result.data["failed"] == 0


def test_run_tests_reports_failures(tmp_path):
    (tmp_path / "add.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "add_test.py").write_text(
        "import unittest\nfrom add import add\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_wrong(self):\n"
        "        self.assertEqual(add(2, 3), 6)  # wrong expectation\n",
        encoding="utf-8",
    )
    tool = RunTestsTool(tmp_path)
    result = tool.execute(str(tmp_path / "add_test.py"))
    assert not result.ok
    assert result.data["failed"] == 1
    assert "test_wrong" in result.data["output_tail"]


def test_coverage_tool_reports_percent(tmp_path):
    (tmp_path / "add.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "add_test.py").write_text(
        "import unittest\nfrom add import add\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_sums(self):\n"
        "        self.assertEqual(add(2, 3), 5)\n",
        encoding="utf-8",
    )
    tool = CoverageTool(tmp_path / "add.py", tmp_path)
    result = tool.execute(str(tmp_path / "add_test.py"))
    assert result.ok
    assert result.data["percent"] == 100.0


def test_registry_survives_bad_tool_arguments():
    registry = ToolRegistry()
    registry.register(AnalyzeSourceTool())
    result = registry.execute("analyze_ast", {})  # missing required 'path'
    assert not result.ok
    assert "Missing required argument" in result.summary

    unknown = registry.execute("nope_tool", {})
    assert not unknown.ok and "Unknown tool" in unknown.summary
