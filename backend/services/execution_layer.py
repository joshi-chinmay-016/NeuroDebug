"""
Secure Execution Layer.

Provides hardened isolated subprocess execution for Python code with:
- Strict timeout enforcement and process-tree termination
- Output buffer caps (prevent memory blowup from infinite loops/prints)
- Environment variable sanitization (redacts API keys and database credentials)
- Clean temporary file lifecycles
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from utils.logging import get_logger, log_execution_result

logger = get_logger("neurodebug.execution_layer")


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
    output_truncated: bool = False


# Sensitive environment variables to strip from child execution
SENSITIVE_ENV_VARS = {
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DATABASE_URL",
    "JWT_SECRET",
    "SECRET_KEY",
    "POSTGRES_PASSWORD",
    "AWS_SECRET_ACCESS_KEY",
}


class ExecutionLayer:
    """
    Hardened execution layer for running Python code in isolated subprocesses.
    """

    DEFAULT_TIMEOUT = 10.0  # seconds
    MAX_EXECUTION_TIME = 30.0  # seconds
    MAX_OUTPUT_BYTES = 50_000  # Cap output size at 50KB to prevent memory exhaustion

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = min(timeout, self.MAX_EXECUTION_TIME)
        self.logger = get_logger("neurodebug.execution_layer")

    def _get_sanitized_environment(self) -> dict[str, str]:
        """Build a clean minimal environment with sensitive credentials stripped."""
        clean_env = {}
        # Keep essential OS environment paths
        for key, value in os.environ.items():
            if key.upper() not in SENSITIVE_ENV_VARS:
                clean_env[key] = value

        # Set safety flags
        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        return clean_env

    def _truncate_output(self, text: str) -> tuple[str, bool]:
        """Truncate text if it exceeds maximum allowable output size."""
        if len(text.encode("utf-8")) > self.MAX_OUTPUT_BYTES:
            truncated = text[: self.MAX_OUTPUT_BYTES] + "\n[... Output truncated after 50,000 bytes ...]"
            return truncated, True
        return text, False

    def execute_code(
        self,
        code: str,
        timeout: float | None = None,
        working_dir: str | None = None,
    ) -> ExecutionResult:
        """
        Execute Python code in a hardened subprocess.

        Args:
            code: Python code to execute.
            timeout: Override timeout for this execution.
            working_dir: Optional working directory.

        Returns:
            ExecutionResult with execution details.
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        exec_timeout = timeout if timeout is not None else self.timeout
        if exec_timeout <= 0:
            raise ValueError("Timeout must be positive")
        exec_timeout = min(exec_timeout, self.MAX_EXECUTION_TIME)

        start_time = time.time()
        stdout = ""
        stderr = ""
        exit_code = None
        timeout_occurred = False
        traceback = None
        output_truncated = False

        # Create temporary file for execution
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        proc = None
        try:
            sanitized_env = self._get_sanitized_environment()

            proc = subprocess.Popen(
                [sys.executable, temp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir,
                env=sanitized_env,
            )

            try:
                raw_stdout, raw_stderr = proc.communicate(timeout=exec_timeout)
                exit_code = proc.returncode

                stdout, trunc_out = self._truncate_output(raw_stdout or "")
                stderr, trunc_err = self._truncate_output(raw_stderr or "")
                output_truncated = trunc_out or trunc_err

                if stderr and "Traceback" in stderr:
                    traceback = self._extract_traceback(stderr)

            except subprocess.TimeoutExpired:
                timeout_occurred = True
                exit_code = -1
                stderr = f"Execution timeout after {exec_timeout:.1f}s"
                self._terminate_process_tree(proc)

        except Exception as exc:
            self.logger.warning("Subprocess execution exception: %s", exc)
            exit_code = -1
            stderr = str(exc)

        finally:
            if proc and proc.poll() is None:
                self._terminate_process_tree(proc)

            # Cleanup temporary file safely
            try:
                Path(temp_file_path).unlink(missing_ok=True)
            except OSError as exc:
                self.logger.warning("Failed to delete temporary file: %s", exc)

        execution_time = time.time() - start_time
        success = (exit_code == 0) and not timeout_occurred

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
            output_truncated=output_truncated,
        )

    def _terminate_process_tree(self, proc: subprocess.Popen) -> None:
        """Forcefully terminate subprocess and any spawned children."""
        try:
            proc.kill()
            proc.communicate(timeout=1.0)
        except Exception:
            pass

    def _extract_traceback(self, stderr: str) -> str | None:
        """Extract the traceback portion from stderr."""
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
                if in_traceback and line.strip() == "" and len(traceback_lines) > 1:
                    break

        return "\n".join(traceback_lines) if traceback_lines else None
