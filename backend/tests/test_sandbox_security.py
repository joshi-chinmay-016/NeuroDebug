"""
Sandbox Security Test Suite.

Comprehensive adversarial test suite validating isolation boundaries:
1. Infinite loop containment & termination
2. Sleep beyond timeout termination
3. Network isolation: outbound HTTP requests blocked
4. Network isolation: localhost / internal services unreachable
5. Environment isolation: sensitive host variables & API keys not leaked
6. Filesystem isolation: host application files unreachable
7. Filesystem traversal: path traversal attempts blocked
8. Process limits: subprocess / fork bomb pattern containment
9. Memory limits: excessive memory allocation terminated safely
10. Bounded stdout: large output buffers truncated to prevent memory exhaustion
11. User identity: execution runs strictly as unprivileged non-root user (UID 10001)
12. Filesystem immutability: root filesystem is read-only
13. Docker socket: host Docker socket is not mounted or accessible
14. Malformed Python syntax error handling
15. Malicious pytest fixture / harness isolation
"""

import pytest

from services.sandbox.docker_executor import DockerSandboxExecutor
from services.sandbox.sandbox_executor import SandboxExecutionStatus


@pytest.fixture
def docker_executor():
    """Create a DockerSandboxExecutor instance."""
    executor = DockerSandboxExecutor()
    if not executor.is_available():
        pytest.skip("Docker daemon is not operational or neurodebug-sandbox image is not available")
    return executor


# 1. Infinite Loop
def test_security_infinite_loop(docker_executor):
    """Scenario 1: Infinite loop workload is terminated strictly at timeout deadline."""
    code = "while True:\n    pass"
    result = docker_executor.execute_code(code, timeout=2.0)

    assert result.success is False
    assert result.status == SandboxExecutionStatus.TIMEOUT
    assert result.timeout_occurred is True


# 2. Sleep Beyond Timeout
def test_security_sleep_beyond_timeout(docker_executor):
    """Scenario 2: Long sleep call is terminated strictly at timeout deadline."""
    code = "import time\ntime.sleep(60)"
    result = docker_executor.execute_code(code, timeout=2.0)

    assert result.success is False
    assert result.status == SandboxExecutionStatus.TIMEOUT
    assert result.timeout_occurred is True


# 3. Outbound Network Request
def test_security_network_disabled_http(docker_executor):
    """Scenario 3: Container has zero outbound network access (--network none)."""
    code = """
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1.0)
try:
    s.connect(("1.1.1.1", 80))
    print("NETWORK_ACCESSIBLE")
except Exception as e:
    print("NETWORK_BLOCKED:", type(e).__name__)
finally:
    s.close()
"""
    result = docker_executor.execute_code(code, timeout=5.0)

    assert result.success is True
    assert "NETWORK_BLOCKED" in result.stdout
    assert "NETWORK_ACCESSIBLE" not in result.stdout


# 4. Localhost / Internal Service Access
def test_security_network_disabled_localhost(docker_executor):
    """Scenario 4: Sandbox cannot connect to host database / postgres / redis on localhost."""
    code = """
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2.0)
try:
    s.connect(("127.0.0.1", 5432))
    print("LOCALHOST_ACCESSIBLE")
except Exception as e:
    print("LOCALHOST_BLOCKED:", type(e).__name__)
finally:
    s.close()
"""
    result = docker_executor.execute_code(code, timeout=5.0)

    assert result.success is True
    assert "LOCALHOST_BLOCKED" in result.stdout
    assert "LOCALHOST_ACCESSIBLE" not in result.stdout


# 5. Environment Secrets Isolation
def test_security_environment_secrets_sanitized(docker_executor, monkeypatch):
    """Scenario 5: Host credentials and sensitive environment variables are not passed through."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_secret_12345")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://secret_db_url")
    monkeypatch.setenv("JWT_SECRET", "super_secret_jwt_key")

    code = """
import os

sensitive_keys = ["GROQ_API_KEY", "DATABASE_URL", "JWT_SECRET", "SECRET_KEY", "POSTGRES_PASSWORD"]
leaked = [k for k in sensitive_keys if k in os.environ]
print("LEAKED_KEYS:", leaked)
"""
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert "LEAKED_KEYS: []" in result.stdout


# 6. Host Application Files Unreachable
def test_security_host_filesystem_unreachable(docker_executor):
    """Scenario 6: Application source tree, config, and .env files are unreachable."""
    code = """
import os
from pathlib import Path

suspicious_paths = [
    "/app/main.py",
    "/app/.env",
    "/backend/.env",
    "c:/NeuroDebug/.env",
    "c:/NeuroDebug/backend/main.py",
]

found = [p for p in suspicious_paths if Path(p).exists()]
print("HOST_FILES_FOUND:", found)
"""
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert "HOST_FILES_FOUND: []" in result.stdout


# 7. Parent Directory Traversal
def test_security_parent_directory_traversal(docker_executor):
    """Scenario 7: Traversal outside workspace does not expose host state."""
    code = """
from pathlib import Path

try:
    shadow = Path("/etc/shadow")
    print("SHADOW_EXISTS:", shadow.exists())
    if shadow.exists():
        content = shadow.read_text()
        print("SHADOW_READABLE: TRUE")
except Exception as e:
    print("SHADOW_ACCESS_ERROR:", type(e).__name__)
"""
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert "SHADOW_READABLE: TRUE" not in result.stdout


# 8. Unprivileged Non-Root User
def test_security_non_root_user(docker_executor):
    """Scenario 8: Process executes under unprivileged UID 10001 (not root UID 0)."""
    code = """
import os
print("UID:", os.getuid())
print("GID:", os.getgid())
"""
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert "UID: 10001" in result.stdout
    assert "GID: 10001" in result.stdout


# 9. Read-Only Root Filesystem
def test_security_read_only_root_filesystem(docker_executor):
    """Scenario 9: Container root filesystem is read-only (--read-only)."""
    code = """
try:
    with open("/malicious.txt", "w") as f:
        f.write("attack")
    print("ROOT_WRITABLE: TRUE")
except OSError as e:
    print("ROOT_READ_ONLY: TRUE", type(e).__name__)
"""
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert "ROOT_READ_ONLY: TRUE" in result.stdout
    assert "ROOT_WRITABLE: TRUE" not in result.stdout


# 10. Ephemeral tmpfs Workspace Isolation
def test_security_tmpfs_isolated(docker_executor):
    """Scenario 10: /tmp is writable for temporary operations via tmpfs."""
    code = """
with open("/tmp/temp_test.txt", "w") as f:
    f.write("ephemeral")

with open("/tmp/temp_test.txt", "r") as f:
    print("TMPFS_READ:", f.read())
"""
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert "TMPFS_READ: ephemeral" in result.stdout


# 11. Docker Socket Non-Exposure
def test_security_docker_socket_not_exposed(docker_executor):
    """Scenario 11: Host Docker daemon socket is not mounted or accessible."""
    code = """
from pathlib import Path

sock = Path("/var/run/docker.sock")
print("DOCKER_SOCK_EXISTS:", sock.exists())
"""
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert "DOCKER_SOCK_EXISTS: False" in result.stdout


# 12. Memory Limit Containment
def test_security_memory_limit_containment(docker_executor):
    """Scenario 12: Memory allocation bomb is safely terminated without crashing host."""
    code = """
# Attempt to allocate 1 GB in a 256MB container
data = []
while True:
    data.append(bytearray(50 * 1024 * 1024))
"""
    result = docker_executor.execute_code(code, timeout=5.0)

    assert result.success is False
    assert result.status in (SandboxExecutionStatus.RESOURCE_LIMIT, SandboxExecutionStatus.FAILURE, SandboxExecutionStatus.TIMEOUT)


# 13. Process / PID Limit (Fork Bomb Pattern)
def test_security_pids_limit_fork_bomb(docker_executor):
    """Scenario 13: Fork bomb / excessive process creation is bounded by pids-limit."""
    code = """
import os

try:
    for _ in range(200):
        os.fork()
    print("FORK_BOMB_UNBOUNDED")
except Exception as e:
    print("FORK_BLOCKED:", type(e).__name__)
"""
    result = docker_executor.execute_code(code, timeout=5.0)

    assert "FORK_BOMB_UNBOUNDED" not in result.stdout


# 14. Bounded Stdout / Stderr Truncation
def test_security_excessive_stdout_truncated(docker_executor):
    """Scenario 14: Very large stdout output is safely truncated to protect API memory."""
    code = "print('B' * 150000)"
    result = docker_executor.execute_code(code)

    assert result.success is True
    assert result.output_truncated is True
    assert len(result.stdout.encode("utf-8")) <= docker_executor.max_output_bytes + 200
    assert "Output truncated" in result.stdout


# 15. Malicious Pytest Fixture Attack
def test_security_malicious_pytest_fixture_isolation(docker_executor):
    """Scenario 15: Malicious pytest suite attempting host modification is contained."""
    code = "def target_func(): return 42"
    malicious_test = """
import os
import pytest
from code_under_test import target_func

def test_exploit_attempt():
    assert target_func() == 42
    # Attempt unauthorized write
    try:
        with open("/etc/pwned", "w") as f:
            f.write("attack")
    except OSError:
        pass  # Expected read-only
"""
    suite = docker_executor.execute_pytest(code, malicious_test)

    assert suite.total_tests == 1
    assert suite.passed == 1
    assert suite.timeout_occurred is False
