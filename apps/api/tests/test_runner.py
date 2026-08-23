import pytest

from app.modules.learning.internal.runner import SubprocessPythonRunner


@pytest.mark.asyncio
async def test_runner_valid_solution_passes() -> None:
    runner = SubprocessPythonRunner()
    student_code = """
def add(a, b):
    return a + b
"""
    tests_code = """
assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(0, 0) == 0
__tests_passed = 3
__tests_total = 3
"""
    result = await runner.run_submission(student_code, tests_code)
    assert result.status == "passed"
    assert result.tests_passed == 3
    assert result.tests_total == 3
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_runner_incorrect_solution_fails() -> None:
    runner = SubprocessPythonRunner()
    student_code = """
def add(a, b):
    return a * b  # Incorrect operation
"""
    tests_code = """
assert add(2, 3) == 5, "Expected add(2, 3) == 5"
"""
    result = await runner.run_submission(student_code, tests_code)
    assert result.status == "failed"
    assert "Expected add(2, 3) == 5" in result.stderr


@pytest.mark.asyncio
async def test_runner_infinite_loop_times_out() -> None:
    runner = SubprocessPythonRunner()
    student_code = """
while True:
    pass
"""
    tests_code = "assert True"
    result = await runner.run_submission(student_code, tests_code, timeout_seconds=1.0)
    assert result.status == "error"
    assert "timed out" in result.stderr.lower()


@pytest.mark.asyncio
async def test_runner_network_access_blocked() -> None:
    runner = SubprocessPythonRunner()
    student_code = """
import urllib.request
urllib.request.urlopen("https://example.com")
"""
    tests_code = "assert True"
    result = await runner.run_submission(student_code, tests_code)
    assert result.status == "error"
    assert "Security Violation" in result.stderr or "Network access is disabled" in result.stderr


@pytest.mark.asyncio
async def test_runner_syntax_error_handled() -> None:
    runner = SubprocessPythonRunner()
    student_code = "def invalid_syntax(:"
    tests_code = "assert True"
    result = await runner.run_submission(student_code, tests_code)
    assert result.status == "error"
    assert "SyntaxError" in result.stderr
