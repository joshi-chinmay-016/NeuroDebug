"""
Tests for Execution Layer.
"""

import pytest

from services.execution_layer import ExecutionLayer, ExecutionResult


class TestExecutionLayer:
    """Test suite for ExecutionLayer."""

    def test_execute_successful_code(self):
        """Test execution of successful Python code."""
        layer = ExecutionLayer()
        code = "print('Hello, World!')"

        result = layer.execute_code(code)

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout
        assert result.timeout_occurred is False

    def test_execute_failing_code(self):
        """Test execution of failing Python code."""
        layer = ExecutionLayer()
        code = "x = undefined_var"

        result = layer.execute_code(code)

        assert isinstance(result, ExecutionResult)
        assert result.success is False
        assert result.exit_code != 0
        assert "NameError" in result.stderr or "undefined_var" in result.stderr
        assert result.timeout_occurred is False

    def test_execute_empty_code_raises_error(self):
        """Test that empty code raises ValueError."""
        layer = ExecutionLayer()

        with pytest.raises(ValueError, match="Code cannot be empty"):
            layer.execute_code("")

        with pytest.raises(ValueError, match="Code cannot be empty"):
            layer.execute_code("   ")

    def test_execute_with_timeout(self):
        """Test execution with custom timeout."""
        layer = ExecutionLayer(timeout=5.0)
        code = "print('test')"

        result = layer.execute_code(code, timeout=2.0)

        assert result.success is True
        assert result.execution_time < 2.5

    def test_execute_timeout_occurred(self):
        """Test that timeout is enforced."""
        layer = ExecutionLayer(timeout=1.0)
        code = "import time; time.sleep(10)"

        result = layer.execute_code(code)

        assert result.success is False
        assert result.timeout_occurred is True
        assert result.exit_code == -1
        assert "timeout" in result.stderr.lower()

    def test_execute_with_syntax_error(self):
        """Test execution of code with syntax error."""
        layer = ExecutionLayer()
        code = "def test(\n    print('missing paren')"

        result = layer.execute_code(code)

        assert result.success is False
        assert result.exit_code != 0
        assert "SyntaxError" in result.stderr

    def test_execute_traceback_extraction(self):
        """Test that traceback is extracted from stderr."""
        layer = ExecutionLayer()
        code = "1/0"

        result = layer.execute_code(code)

        assert result.success is False
        assert result.traceback is not None
        assert "Traceback" in result.traceback or "ZeroDivisionError" in result.traceback

    def test_max_execution_time_enforced(self):
        """Test that MAX_EXECUTION_TIME is enforced."""
        layer = ExecutionLayer(timeout=100.0)
        # The timeout should be capped at MAX_EXECUTION_TIME (60s)
        assert layer.timeout == 60.0

    def test_invalid_timeout_raises_error(self):
        """Test that invalid timeout raises ValueError."""
        layer = ExecutionLayer()

        with pytest.raises(ValueError, match="Timeout must be positive"):
            layer.execute_code("print('test')", timeout=-1)

        with pytest.raises(ValueError, match="Timeout must be positive"):
            layer.execute_code("print('test')", timeout=0)
