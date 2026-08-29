"""
Tests for Hardened Subprocess Execution Layer.
"""

import os
import pytest

from services.execution_layer import ExecutionLayer


def test_execution_layer_clean_code():
    """Verify standard execution of valid Python code."""
    layer = ExecutionLayer(timeout=5.0)
    result = layer.execute_code("print('Hello from hardened runner!')")

    assert result.success is True
    assert result.exit_code == 0
    assert "Hello from hardened runner!" in result.stdout
    assert result.timeout_occurred is False
    assert result.output_truncated is False


def test_execution_layer_timeout_handling():
    """Verify that infinite loops timeout and process is killed."""
    layer = ExecutionLayer(timeout=1.0)
    code = "import time\nwhile True:\n    time.sleep(0.1)\n"
    result = layer.execute_code(code, timeout=1.0)

    assert result.success is False
    assert result.timeout_occurred is True
    assert "Execution timeout" in result.stderr


def test_execution_layer_output_truncation():
    """Verify output size cap protects against unbounded stdout."""
    layer = ExecutionLayer(timeout=5.0)
    # Generate 100,000 characters
    code = "print('A' * 70000)"
    result = layer.execute_code(code)

    assert result.success is True
    assert result.output_truncated is True
    assert "[... Output truncated" in result.stdout


def test_execution_layer_environment_sanitization(monkeypatch):
    """Verify sensitive environment variables are not leaked into child subprocess."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_super_secret_test_key_12345")
    layer = ExecutionLayer(timeout=5.0)
    code = "import os; print('KEY_PRESENT:', 'GROQ_API_KEY' in os.environ)"
    result = layer.execute_code(code)

    assert result.success is True
    assert "KEY_PRESENT: False" in result.stdout
