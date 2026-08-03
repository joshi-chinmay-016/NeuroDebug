"""
Unit tests for Patch Validator service.
"""

import pytest
from services.patch_validator import PatchValidator


class TestPatchValidator:
    """Test suite for PatchValidator."""

    def test_validate_syntax_valid_code(self):
        """Test validation of valid Python code."""
        code = """
def add(a, b):
    return a + b

result = add(2, 3)
print(result)
"""
        is_valid, error = PatchValidator.validate_syntax(code)
        assert is_valid is True
        assert error is None

    def test_validate_syntax_invalid_code(self):
        """Test validation of invalid Python code."""
        code = """
def add(a, b:
    return a + b
"""
        is_valid, error = PatchValidator.validate_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "SyntaxError" in error

    def test_validate_syntax_missing_parenthesis(self):
        """Test validation of code with missing parenthesis."""
        code = "print('hello'"
        is_valid, error = PatchValidator.validate_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_validate_patch_valid(self):
        """Test patch validation with valid patch."""
        original = "x = 1\nprint(x)"
        patched = "x = 2\nprint(x)"
        is_valid, error = PatchValidator.validate_patch(original, patched)
        assert is_valid is True
        assert error is None

    def test_validate_patch_invalid(self):
        """Test patch validation with invalid patch."""
        original = "x = 1\nprint(x)"
        patched = "x = 1\nprint(x"  # Missing closing parenthesis
        is_valid, error = PatchValidator.validate_patch(original, patched)
        assert is_valid is False
        assert error is not None

    def test_validate_minimal_change_small_change(self):
        """Test minimal change validation with small change."""
        original = """def add(a, b):
    return a + b

result = add(2, 3)
print(result)"""
        patched = """def add(a, b):
    return a + b

result = add(2, 4)
print(result)"""
        is_valid, error = PatchValidator.validate_minimal_change(original, patched)
        assert is_valid is True
        assert error is None

    def test_validate_minimal_change_large_change(self):
        """Test minimal change validation with large change."""
        original = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b

result = add(2, 3)
print(result)"""
        patched = """def complex_function():
    # This is a completely different function
    for i in range(100):
        print(i)
    return i

complex_function()"""
        is_valid, error = PatchValidator.validate_minimal_change(original, patched)
        assert is_valid is False
        assert error is not None
        assert "too many lines" in error.lower()

    def test_validate_minimal_change_short_code(self):
        """Test minimal change validation allows more flexibility for short code."""
        original = "x = 1"
        patched = "y = 2"
        is_valid, error = PatchValidator.validate_minimal_change(original, patched)
        # Short code should pass even with complete change
        assert is_valid is True

    def test_validate_minimal_change_no_change(self):
        """Test minimal change validation with no change."""
        original = "x = 1\nprint(x)"
        patched = "x = 1\nprint(x)"
        is_valid, error = PatchValidator.validate_minimal_change(original, patched)
        assert is_valid is True
        assert error is None
