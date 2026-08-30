"""
Fake/Mock Sandbox Executor for fast, reliable unit testing.
"""

from __future__ import annotations

from typing import Callable

from services.sandbox.sandbox_executor import (
    SandboxExecutionResult,
    SandboxExecutionStatus,
    SandboxExecutor,
    SandboxTestResult,
    SandboxTestSuiteResult,
)


class FakeSandboxExecutor(SandboxExecutor):
    """
    In-memory mock implementation of SandboxExecutor.

    Allows injecting custom results, simulating timeouts, errors,
    and capturing invocations during unit tests without requiring Docker.
    """

    def __init__(
        self,
        default_code_result: SandboxExecutionResult | None = None,
        default_pytest_result: SandboxTestSuiteResult | None = None,
        is_available_flag: bool = True,
    ):
        self.default_code_result = default_code_result
        self.default_pytest_result = default_pytest_result
        self._is_available = is_available_flag
        self.code_executions: list[dict] = []
        self.pytest_executions: list[dict] = []
        self.custom_code_handler: Callable[[str, float | None], SandboxExecutionResult] | None = None
        self.custom_pytest_handler: Callable[[str, str, float | None], SandboxTestSuiteResult] | None = None

    def execute_code(
        self,
        code: str,
        timeout: float | None = None,
        working_dir: str | None = None,
    ) -> SandboxExecutionResult:
        self.code_executions.append({
            "code": code,
            "timeout": timeout,
            "working_dir": working_dir,
        })

        if self.custom_code_handler:
            return self.custom_code_handler(code, timeout)

        if self.default_code_result:
            return self.default_code_result

        # Default fallback: simulate successful execution
        return SandboxExecutionResult(
            success=True,
            status=SandboxExecutionStatus.SUCCESS,
            exit_code=0,
            stdout="Output from FakeSandboxExecutor",
            stderr="",
            execution_time=0.01,
            timeout_occurred=False,
            container_id="fake-sandbox-container",
        )

    def execute_pytest(
        self,
        code: str,
        test_code: str,
        timeout: float | None = None,
    ) -> SandboxTestSuiteResult:
        self.pytest_executions.append({
            "code": code,
            "test_code": test_code,
            "timeout": timeout,
        })

        if self.custom_pytest_handler:
            return self.custom_pytest_handler(code, test_code, timeout)

        if self.default_pytest_result:
            return self.default_pytest_result

        # Default fallback: simulate passing test suite
        return SandboxTestSuiteResult(
            total_tests=1,
            passed=1,
            failed=0,
            skipped=0,
            duration=0.02,
            test_results=[
                SandboxTestResult(
                    test_name="test_fake_case",
                    passed=True,
                    failed=False,
                    skipped=False,
                    duration=0.01,
                )
            ],
            output="test_fake_case PASSED [100%]\n1 passed in 0.02s",
            error=None,
        )

    def is_available(self) -> bool:
        return self._is_available
