import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from testgen.validation.ast_validator import validate_input_file


def _write(tmp_path, code: str):
    target = tmp_path / "sample.py"
    target.write_text(code, encoding="utf-8")
    return str(target)


def test_valid_single_function(tmp_path):
    report = validate_input_file(_write(tmp_path, "import math\n\ndef f(x):\n    return x\n"))
    assert report.ok and not report.warnings


def test_missing_file_rejected():
    report = validate_input_file("definitely_missing_42.py")
    assert not report.ok and "not found" in report.errors[0].lower()


def test_syntax_error_rejected(tmp_path):
    report = validate_input_file(_write(tmp_path, "def broken(:\n    pass"))
    assert not report.ok and any("SyntaxError" in e for e in report.errors)


def test_no_functions_rejected(tmp_path):
    report = validate_input_file(_write(tmp_path, "print('hello')"))
    assert not report.ok and "no top-level functions" in report.errors[0].lower()


def test_multiple_functions_ok_with_warning(tmp_path):
    report = validate_input_file(
        _write(tmp_path, "def f(x):\n    return x\n\ndef g(y):\n    return y\n")
    )
    assert report.ok
    assert report.warnings and "multiple functions" in report.warnings[0].lower()
