"""
Sandbox Execution Subsystem Abstraction.

Defines the core interface, result contracts, and exception hierarchy
for isolated sandboxed code and test execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class SandboxExecutionStatus(str, Enum):
    """Execution status for sandbox workloads."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"


class SandboxError(Exception):
    """Base class for all sandbox execution exceptions."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SandboxConfigurationError(SandboxError):
    """Raised when sandbox configuration or runtime environment is invalid."""


class SandboxStartupError(SandboxError):
    """Raised when sandbox container initialization or startup fails."""


class SandboxTimeoutError(SandboxError):
    """Raised when a sandboxed execution exceeds its hard deadline."""


class SandboxExecutionError(SandboxError):
    """Raised when unexpected errors occur during containerized execution."""


class SandboxResourceLimitError(SandboxError):
    """Raised when a workload violates configured memory, CPU, or PID limits."""


class SandboxCleanupError(SandboxError):
    """Raised when post-execution teardown or workspace purge fails."""


@dataclass
class SandboxExecutionResult:
    """Structured result of isolated code execution in the sandbox."""

    success: bool
    status: SandboxExecutionStatus
    exit_code: int | None
    stdout: str
    stderr: str
    execution_time: float
    timeout_occurred: bool = False
    traceback: str | None = None
    output_truncated: bool = False
    resource_limited: bool = False
    resource_reason: str | None = None
    sandbox_error: str | None = None
    container_id: str | None = None


@dataclass
class SandboxTestResult:
    """Individual test case result from sandboxed pytest execution."""

    test_name: str
    passed: bool
    failed: bool
    skipped: bool
    duration: float
    error_message: str | None = None


@dataclass
class SandboxTestSuiteResult:
    """Aggregate result of a complete sandboxed pytest suite."""

    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    test_results: list[SandboxTestResult] = field(default_factory=list)
    output: str = ""
    error: str | None = None
    timeout_occurred: bool = False
    output_truncated: bool = False
    sandbox_error: str | None = None


class SandboxExecutor(ABC):
    """
    Abstract interface for executing untrusted workloads inside an isolated sandbox.

    All untrusted Python execution must pass through this contract.
    Implementations must enforce strict containment, bounded timeouts,
    output size restrictions, and deterministic cleanup.
    """

    @abstractmethod
    def execute_code(
        self,
        code: str,
        timeout: float | None = None,
        working_dir: str | None = None,
    ) -> SandboxExecutionResult:
        """
        Execute raw Python code in an isolated sandbox container.

        Args:
            code: Python code string to execute.
            timeout: Optional execution timeout in seconds.
            working_dir: Optional working directory override.

        Returns:
            SandboxExecutionResult detailing the execution outcome.
        """
        pass

    @abstractmethod
    def execute_pytest(
        self,
        code: str,
        test_code: str,
        timeout: float | None = None,
    ) -> SandboxTestSuiteResult:
        """
        Execute pytest test suite against target Python code in an isolated sandbox.

        Args:
            code: The Python code under test.
            test_code: The pytest test suite code.
            timeout: Optional execution timeout in seconds.

        Returns:
            SandboxTestSuiteResult with test pass/fail breakdown and logs.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check whether the underlying sandbox runtime environment is available.

        Returns:
            True if the sandbox backend is operational, False otherwise.
        """
        pass
