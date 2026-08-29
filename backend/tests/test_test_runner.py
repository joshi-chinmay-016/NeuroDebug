"""Tests for the TestRunner service."""

from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch

from services.test_runner import PytestRunner


def test_run_tests_parses_successful_pytest_output():
    runner = PytestRunner(timeout=5.0)

    completed_process = CompletedProcess(
        args=["pytest"],
        returncode=0,
        stdout="test_add PASSED\n",
        stderr="",
    )

    with patch("services.test_runner.subprocess.run", return_value=completed_process):
        result = runner.run_tests(
            code="def add(a, b): return a + b",
            test_code="def test_add():\n    assert 1 == 1",
        )

    assert result.total_tests == 1
    assert result.passed == 1
    assert result.failed == 0
    assert result.error is None
    assert result.test_results[0].test_name == "test_add"


def test_run_tests_timeout_is_reported():
    runner = PytestRunner(timeout=5.0)

    with patch(
        "services.test_runner.subprocess.run",
        side_effect=TimeoutExpired(cmd=["pytest"], timeout=5.0),
    ):
        result = runner.run_tests(
            code="def add(a, b): return a + b",
            test_code="def test_add():\n    assert 1 == 1",
        )

    assert result.total_tests == 0
    assert result.failed == 0
    assert result.error == "Test execution timeout after 5.0s"
