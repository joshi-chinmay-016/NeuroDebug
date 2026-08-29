"""
Test Runner Service.

Executes pytest test cases and records results.
"""

import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


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


class PytestRunner:
    """
    Executes pytest test cases and records detailed results.

    Uses subprocess isolation for safe test execution.
    """

    DEFAULT_TIMEOUT = 30.0  # seconds

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize the test runner.

        Args:
            timeout: Default timeout for test execution in seconds.
        """
        self.timeout = timeout

    def run_tests(
        self,
        code: str,
        test_code: str,
        timeout: float | None = None,
    ) -> TestSuiteResultData:
        """
        Execute pytest tests for the given code.

        Args:
            code: The original Python code to test.
            test_code: The pytest test code.
            timeout: Override timeout for this execution.

        Returns:
            TestSuiteResultData with detailed test execution results.
        """
        exec_timeout = timeout if timeout is not None else self.timeout

        start_time = time.time()
        test_results = []
        output = ""
        error = None

        # Create temporary directory for test execution
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write code file
            code_file = temp_path / "code_under_test.py"
            code_file.write_text(code, encoding="utf-8")

            # Write test file
            test_file = temp_path / "test_code.py"
            test_file.write_text(test_code, encoding="utf-8")

            try:
                # Run pytest with verbose output for detailed results
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        str(test_file),
                        "-v",
                        "--tb=short",
                        "--no-header",
                        "-rN",  # Disable summary for custom parsing
                    ],
                    capture_output=True,
                    text=True,
                    timeout=exec_timeout,
                    cwd=temp_dir,
                    check=False,
                )

                output = result.stdout + result.stderr
                test_results = self._parse_pytest_output(output)

                if result.returncode not in [0, 1]:  # 0=all passed, 1=some failed
                    error = f"pytest exited with code {result.returncode}"

            except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
                error = f"Test execution timeout after {exec_timeout}s"
                output = error

        duration = time.time() - start_time

        # Calculate summary
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
        )

    def _parse_pytest_output(self, output: str) -> list[TestResultData]:
        """
        Parse pytest verbose output to extract individual test results.

        Args:
            output: Raw pytest output.

        Returns:
            List of TestResultData objects.
        """
        test_results = []
        lines = output.split("\n")

        for line in lines:
            line = line.strip()

            # Parse test lines like: test_add_positive_numbers PASSED
            if line and not line.startswith("=") and not line.startswith("test_"):
                continue

            # Match test result patterns
            if "::" in line or line.startswith("test_"):
                parts = line.split()
                if len(parts) >= 2:
                    test_name = (
                        parts[0].split("::")[-1] if "::" in parts[0] else parts[0]
                    )
                    status = parts[-1].upper()

                    passed = status == "PASSED"
                    failed = status == "FAILED"
                    skipped = status == "SKIPPED" or status == "XFAIL"

                    # Extract duration if available
                    duration = 0.0
                    for part in parts:
                        if part.endswith("s") and part.replace(".", "", 1).isdigit():
                            try:
                                duration = float(part.rstrip("s"))
                            except ValueError:
                                pass

                    error_message = None
                    if failed:
                        # Try to extract error from next lines
                        error_message = "Test failed"

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
