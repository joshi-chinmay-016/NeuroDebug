"""
Unit tests for Sandbox Executor abstraction, FakeSandboxExecutor, and DockerSandboxExecutor.
"""

from unittest.mock import MagicMock, patch
import subprocess
import pytest

from services.sandbox import (
    DockerSandboxExecutor,
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


# ──────────────────────────────────────────────────────────────────
# DockerSandboxExecutor Unit Tests (Mocked Docker CLI)
# ──────────────────────────────────────────────────────────────────


def test_docker_command_construction_security_flags():
    """Verify that DockerSandboxExecutor constructs commands with all required security controls."""
    executor = DockerSandboxExecutor(
        image_name="neurodebug-sandbox:latest",
        memory_limit="256m",
        cpu_limit="1.0",
        pids_limit=64,
        tmpfs_size="64m",
        user="10001:10001",
    )

    cmd = executor._build_docker_run_command(
        container_name="neurodebug-sbx-test1234",
        workspace_host_path="/tmp/fake_dir",
        entrypoint_args=["python3", "/workspace/main.py"],
    )

    assert cmd[0] == "docker"
    assert cmd[1] == "run"
    assert "--rm" in cmd
    assert "--name" in cmd and "neurodebug-sbx-test1234" in cmd
    assert "--network" in cmd and cmd[cmd.index("--network") + 1] == "none"
    assert "--read-only" in cmd
    assert "--cap-drop" in cmd and cmd[cmd.index("--cap-drop") + 1] == "ALL"
    assert "--security-opt" in cmd and cmd[cmd.index("--security-opt") + 1] == "no-new-privileges:true"
    assert "--user" in cmd and cmd[cmd.index("--user") + 1] == "10001:10001"
    assert "--pids-limit" in cmd and cmd[cmd.index("--pids-limit") + 1] == "64"
    assert "--memory" in cmd and cmd[cmd.index("--memory") + 1] == "256m"
    assert "--memory-swap" in cmd and cmd[cmd.index("--memory-swap") + 1] == "256m"
    assert "--cpus" in cmd and cmd[cmd.index("--cpus") + 1] == "1.0"
    assert "--tmpfs" in cmd and "/tmp:rw,noexec,nosuid,size=64m" in cmd[cmd.index("--tmpfs") + 1]
    assert "-w" in cmd and cmd[cmd.index("-w") + 1] == "/workspace"
    assert "neurodebug-sandbox:latest" in cmd


def test_docker_executor_code_success():
    """Test successful Python code execution in mocked Docker container."""
    executor = DockerSandboxExecutor()

    mock_proc = MagicMock()
    mock_proc.communicate.return_value = ("Hello Sandbox\n", "")
    mock_proc.returncode = 0
    mock_proc.poll.return_value = 0

    with patch("subprocess.Popen", return_value=mock_proc):
        res = executor.execute_code("print('Hello Sandbox')")

    assert res.success is True
    assert res.status == SandboxExecutionStatus.SUCCESS
    assert res.exit_code == 0
    assert res.stdout == "Hello Sandbox\n"
    assert res.timeout_occurred is False
    assert res.output_truncated is False


def test_docker_executor_code_timeout():
    """Test Docker timeout enforcement and container cleanup."""
    executor = DockerSandboxExecutor(default_timeout=5.0)

    mock_proc = MagicMock()
    mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="docker run ...", timeout=5.0)
    mock_proc.poll.return_value = None

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch.object(executor, "_cleanup_container") as mock_cleanup:
            res = executor.execute_code("import time; time.sleep(10)")

    assert res.success is False
    assert res.status == SandboxExecutionStatus.TIMEOUT
    assert res.timeout_occurred is True
    assert "timeout" in res.stderr.lower()
    assert mock_cleanup.called


def test_docker_executor_code_oom_killed():
    """Test Docker container OOM / exit code 137 resource limit handling."""
    executor = DockerSandboxExecutor()

    mock_proc = MagicMock()
    mock_proc.communicate.return_value = ("", "Killed\n")
    mock_proc.returncode = 137
    mock_proc.poll.return_value = 137

    with patch("subprocess.Popen", return_value=mock_proc):
        res = executor.execute_code("x = 'a' * 10**10")

    assert res.success is False
    assert res.status == SandboxExecutionStatus.RESOURCE_LIMIT
    assert res.resource_limited is True
    assert res.exit_code == 137
    assert "resource boundaries" in res.stderr


def test_docker_executor_output_truncation():
    """Test output truncation when stdout exceeds byte threshold."""
    executor = DockerSandboxExecutor(max_output_bytes=100)

    huge_output = "A" * 500
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = (huge_output, "")
    mock_proc.returncode = 0
    mock_proc.poll.return_value = 0

    with patch("subprocess.Popen", return_value=mock_proc):
        res = executor.execute_code("print('A' * 500)")

    assert res.output_truncated is True
    assert len(res.stdout) < 500
    assert "Output truncated after 100 bytes" in res.stdout


def test_docker_executor_pytest_execution():
    """Test pytest execution and output parsing in mocked Docker container."""
    executor = DockerSandboxExecutor()

    pytest_output = (
        "test_code.py::test_case_one PASSED [ 50%]\n"
        "test_code.py::test_case_two FAILED [100%]\n"
        "================ 1 failed, 1 passed in 0.12s ================\n"
    )

    mock_proc = MagicMock()
    mock_proc.communicate.return_value = (pytest_output, "")
    mock_proc.returncode = 1
    mock_proc.poll.return_value = 1

    with patch("subprocess.Popen", return_value=mock_proc):
        suite = executor.execute_pytest(
            code="def add(a, b): return a + b",
            test_code="def test_case_one(): assert add(1, 2) == 3\ndef test_case_two(): assert add(1, 2) == 4",
        )

    assert suite.total_tests == 2
    assert suite.passed == 1
    assert suite.failed == 1
    assert suite.skipped == 0
    assert len(suite.test_results) == 2
    assert suite.test_results[0].test_name == "test_case_one"
    assert suite.test_results[0].passed is True
    assert suite.test_results[1].test_name == "test_case_two"
    assert suite.test_results[1].failed is True
    assert suite.test_results[1].error_message == "Test failed"


def test_docker_executor_availability_check():
    """Test docker daemon availability check method."""
    executor = DockerSandboxExecutor()

    with patch("subprocess.run") as mock_run:
        DockerSandboxExecutor.reset_availability_cache()
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        assert executor.is_available() is True

        DockerSandboxExecutor.reset_availability_cache()
        mock_run.return_value = MagicMock(returncode=1, stderr="error connecting")
        assert executor.is_available() is False

        DockerSandboxExecutor.reset_availability_cache()
        mock_run.side_effect = Exception("Docker daemon offline")
        assert executor.is_available() is False
        DockerSandboxExecutor.reset_availability_cache()
