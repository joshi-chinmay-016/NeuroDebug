"""
Tests for Verification Engine.
"""

from services.execution_layer import ExecutionLayer
from services.test_runner import TestRunner
from services.verification_engine import VerificationEngine, VerificationStatus


class TestVerificationEngine:
    """Test suite for VerificationEngine."""

    def test_verify_patch_with_success_improvement(self):
        """Test verification when patch fixes the original issue."""
        engine = VerificationEngine()
        original_code = "x = undefined_var\nprint(x)"
        patched_code = "x = 'defined'\nprint(x)"

        report = engine.verify_patch(original_code, patched_code)

        assert report.verification_status == VerificationStatus.VERIFIED
        assert report.failure_reason is None
        assert report.evidence.original_code_execution.success is False
        assert report.evidence.patched_code_execution.success is True
        assert report.runtime > 0

    def test_verify_patch_with_regression(self):
        """Test verification when patch introduces a regression."""
        engine = VerificationEngine()
        original_code = "print('Hello')"
        patched_code = "x = undefined_var\nprint(x)"

        report = engine.verify_patch(original_code, patched_code)

        assert report.verification_status == VerificationStatus.UNVERIFIED
        assert "regression" in report.failure_reason.lower()
        assert report.evidence.original_code_execution.success is True
        assert report.evidence.patched_code_execution.success is False

    def test_verify_patch_both_fail(self):
        """Test verification when both original and patched code fail."""
        engine = VerificationEngine()
        original_code = "x = undefined_var1\nprint(x)"
        patched_code = "x = undefined_var2\nprint(x)"

        report = engine.verify_patch(original_code, patched_code)

        assert report.verification_status == VerificationStatus.UNVERIFIED
        assert report.evidence.original_code_execution.success is False
        assert report.evidence.patched_code_execution.success is False

    def test_verify_patch_with_timeout(self):
        """Test verification when patched code times out."""
        from services.execution_layer import ExecutionLayer

        custom_exec = ExecutionLayer(timeout=1.0)
        engine = VerificationEngine(execution_layer=custom_exec)
        original_code = "print('test')"
        patched_code = "import time; time.sleep(10)"

        report = engine.verify_patch(original_code, patched_code)

        assert report.verification_status == VerificationStatus.UNVERIFIED
        assert report.evidence.patched_code_execution.timeout_occurred is True
        # Timeout is classified as regression when original succeeded
        assert report.evidence.execution_comparison["success_regressed"] is True

    def test_verify_patch_with_tests(self):
        """Test verification with provided test code."""
        engine = VerificationEngine()
        original_code = "def add(a, b):\n    return a + b"
        patched_code = "def add(a, b):\n    return a + b"
        test_code = """
def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
"""

        report = engine.verify_patch(original_code, patched_code, test_code)

        # Test results should be present
        assert report.evidence.test_results is not None
        assert report.evidence.test_results.total_tests >= 1

    def test_verify_patch_execution_comparison(self):
        """Test that execution comparison is calculated correctly."""
        engine = VerificationEngine()
        original_code = "x = 1/0"
        patched_code = "x = 1/1"

        report = engine.verify_patch(original_code, patched_code)

        comparison = report.evidence.execution_comparison
        assert comparison["original_success"] is False
        assert comparison["patched_success"] is True
        assert comparison["success_improved"] is True
        assert comparison["success_regressed"] is False

    def test_verify_patch_custom_components(self):
        """Test verification with custom execution layer and test runner."""
        custom_exec = ExecutionLayer(timeout=5.0)
        custom_test = TestRunner(timeout=5.0)
        engine = VerificationEngine(
            execution_layer=custom_exec, test_runner=custom_test
        )

        original_code = "print('test')"
        patched_code = "print('test')"

        report = engine.verify_patch(original_code, patched_code)

        assert report is not None
        assert report.runtime > 0

    def test_verify_patch_execution_summary(self):
        """Test that execution summary is generated correctly."""
        engine = VerificationEngine()
        original_code = "x = undefined_var"
        patched_code = "x = 'defined'"

        report = engine.verify_patch(original_code, patched_code)

        assert report.execution_summary is not None
        assert "Verification Status" in report.execution_summary
        assert "Original Code" in report.execution_summary
        assert "Patched Code" in report.execution_summary
