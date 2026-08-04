"""
Verification Engine Service.

Orchestrates execution verification of candidate patches.
Provides structured evidence for patch correctness.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from services.execution_layer import ExecutionLayer, ExecutionResult
from services.test_runner import TestRunner, TestSuiteResult
from utils.logging import get_logger, log_pipeline_stage, log_verification_stage

logger = get_logger("neurodebug.verification_engine")


class VerificationStatus(str, Enum):
    """Verification status classification."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class VerificationEvidence:
    """Evidence collected during verification."""

    original_code_execution: ExecutionResult
    patched_code_execution: ExecutionResult
    test_results: TestSuiteResult | None
    execution_comparison: dict[str, Any]


@dataclass
class VerificationReport:
    """Complete verification report for a patch."""

    verification_status: VerificationStatus
    execution_summary: str
    runtime: float
    failure_reason: str | None
    evidence: VerificationEvidence


class VerificationEngine:
    """
    Verifies candidate patches through execution and testing.

    Pipeline:
    1. Execute original code
    2. Execute patched code
    3. Run generated tests (if available)
    4. Compare results
    5. Classify as VERIFIED or UNVERIFIED
    """

    def __init__(
        self,
        execution_layer: ExecutionLayer | None = None,
        test_runner: TestRunner | None = None,
    ):
        """
        Initialize the verification engine.

        Args:
            execution_layer: Optional ExecutionLayer instance.
            test_runner: Optional TestRunner instance.
        """
        self.execution_layer = execution_layer or ExecutionLayer()
        self.test_runner = test_runner or TestRunner()

    def verify_patch(
        self,
        original_code: str,
        patched_code: str,
        test_code: str | None = None,
    ) -> VerificationReport:
        """
        Verify a candidate patch through execution and testing.

        Args:
            original_code: The original Python code.
            patched_code: The candidate patch code.
            test_code: Optional pytest test code for verification.

        Returns:
            VerificationReport with verification status and evidence.
        """
        start_time = time.time()
        logger.info("Starting patch verification")

        # Step 1: Execute original code
        logger.info("Step 1: Executing original code")
        orig_start = time.time()
        original_execution = self.execution_layer.execute_code(original_code)
        orig_duration = (time.time() - orig_start) * 1000
        log_verification_stage(
            logger, "original_execution", orig_duration, "success" if original_execution.success else "failed"
        )

        # Step 2: Execute patched code
        logger.info("Step 2: Executing patched code")
        patch_start = time.time()
        patched_execution = self.execution_layer.execute_code(patched_code)
        patch_duration = (time.time() - patch_start) * 1000
        log_verification_stage(
            logger, "patched_execution", patch_duration, "success" if patched_execution.success else "failed"
        )

        # Step 3: Run tests if provided
        test_results = None
        if test_code:
            logger.info("Step 3: Running test suite")
            test_start = time.time()
            test_results = self.test_runner.run_tests(
                code=patched_code, test_code=test_code
            )
            test_duration = (time.time() - test_start) * 1000
            log_verification_stage(
                logger, "test_execution", test_duration, "success" if test_results.failed == 0 else "failed",
                tests_passed=test_results.passed,
                tests_failed=test_results.failed,
            )

        # Step 4: Compare executions
        execution_comparison = self._compare_executions(
            original_execution, patched_execution
        )

        # Step 5: Classify verification status
        verification_status, failure_reason = self._classify_verification(
            original_execution=original_execution,
            patched_execution=patched_execution,
            test_results=test_results,
            execution_comparison=execution_comparison,
        )

        # Step 6: Generate execution summary
        execution_summary = self._generate_execution_summary(
            original_execution,
            patched_execution,
            test_results,
            verification_status,
        )

        total_runtime = time.time() - start_time

        # Build evidence
        evidence = VerificationEvidence(
            original_code_execution=original_execution,
            patched_code_execution=patched_execution,
            test_results=test_results,
            execution_comparison=execution_comparison,
        )

        logger.info(
            "Verification complete: status=%s runtime=%.2fs",
            verification_status.value,
            total_runtime,
        )

        return VerificationReport(
            verification_status=verification_status,
            execution_summary=execution_summary,
            runtime=total_runtime,
            failure_reason=failure_reason,
            evidence=evidence,
        )

    def _compare_executions(
        self, original: ExecutionResult, patched: ExecutionResult
    ) -> dict[str, Any]:
        """
        Compare original and patched execution results.

        Args:
            original: Original code execution result.
            patched: Patched code execution result.

        Returns:
            Dictionary with comparison metrics.
        """
        return {
            "original_success": original.success,
            "patched_success": patched.success,
            "success_improved": not original.success and patched.success,
            "success_regressed": original.success and not patched.success,
            "original_exit_code": original.exit_code,
            "patched_exit_code": patched.exit_code,
            "original_timeout": original.timeout_occurred,
            "patched_timeout": patched.timeout_occurred,
            "stdout_match": original.stdout == patched.stdout,
            "stderr_match": original.stderr == patched.stderr,
            "execution_time_delta": patched.execution_time - original.execution_time,
        }

    def _classify_verification(
        self,
        original_execution: ExecutionResult,
        patched_execution: ExecutionResult,
        test_results: TestSuiteResult | None,
        execution_comparison: dict[str, Any],
    ) -> tuple[VerificationStatus, str | None]:
        """
        Classify patch as VERIFIED or UNVERIFIED based on evidence.

        Args:
            original_execution: Original code execution result.
            patched_execution: Patched code execution result.
            test_results: Test suite results if available.
            execution_comparison: Execution comparison metrics.

        Returns:
            Tuple of (VerificationStatus, failure_reason).
        """
        failure_reason = None

        # If tests are available, they are the primary verification method
        if test_results:
            if test_results.failed > 0:
                failure_reason = f"{test_results.failed} test(s) failed"
                return VerificationStatus.UNVERIFIED, failure_reason

            if test_results.passed > 0 and test_results.failed == 0:
                return VerificationStatus.VERIFIED, None

            if test_results.total_tests == 0:
                failure_reason = "No tests were executed"
                return VerificationStatus.UNVERIFIED, failure_reason

        # Without tests, use execution comparison
        # Patch is verified if it fixes the original issue
        if execution_comparison["success_improved"]:
            return VerificationStatus.VERIFIED, None

        # Patch is unverified if it introduces a regression
        if execution_comparison["success_regressed"]:
            failure_reason = "Patch introduced execution regression"
            return VerificationStatus.UNVERIFIED, failure_reason

        # Patch is unverified if it times out
        if patched_execution.timeout_occurred:
            failure_reason = "Patched code execution timed out"
            return VerificationStatus.UNVERIFIED, failure_reason

        # Patch is unverified if it still fails
        if not patched_execution.success:
            failure_reason = f"Patched code failed with exit code {patched_execution.exit_code}"
            return VerificationStatus.UNVERIFIED, failure_reason

        # If original succeeded and patch succeeded, need more evidence
        # Without tests, we cannot verify the fix is correct
        if original_execution.success and patched_execution.success:
            failure_reason = "Insufficient evidence - both original and patched code execute successfully without tests"
            return VerificationStatus.UNVERIFIED, failure_reason

        return VerificationStatus.UNVERIFIED, "Unable to verify patch correctness"

    def _generate_execution_summary(
        self,
        original: ExecutionResult,
        patched: ExecutionResult,
        test_results: TestSuiteResult | None,
        status: VerificationStatus,
    ) -> str:
        """
        Generate human-readable execution summary.

        Args:
            original: Original execution result.
            patched: Patched execution result.
            test_results: Test results if available.
            status: Verification status.

        Returns:
            Human-readable summary string.
        """
        parts = []

        parts.append(f"Verification Status: {status.value}")
        parts.append(f"Original Code: {'SUCCESS' if original.success else 'FAILED'}")
        parts.append(f"Patched Code: {'SUCCESS' if patched.success else 'FAILED'}")

        if original.timeout_occurred:
            parts.append("Original code timed out")
        if patched.timeout_occurred:
            parts.append("Patched code timed out")

        if test_results:
            parts.append(
                f"Tests: {test_results.passed} passed, {test_results.failed} failed, {test_results.skipped} skipped"
            )

        parts.append(f"Original execution time: {original.execution_time:.3f}s")
        parts.append(f"Patched execution time: {patched.execution_time:.3f}s")

        return "\n".join(parts)
