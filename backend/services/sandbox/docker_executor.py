"""
Hardened Docker Sandbox Executor.

Executes untrusted user code and generated pytest suites in ephemeral,
resource-constrained, network-isolated Docker containers.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from services.sandbox.sandbox_executor import (
    SandboxExecutionResult,
    SandboxExecutionStatus,
    SandboxExecutor,
    SandboxStartupError,
    SandboxTestResult,
    SandboxTestSuiteResult,
)
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.sandbox.docker")


class DockerSandboxExecutor(SandboxExecutor):
    """
    Executes Python workloads in ephemeral, hardened Docker containers.

    Security Isolation Controls:
    - Container per job with auto-removal (--rm)
    - Zero network access (--network none)
    - Read-only root filesystem (--read-only)
    - Dedicated tmpfs for safe temporary writes (/tmp:rw,noexec,nosuid)
    - Dropped all Linux capabilities (--cap-drop ALL)
    - Privilege escalation prevention (no-new-privileges:true)
    - Unprivileged non-root execution (UID 10001:10001)
    - Hard PID / process count limit (--pids-limit 64)
    - Strict memory boundary (--memory 256m --memory-swap 256m)
    - Strict CPU boundary (--cpus 1.0)
    - Bounded stdout/stderr streaming (50KB cap)
    - Guaranteed container termination and workspace purge on timeouts/errors
    """

    def __init__(
        self,
        image_name: str | None = None,
        default_timeout: float | None = None,
        max_timeout: float | None = None,
        memory_limit: str | None = None,
        cpu_limit: str | None = None,
        pids_limit: int | None = None,
        max_output_bytes: int | None = None,
        tmpfs_size: str | None = None,
        user: str | None = None,
    ):
        self.image_name = image_name or Config.SANDBOX_IMAGE
        self.default_timeout = default_timeout or Config.SANDBOX_TIMEOUT_SECONDS
        self.max_timeout = max_timeout or Config.SANDBOX_MAX_TIMEOUT_SECONDS
        self.memory_limit = memory_limit or Config.SANDBOX_MEMORY_LIMIT
        self.cpu_limit = cpu_limit or Config.SANDBOX_CPU_LIMIT
        self.pids_limit = pids_limit or Config.SANDBOX_PIDS_LIMIT
        self.max_output_bytes = max_output_bytes or Config.SANDBOX_MAX_OUTPUT_BYTES
        self.tmpfs_size = tmpfs_size or Config.SANDBOX_TMPFS_SIZE
        self.user = user or Config.SANDBOX_USER

    _cached_available: bool | None = None

    def is_available(self) -> bool:
        """Check if Docker daemon is operational and required sandbox image exists."""
        if Config.SANDBOX_FORCE_FALLBACK:
            return False
        if DockerSandboxExecutor._cached_available is not None:
            return DockerSandboxExecutor._cached_available
        try:
            res = subprocess.run(
                ["docker", "ps", "-q"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=1.5,
                check=False,
            )
            if res.returncode != 0:
                DockerSandboxExecutor._cached_available = False
                return False
            err_lower = (res.stderr or "").lower()
            if any(p in err_lower for p in ("error", "cannot connect", "failed to connect", "is not running")):
                DockerSandboxExecutor._cached_available = False
                return False

            # Verify that the configured sandbox image is present locally
            img_res = subprocess.run(
                ["docker", "image", "inspect", self.image_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1.5,
                check=False,
            )
            is_ok = (img_res.returncode == 0)
            DockerSandboxExecutor._cached_available = is_ok
            return is_ok
        except Exception:
            DockerSandboxExecutor._cached_available = False
            return False

    @classmethod
    def reset_availability_cache(cls) -> None:
        """Reset the cached daemon availability state (used by unit tests)."""
        cls._cached_available = None

    def _truncate_output(self, text: str) -> tuple[str, bool]:
        """Truncate text if it exceeds maximum allowable output size."""
        encoded = text.encode("utf-8")
        if len(encoded) > self.max_output_bytes:
            truncated = text[: self.max_output_bytes] + f"\n[... Output truncated after {self.max_output_bytes} bytes ...]"
            return truncated, True
        return text, False

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

    def _build_docker_run_command(
        self,
        container_name: str,
        workspace_host_path: str,
        entrypoint_args: list[str],
    ) -> list[str]:
        """Construct the hardened docker run command with full security constraints."""
        # Convert path to absolute POSIX format for Docker volume mount
        host_posix_path = Path(workspace_host_path).resolve().as_posix()

        cmd = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            f"/tmp:rw,noexec,nosuid,size={self.tmpfs_size}",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--user",
            self.user,
            "--pids-limit",
            str(self.pids_limit),
            "--memory",
            self.memory_limit,
            "--memory-swap",
            self.memory_limit,
            "--cpus",
            str(self.cpu_limit),
            "-v",
            f"{host_posix_path}:/workspace:ro",
            "-w",
            "/workspace",
            "-e",
            "PYTHONUNBUFFERED=1",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            "-e",
            "PYTHONPATH=/workspace",
            "-e",
            "TMPDIR=/tmp",
            self.image_name,
        ]
        cmd.extend(entrypoint_args)
        return cmd

    def _cleanup_container(self, container_name: str) -> None:
        """Forcefully terminate and remove any container with the given name."""
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5.0,
                check=False,
            )
        except Exception as exc:
            logger.debug("Container cleanup exception (non-fatal): %s", exc)

    def execute_code(
        self,
        code: str,
        timeout: float | None = None,
        working_dir: str | None = None,
    ) -> SandboxExecutionResult:
        """
        Execute raw Python code inside an ephemeral Docker sandbox container.
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        exec_timeout = timeout if timeout is not None else self.default_timeout
        if exec_timeout <= 0:
            raise ValueError("Timeout must be positive")
        exec_timeout = min(exec_timeout, self.max_timeout)

        job_id = uuid.uuid4().hex[:12]
        container_name = f"neurodebug-sbx-{job_id}"
        temp_dir = tempfile.mkdtemp(prefix="neurodebug_sbx_")

        start_time = time.time()
        stdout = ""
        stderr = ""
        exit_code = None
        timeout_occurred = False
        traceback = None
        output_truncated = False
        sandbox_error = None
        status = SandboxExecutionStatus.SUCCESS

        proc = None
        try:
            # Write code to isolated workspace
            code_file = Path(temp_dir) / "main.py"
            code_file.write_text(code, encoding="utf-8")

            # Build Docker command
            docker_cmd = self._build_docker_run_command(
                container_name=container_name,
                workspace_host_path=temp_dir,
                entrypoint_args=["/workspace/main.py"],
            )

            proc = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                raw_stdout, raw_stderr = proc.communicate(timeout=exec_timeout)
                exit_code = proc.returncode

                stdout, trunc_out = self._truncate_output(raw_stdout or "")
                stderr, trunc_err = self._truncate_output(raw_stderr or "")
                output_truncated = trunc_out or trunc_err

                if stderr and "Traceback" in stderr:
                    traceback = self._extract_traceback(stderr)

                if exit_code == 0:
                    status = SandboxExecutionStatus.SUCCESS
                elif exit_code == 137:
                    # 137 typically means killed by OOM killer or SIGKILL
                    status = SandboxExecutionStatus.RESOURCE_LIMIT
                    stderr += "\n[Sandbox Error: Process exceeded resource boundaries or was terminated by OOM killer (Exit 137)]"
                else:
                    status = SandboxExecutionStatus.FAILURE

            except subprocess.TimeoutExpired:
                timeout_occurred = True
                status = SandboxExecutionStatus.TIMEOUT
                exit_code = -1
                stderr = f"Execution timeout exceeded after {exec_timeout:.1f}s"
                self._cleanup_container(container_name)

        except FileNotFoundError as exc:
            # Docker binary not installed / found
            logger.error("Docker binary not found: %s", exc)
            sandbox_error = f"Docker CLI unavailable: {exc}"
            status = SandboxExecutionStatus.ERROR
            exit_code = -1
        except Exception as exc:
            logger.error("Docker sandbox execution exception: %s", exc)
            sandbox_error = f"Sandbox execution failure: {exc}"
            status = SandboxExecutionStatus.ERROR
            exit_code = -1
            stderr = str(exc)

        finally:
            if proc and proc.poll() is None:
                self._cleanup_container(container_name)
            shutil.rmtree(temp_dir, ignore_errors=True)

        execution_time = time.time() - start_time
        success = (status == SandboxExecutionStatus.SUCCESS) and not timeout_occurred

        return SandboxExecutionResult(
            success=success,
            status=status,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            execution_time=execution_time,
            timeout_occurred=timeout_occurred,
            traceback=traceback,
            output_truncated=output_truncated,
            resource_limited=(status == SandboxExecutionStatus.RESOURCE_LIMIT),
            resource_reason="OOM or memory limit exceeded" if status == SandboxExecutionStatus.RESOURCE_LIMIT else None,
            sandbox_error=sandbox_error,
            container_id=container_name,
        )

    def execute_pytest(
        self,
        code: str,
        test_code: str,
        timeout: float | None = None,
    ) -> SandboxTestSuiteResult:
        """
        Execute pytest test suite against target Python code inside Docker sandbox.
        """
        exec_timeout = timeout if timeout is not None else self.default_timeout
        if exec_timeout <= 0:
            raise ValueError("Timeout must be positive")
        exec_timeout = min(exec_timeout, self.max_timeout)

        job_id = uuid.uuid4().hex[:12]
        container_name = f"neurodebug-sbx-test-{job_id}"
        temp_dir = tempfile.mkdtemp(prefix="neurodebug_sbx_test_")

        start_time = time.time()
        test_results: list[SandboxTestResult] = []
        output = ""
        error = None
        timeout_occurred = False
        output_truncated = False
        sandbox_error = None

        proc = None
        try:
            # Write target code and test files
            code_file = Path(temp_dir) / "code_under_test.py"
            code_file.write_text(code, encoding="utf-8")

            test_file = Path(temp_dir) / "test_code.py"
            test_file.write_text(test_code, encoding="utf-8")

            # Build Docker command to run pytest
            docker_cmd = self._build_docker_run_command(
                container_name=container_name,
                workspace_host_path=temp_dir,
                entrypoint_args=[
                    "-m",
                    "pytest",
                    "/workspace/test_code.py",
                    "-v",
                    "--tb=short",
                    "--no-header",
                    "-rN",
                ],
            )

            proc = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                raw_stdout, raw_stderr = proc.communicate(timeout=exec_timeout)
                combined = (raw_stdout or "") + ("\n" + raw_stderr if raw_stderr else "")
                output, output_truncated = self._truncate_output(combined)
                test_results = self._parse_pytest_output(output)

                if proc.returncode not in (0, 1):  # 0=all passed, 1=some failed
                    if proc.returncode == 137:
                        error = "Sandbox resource boundary exceeded during test execution (Exit 137)"
                    else:
                        error = f"pytest exited with code {proc.returncode}"

            except subprocess.TimeoutExpired:
                timeout_occurred = True
                error = f"Test execution timeout exceeded after {exec_timeout:.1f}s"
                output = error
                self._cleanup_container(container_name)

        except FileNotFoundError as exc:
            logger.error("Docker binary not found for pytest: %s", exc)
            sandbox_error = f"Docker CLI unavailable: {exc}"
            error = sandbox_error
        except Exception as exc:
            logger.error("Docker pytest execution exception: %s", exc)
            sandbox_error = f"Sandbox execution failure: {exc}"
            error = str(exc)

        finally:
            if proc and proc.poll() is None:
                self._cleanup_container(container_name)
            shutil.rmtree(temp_dir, ignore_errors=True)

        duration = time.time() - start_time
        passed = sum(1 for t in test_results if t.passed)
        failed = sum(1 for t in test_results if t.failed)
        skipped = sum(1 for t in test_results if t.skipped)

        return SandboxTestSuiteResult(
            total_tests=len(test_results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            test_results=test_results,
            output=output,
            error=error,
            timeout_occurred=timeout_occurred,
            output_truncated=output_truncated,
            sandbox_error=sandbox_error,
        )

    def _parse_pytest_output(self, output: str) -> list[SandboxTestResult]:
        """Parse pytest verbose output to extract individual test case results."""
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
                        SandboxTestResult(
                            test_name=test_name,
                            passed=passed,
                            failed=failed,
                            skipped=skipped,
                            duration=duration,
                            error_message=error_message,
                        )
                    )

        return test_results
