"""
Docker Sandbox Integration Tests.

Validates end-to-end Python and pytest execution in live Docker sandbox containers.
Skips gracefully if Docker daemon is not operational or sandbox image is not built.
"""

import pytest

from services.sandbox.docker_executor import DockerSandboxExecutor
from services.sandbox.sandbox_executor import (
    SandboxExecutionStatus,
    SandboxTestSuiteResult,
)


@pytest.fixture
def docker_executor():
    """Create a DockerSandboxExecutor instance."""
    executor = DockerSandboxExecutor()
    if not executor.is_available():
        pytest.skip("Docker daemon is not operational or neurodebug-sandbox image is not available")
    return executor


def test_docker_sandbox_executes_valid_code(docker_executor):
    """Verify live Docker sandbox executes valid Python and returns stdout."""
    code = "print('Hello from Live Docker Sandbox!')"
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert result.status == SandboxExecutionStatus.SUCCESS
    assert result.exit_code == 0
    assert "Hello from Live Docker Sandbox!" in result.stdout
    assert result.timeout_occurred is False
    assert result.execution_time > 0
    assert result.container_id is not None


def test_docker_sandbox_handles_failing_code(docker_executor):
    """Verify live Docker sandbox catches exceptions and captures tracebacks."""
    code = "x = 1 / 0"
    result = docker_executor.execute_code(code)

    assert result.success is False
    assert result.status == SandboxExecutionStatus.FAILURE
    assert result.exit_code != 0
    assert "ZeroDivisionError" in result.stderr
    assert result.traceback is not None
    assert "division by zero" in result.traceback


def test_docker_sandbox_executes_pytest_suite(docker_executor):
    """Verify live Docker sandbox executes pytest suites and parses results."""
    code = """
def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError('Cannot divide by zero')
    return a / b
"""

    test_code = """
from code_under_test import multiply, divide
import pytest

def test_multiply():
    assert multiply(3, 4) == 12

def test_divide():
    assert divide(10, 2) == 5.0

def test_divide_zero():
    with pytest.raises(ValueError):
        divide(10, 0)

def test_failing_case():
    assert multiply(2, 2) == 5
"""

    suite: SandboxTestSuiteResult = docker_executor.execute_pytest(code, test_code)

    assert suite.total_tests == 4
    assert suite.passed == 3
    assert suite.failed == 1
    assert suite.skipped == 0
    assert suite.timeout_occurred is False
    assert len(suite.test_results) == 4

    passed_tests = [t.test_name for t in suite.test_results if t.passed]
    failed_tests = [t.test_name for t in suite.test_results if t.failed]

    assert "test_multiply" in passed_tests
    assert "test_divide" in passed_tests
    assert "test_divide_zero" in passed_tests
    assert "test_failing_case" in failed_tests


def test_docker_sandbox_timeout_terminates_container(docker_executor):
    """Verify live Docker sandbox terminates stuck workloads and kills container."""
    code = "import time\ntime.sleep(20)"
    result = docker_executor.execute_code(code, timeout=2.0)

    assert result.success is False
    assert result.status == SandboxExecutionStatus.TIMEOUT
    assert result.timeout_occurred is True
    assert "timeout" in result.stderr.lower()


def test_docker_sandbox_output_truncation(docker_executor):
    """Verify live Docker sandbox truncates excessive stdout."""
    code = "print('X' * 100000)"
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert result.output_truncated is True
    assert len(result.stdout.encode("utf-8")) <= docker_executor.max_output_bytes + 200
    assert "Output truncated" in result.stdout
