"""
Unit tests for Sandbox Executor abstraction and FakeSandboxExecutor.
"""

import pytest

from services.sandbox import (
    FakeSandboxExecutor,
    SandboxExecutionResult,
    SandboxExecutionStatus,
    SandboxExecutor,
    SandboxTestResult,
    SandboxTestSuiteResult,
    SandboxTimeoutError,
)


def test_sandbox_executor_is_abstract():
    """Verify SandboxExecutor cannot be instantiated directly."""
    with pytest.raises(TypeError):
        SandboxExecutor()  # type: ignore


def test_fake_sandbox_executor_default_code_execution():
    """Test fake executor default code execution."""
    executor = FakeSandboxExecutor()
    assert executor.is_available() is True

    result = executor.execute_code("print('hello')")
    assert isinstance(result, SandboxExecutionResult)
    assert result.success is True
    assert result.status == SandboxExecutionStatus.SUCCESS
    assert result.exit_code == 0
    assert "Output from FakeSandboxExecutor" in result.stdout
    assert len(executor.code_executions) == 1
    assert executor.code_executions[0]["code"] == "print('hello')"


def test_fake_sandbox_executor_default_pytest_execution():
    """Test fake executor default pytest suite execution."""
    executor = FakeSandboxExecutor()
    suite = executor.execute_pytest("def f(): return 1", "def test_f(): assert f() == 1")
    assert isinstance(suite, SandboxTestSuiteResult)
    assert suite.total_tests == 1
    assert suite.passed == 1
    assert suite.failed == 0
    assert len(suite.test_results) == 1
    assert suite.test_results[0].passed is True
    assert len(executor.pytest_executions) == 1


def test_fake_sandbox_executor_custom_handlers():
    """Test fake executor with custom handler hooks."""
    executor = FakeSandboxExecutor()

    def custom_code(code: str, timeout: float | None) -> SandboxExecutionResult:
        if "timeout" in code:
            return SandboxExecutionResult(
                success=False,
                status=SandboxExecutionStatus.TIMEOUT,
                exit_code=-1,
                stdout="",
                stderr="Timeout",
                execution_time=10.0,
                timeout_occurred=True,
            )
        return SandboxExecutionResult(
            success=True,
            status=SandboxExecutionStatus.SUCCESS,
            exit_code=0,
            stdout="Custom stdout",
            stderr="",
            execution_time=0.05,
        )

    executor.custom_code_handler = custom_code

    ok_res = executor.execute_code("x = 1")
    assert ok_res.success is True
    assert ok_res.stdout == "Custom stdout"

    to_res = executor.execute_code("trigger timeout")
    assert to_res.timeout_occurred is True
    assert to_res.status == SandboxExecutionStatus.TIMEOUT


def test_sandbox_custom_exceptions():
    """Verify sandbox exceptions have message and details."""
    err = SandboxTimeoutError("Execution exceeded 10s", details={"timeout": 10.0})
    assert err.message == "Execution exceeded 10s"
    assert err.details["timeout"] == 10.0
    assert str(err) == "Execution exceeded 10s"
