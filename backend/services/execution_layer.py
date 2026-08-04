"""
Secure Execution Layer.

Provides isolated subprocess execution for Python code with timeout protection.
Architected for future Docker sandbox replacement.
"""

import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils.logging import get_logger, log_execution_result


@dataclass
class ExecutionResult:
    """Result of code execution in isolated subprocess."""

    success: bool
    exit_code: int | None
    stdout: str
    stderr: str
    execution_time: float
    timeout_occurred: bool
    traceback: str | None


class ExecutionLayer:
    """
    Secure execution layer for running Python code in isolated subprocesses.

    This implementation uses subprocess isolation with timeout protection.
    Future iterations can replace this with Docker sandboxing for stronger isolation.
    """

    DEFAULT_TIMEOUT = 30.0  # seconds
    MAX_EXECUTION_TIME = 60.0  # seconds

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize the execution layer.

        Args:
            timeout: Default timeout for code execution in seconds.
        """
        self.timeout = min(timeout, self.MAX_EXECUTION_TIME)
        self.logger = get_logger("neurodebug.execution_layer")

    def execute_code(
        self,
        code: str,
        timeout: float | None = None,
        working_dir: str | None = None,
    ) -> ExecutionResult:
        """
        Execute Python code in an isolated subprocess.

        Args:
            code: Python code to execute.
            timeout: Override timeout for this execution. If None, uses instance default.
            working_dir: Optional working directory for execution.

        Returns:
            ExecutionResult with execution details.

        Raises:
            ValueError: If code is empty or timeout is invalid.
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        exec_timeout = timeout if timeout is not None else self.timeout
        if exec_timeout <= 0:
            raise ValueError("Timeout must be positive")

        start_time = time.time()
        stdout = ""
        stderr = ""
        exit_code = None
        timeout_occurred = False
        traceback = None

        # Create temporary file for code
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            # Execute in isolated subprocess
            result = subprocess.run(
                ["python", temp_file_path],
                capture_output=True,
                text=True,
                timeout=exec_timeout,
                cwd=working_dir,
            )

            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode

            # Extract traceback from stderr if present
            if stderr and "Traceback" in stderr:
                traceback = self._extract_traceback(stderr)

        except subprocess.TimeoutExpired:
            timeout_occurred = True
            exit_code = -1
            stderr = f"Execution timeout after {exec_timeout}s"
            traceback = None

        except Exception as exc:
            exit_code = -1
            stderr = f"Execution error: {exc}"
            traceback = str(exc)

        finally:
            # Clean up temporary file
            try:
                Path(temp_file_path).unlink()
            except Exception:
                pass

        execution_time = time.time() - start_time
        success = exit_code == 0 and not timeout_occurred

        # Log execution result
        log_execution_result(
            self.logger,
            execution_type="subprocess",
            success=success,
            exit_code=exit_code,
            execution_time=execution_time,
            timeout_occurred=timeout_occurred,
        )

        return ExecutionResult(
            success=success,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            execution_time=execution_time,
            timeout_occurred=timeout_occurred,
            traceback=traceback,
        )

    def _extract_traceback(self, stderr: str) -> str:
        """
        Extract the traceback portion from stderr.

        Args:
            stderr: Standard error output.

        Returns:
            Extracted traceback string or None if not found.
        """
        if "Traceback" not in stderr:
            return None

        lines = stderr.split("\n")
        traceback_lines = []
        in_traceback = False

        for line in lines:
            if line.startswith("Traceback"):
                in_traceback = True
            if in_traceback:
                traceback_lines.append(line)
                # Stop at the error type line (e.g., "NameError:")
                if line.strip() and not line.startswith(" ") and ":" in line:
                    # Continue to capture the error message
                    continue
                # Stop after we've captured the full traceback
                if in_traceback and line.strip() == "" and len(traceback_lines) > 1:
                    break

        return "\n".join(traceback_lines) if traceback_lines else None
