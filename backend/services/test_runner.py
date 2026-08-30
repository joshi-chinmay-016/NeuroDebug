"""
Test Runner Service.

Executes pytest test cases in isolated Docker sandboxes and records detailed results.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from services.sandbox.docker_executor import DockerSandboxExecutor
from services.sandbox.sandbox_executor import (
    SandboxExecutor,
    SandboxTestSuiteResult,
)
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.test_runner")


@dataclass
class TestResultData:
    """Result of a single test execution."""

    test_name: str
    passed: bool
    failed: bool
    skipped: bool
    duration: float
    error_message: str | None


@dataclass
class TestSuiteResultData:
    """Result of a complete test suite execution."""

    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    test_results: list[TestResultData]
    output: str
    error: str | None
    timeout_occurred: bool = False
    output_truncated: bool = False
    sandbox_error: str | None = None


class PytestRunner:
    """
    Executes pytest test cases and records detailed results.

    Delegates test execution to DockerSandboxExecutor for secure containment.
    """

    DEFAULT_TIMEOUT = 30.0  # seconds

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        sandbox_executor: SandboxExecutor | None = None,
    ):
        """
        Initialize the test runner.

        Args:
            timeout: Default timeout for test execution in seconds.
            sandbox_executor: Optional custom SandboxExecutor instance.
        """
        self.timeout = timeout
        if sandbox_executor is not None:
            self.sandbox_executor = sandbox_executor
        else:
            docker_exec = DockerSandboxExecutor(default_timeout=self.timeout)
            self.sandbox_executor = docker_exec

    def run_tests(
        self,
        code: str,
        test_code: str,
        timeout: float | None = None,
    ) -> TestSuiteResultData:
        """
        Execute pytest tests for the given code in an isolated sandbox.

        Args:
            code: The original Python code to test.
            test_code: The pytest test code.
            timeout: Override timeout for this execution.

        Returns:
            TestSuiteResultData with detailed test execution results.
        """
        exec_timeout = timeout if timeout is not None else self.timeout

        # If sandbox executor is operational (or mocked), execute in sandbox
        if self.sandbox_executor.is_available():
            suite_res: SandboxTestSuiteResult = self.sandbox_executor.execute_pytest(
                code=code,
                test_code=test_code,
                timeout=exec_timeout,
            )

            converted_results = [
                TestResultData(
                    test_name=t.test_name,
                    passed=t.passed,
                    failed=t.failed,
                    skipped=t.skipped,
                    duration=t.duration,
                    error_message=t.error_message,
                )
                for t in suite_res.test_results
            ]

            return TestSuiteResultData(
                total_tests=suite_res.total_tests,
                passed=suite_res.passed,
                failed=suite_res.failed,
                skipped=suite_res.skipped,
                duration=suite_res.duration,
                test_results=converted_results,
                output=suite_res.output,
                error=suite_res.error,
                timeout_occurred=suite_res.timeout_occurred,
                output_truncated=suite_res.output_truncated,
                sandbox_error=suite_res.sandbox_error,
            )

        # Fallback for environments where Docker daemon is not running (e.g. host testing without Docker)
        return self._run_tests_fallback(code, test_code, exec_timeout)

    def _run_tests_fallback(
        self,
        code: str,
        test_code: str,
        exec_timeout: float,
    ) -> TestSuiteResultData:
        """Fallback local subprocess execution when Docker daemon is not present."""
        start_time = time.time()
        test_results = []
        output = ""
        error = None
        timeout_occurred = False

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            code_file = temp_path / "code_under_test.py"
            code_file.write_text(code, encoding="utf-8")

            test_file = temp_path / "test_code.py"
            test_file.write_text(test_code, encoding="utf-8")

            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        str(test_file),
                        "-v",
                        "--tb=short",
                        "--no-header",
                        "-rN",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=exec_timeout,
                    cwd=temp_dir,
                    check=False,
                )

                output = result.stdout + result.stderr
                test_results = self._parse_pytest_output(output)

                if result.returncode not in [0, 1]:
                    error = f"pytest exited with code {result.returncode}"

            except subprocess.TimeoutExpired:
                timeout_occurred = True
                error = f"Test execution timeout after {exec_timeout}s"
                output = error
            except (OSError, FileNotFoundError) as exc:
                error = f"Test execution failed: {exc}"
                output = error

        duration = time.time() - start_time
        passed = sum(1 for t in test_results if t.passed)
        failed = sum(1 for t in test_results if t.failed)
        skipped = sum(1 for t in test_results if t.skipped)

        return TestSuiteResultData(
            total_tests=len(test_results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            test_results=test_results,
            output=output,
            error=error,
            timeout_occurred=timeout_occurred,
        )

    def _parse_pytest_output(self, output: str) -> list[TestResultData]:
        """Parse pytest verbose output to extract individual test results."""
        test_results = []
        lines = output.split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("=") or line.startswith("_"):
                continue

            if "::" in line or line.startswith("test_"):
                parts = line.split()
                if len(parts) >= 2:
                    test_name = parts[0].split("::")[-1]
                    upper_parts = [p.upper() for p in parts]

                    passed = "PASSED" in upper_parts
                    failed = "FAILED" in upper_parts or "ERROR" in upper_parts
                    skipped = "SKIPPED" in upper_parts or "XFAIL" in upper_parts

                    if not (passed or failed or skipped):
                        continue

                    duration = 0.0
                    for part in parts:
                        if part.endswith("s") and part.replace(".", "", 1).isdigit():
                            try:
                                duration = float(part.rstrip("s"))
                            except ValueError:
                                pass

                    error_message = "Test failed" if failed else None

                    test_results.append(
                        TestResultData(
                            test_name=test_name,
                            passed=passed,
                            failed=failed,
                            skipped=skipped,
                            duration=duration,
                            error_message=error_message,
                        )
                    )

        return test_results
