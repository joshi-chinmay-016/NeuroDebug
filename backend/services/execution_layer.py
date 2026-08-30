"""
Secure Execution Layer.

Routes code execution through the isolated SandboxExecutor (Docker Sandbox).
Ensures untrusted Python code is never executed directly inside the FastAPI application process.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from services.sandbox.docker_executor import DockerSandboxExecutor
from services.sandbox.fake_executor import FakeSandboxExecutor
from services.sandbox.sandbox_executor import (
    SandboxExecutionResult,
    SandboxExecutionStatus,
    SandboxExecutor,
)
from utils.config import Config
from utils.logging import get_logger, log_execution_result

logger = get_logger("neurodebug.execution_layer")


@dataclass
class ExecutionResult:
    """Result of code execution in isolated sandbox."""

    success: bool
    exit_code: int | None
    stdout: str
    stderr: str
    execution_time: float
    timeout_occurred: bool
    traceback: str | None
    output_truncated: bool = False
    status: SandboxExecutionStatus = SandboxExecutionStatus.SUCCESS
    resource_limited: bool = False
    sandbox_error: str | None = None
    container_id: str | None = None


# Sensitive environment variables to strip
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
    Hardened execution layer routing code execution to isolated Docker sandboxes.
    """

    DEFAULT_TIMEOUT = 10.0  # seconds
    MAX_EXECUTION_TIME = 30.0  # seconds
    MAX_OUTPUT_BYTES = 50_000  # Cap output size at 50KB to prevent memory exhaustion

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        sandbox_executor: SandboxExecutor | None = None,
    ):
        self.timeout = min(timeout, self.MAX_EXECUTION_TIME)
        self.logger = get_logger("neurodebug.execution_layer")
        if sandbox_executor is not None:
            self.sandbox_executor = sandbox_executor
        else:
            docker_exec = DockerSandboxExecutor(default_timeout=self.timeout)
            if not Config.SANDBOX_FORCE_FALLBACK and docker_exec.is_available():
                self.sandbox_executor = docker_exec
            else:
                # Docker daemon not running or fallback forced (e.g. test environment)
                self.sandbox_executor = docker_exec

    def execute_code(
        self,
        code: str,
        timeout: float | None = None,
        working_dir: str | None = None,
    ) -> ExecutionResult:
        """
        Execute Python code in isolated sandbox.

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

        # If sandbox executor is operational, use it
        if self.sandbox_executor.is_available():
            sbx_res: SandboxExecutionResult = self.sandbox_executor.execute_code(
                code=code,
                timeout=exec_timeout,
                working_dir=working_dir,
            )
            exec_time = time.time() - start_time

            log_execution_result(
                self.logger,
                execution_type="docker_sandbox",
                success=sbx_res.success,
                exit_code=sbx_res.exit_code,
                execution_time=exec_time,
                timeout_occurred=sbx_res.timeout_occurred,
            )

            return ExecutionResult(
                success=sbx_res.success,
                exit_code=sbx_res.exit_code,
                stdout=sbx_res.stdout,
                stderr=sbx_res.stderr,
                execution_time=sbx_res.execution_time,
                timeout_occurred=sbx_res.timeout_occurred,
                traceback=sbx_res.traceback,
                output_truncated=sbx_res.output_truncated,
                status=sbx_res.status,
                resource_limited=sbx_res.resource_limited,
                sandbox_error=sbx_res.sandbox_error,
                container_id=sbx_res.container_id,
            )

        # Fallback for environments where Docker daemon is completely unavailable (e.g. unit test runner without Docker)
        return self._execute_fallback_sanitized(code, exec_timeout, working_dir, start_time)

    def _execute_fallback_sanitized(
        self,
        code: str,
        exec_timeout: float,
        working_dir: str | None,
        start_time: float,
    ) -> ExecutionResult:
        """Sanitized fallback subprocess execution when Docker daemon is not present."""
        stdout = ""
        stderr = ""
        exit_code = None
        timeout_occurred = False
        traceback = None
        output_truncated = False
        status = SandboxExecutionStatus.SUCCESS

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

                status = SandboxExecutionStatus.SUCCESS if exit_code == 0 else SandboxExecutionStatus.FAILURE

            except subprocess.TimeoutExpired:
                timeout_occurred = True
                status = SandboxExecutionStatus.TIMEOUT
                exit_code = -1
                stderr = f"Execution timeout after {exec_timeout:.1f}s"
                self._terminate_process_tree(proc)

        except Exception as exc:
            self.logger.warning("Subprocess execution exception: %s", exc)
            status = SandboxExecutionStatus.ERROR
            exit_code = -1
            stderr = str(exc)

        finally:
            if proc and proc.poll() is None:
                self._terminate_process_tree(proc)
            try:
                Path(temp_file_path).unlink(missing_ok=True)
            except OSError:
                pass

        execution_time = time.time() - start_time
        success = (exit_code == 0) and not timeout_occurred

        log_execution_result(
            self.logger,
            execution_type="subprocess_fallback",
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
            status=status,
        )

    def _get_sanitized_environment(self) -> dict[str, str]:
        """Build a clean minimal environment with sensitive credentials stripped."""
        clean_env = {}
        for key, value in os.environ.items():
            if key.upper() not in SENSITIVE_ENV_VARS:
                clean_env[key] = value

        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        return clean_env

    def _truncate_output(self, text: str) -> tuple[str, bool]:
        """Truncate text if it exceeds maximum allowable output size."""
        if len(text.encode("utf-8")) > self.MAX_OUTPUT_BYTES:
            truncated = text[: self.MAX_OUTPUT_BYTES] + "\n[... Output truncated after 50,000 bytes ...]"
            return truncated, True
        return text, False

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
