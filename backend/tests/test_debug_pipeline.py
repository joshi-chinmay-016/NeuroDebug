"""Tests for the DebugPipeline orchestration layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.responses import (
    DebugResponse,
    ExecutionResultResponse,
    PatchResponse,
    TestResultResponse,
    TestSuiteResultResponse,
    VerificationEvidenceResponse,
    VerificationReportResponse,
)
from services.debug_pipeline import DebugPipeline
from services.execution_layer import ExecutionResult
from services.test_runner import TestResultData, TestSuiteResultData
from services.verification_engine import (
    VerificationEvidence,
    VerificationReport,
    VerificationStatus,
)


def _issue(rule_id: str, severity: str, category: str, message: str) -> dict:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "category": category,
        "message": message,
        "line": 1,
    }


def _verification_report_response() -> VerificationReportResponse:
    return VerificationReportResponse(
        verification_status="VERIFIED",
        execution_summary="Verification Status: VERIFIED",
        runtime=0.25,
        failure_reason=None,
        evidence=VerificationEvidenceResponse(
            original_code_execution=ExecutionResultResponse(
                success=False,
                exit_code=1,
                stdout="",
                stderr="NameError",
                execution_time=0.01,
                timeout_occurred=False,
                traceback=None,
            ),
            patched_code_execution=ExecutionResultResponse(
                success=True,
                exit_code=0,
                stdout="ok\n",
                stderr="",
                execution_time=0.01,
                timeout_occurred=False,
                traceback=None,
            ),
            test_results=TestSuiteResultResponse(
                total_tests=1,
                passed=1,
                failed=0,
                skipped=0,
                duration=0.1,
                test_results=[
                    TestResultResponse(
                        test_name="test_add",
                        passed=True,
                        failed=False,
                        skipped=False,
                        duration=0.1,
                        error_message=None,
                    )
                ],
                output="",
                error=None,
            ),
            execution_comparison={
                "original_success": False,
                "patched_success": True,
                "success_improved": True,
                "success_regressed": False,
            },
        ),
    )


class TestDebugPipeline:
    """Test suite for DebugPipeline."""

    def test_determine_error_type_syntax_error(self, pipeline):
        error_type, confidence = pipeline._determine_error_type(
            {"syntax_error": "SyntaxError at line 1: invalid syntax"}, []
        )

        assert error_type == "SyntaxError"
        assert confidence == 1.0

    def test_determine_error_type_error_severity(self, pipeline):
        error_type, confidence = pipeline._determine_error_type(
            {"syntax_error": None},
            [_issue("R002", "error", "UndefinedVariable", "Name 'x' is not defined")],
        )

        assert error_type == "UndefinedVariable"
        assert confidence == 0.9

    def test_determine_error_type_warning_severity(self, pipeline):
        error_type, confidence = pipeline._determine_error_type(
            {"syntax_error": None},
            [_issue("R004", "warning", "BareExcept", "Bare except clause")],
        )

        assert error_type == "BareExcept"
        assert confidence == 0.7

    def test_determine_error_type_no_issues(self, pipeline):
        error_type, confidence = pipeline._determine_error_type(
            {"syntax_error": None}, []
        )

        assert error_type == "Clean"
        assert confidence == 1.0

    def test_generate_explanation_syntax_error(self, pipeline):
        explanation = pipeline._generate_explanation(
            {"syntax_error": "SyntaxError at line 1: missing colon"}, []
        )

        assert explanation == "SyntaxError at line 1: missing colon"

    def test_generate_explanation_no_issues(self, pipeline):
        explanation = pipeline._generate_explanation({"syntax_error": None}, [])

        assert explanation == "No issues detected in the code."

    def test_generate_explanation_with_issues(self, pipeline):
        explanation = pipeline._generate_explanation(
            {"syntax_error": None},
            [
                _issue("R002", "error", "UndefinedVariable", "Name 'x' is not defined"),
                _issue("R004", "warning", "BareExcept", "Bare except clause"),
            ],
        )

        assert "Detected issues:" in explanation
        assert "Name 'x' is not defined" in explanation
        assert "Bare except clause" in explanation

    def test_generate_explanation_limits_to_top_3(self, pipeline):
        explanation = pipeline._generate_explanation(
            {"syntax_error": None},
            [
                _issue(f"R00{i}", "error", f"Error{i}", f"Error message {i}")
                for i in range(1, 6)
            ],
        )

        assert "... and 2 more issue(s)." in explanation

    @patch("services.debug_pipeline.Config.get_groq_api_key", return_value=None)
    @patch("services.debug_pipeline.analyze_code_ast")
    @patch("services.debug_pipeline.apply_rules")
    @pytest.mark.asyncio
    async def test_execute_returns_clean_response_without_api_key(
        self, mock_apply_rules, mock_analyze_code_ast, _mock_get_groq_api_key, pipeline
    ):
        mock_analyze_code_ast.return_value = {"syntax_error": None, "success": True}
        mock_apply_rules.return_value = []

        result = await pipeline.execute(code="x = 1", api_key=None)

        assert isinstance(result, DebugResponse)
        assert result.error_type == "Clean"
        assert result.explanation == "No issues detected in the code."
        assert result.confidence_score == 1.0
        assert result.patch_status == "not_generated"
        assert result.validation_result == "not_attempted"
        assert result.candidate_patch is None
        assert result.verification_report is None
        assert set(result.metadata) >= {
            "ast_duration_ms",
            "rule_duration_ms",
            "total_duration_ms",
        }

    @patch("routes.debug._convert_verification_report_to_response")
    @patch("services.debug_pipeline.Config.validate_api_key", return_value=True)
    @patch("services.debug_pipeline.Config.get_groq_api_key", return_value="test-key")
    @patch("services.debug_pipeline.GroqClient")
    @patch("services.debug_pipeline.analyze_code_ast")
    @patch("services.debug_pipeline.apply_rules")
    @pytest.mark.asyncio
    async def test_execute_orchestrates_patch_generation_and_verification(
        self,
        mock_apply_rules,
        mock_analyze_code_ast,
        mock_groq_client,
        _mock_get_groq_api_key,
        _mock_validate_api_key,
        mock_convert_verification_report,
    ):
        mock_analyze_code_ast.return_value = {"syntax_error": None, "success": True}
        mock_apply_rules.return_value = [
            _issue("R002", "error", "UndefinedVariable", "Name 'x' is not defined")
        ]

        llm_client = MagicMock()
        llm_client.generate_analysis = AsyncMock(
            return_value={
                "explanation": "LLM explanation",
                "error_type": "UndefinedVariable",
                "confidence_score": 0.88,
            }
        )
        llm_client.generate_patch = AsyncMock(return_value="x = 'defined'")
        mock_groq_client.return_value = llm_client

        patch_response = PatchResponse(
            original_code="x = undefined_var",
            patched_code="x = 'defined'",
            unified_diff="diff",
            validation_passed=True,
            validation_error=None,
        )
        pipeline = DebugPipeline()
        internal_report = VerificationReport(
            verification_status=VerificationStatus.VERIFIED,
            execution_summary="Verification Status: VERIFIED",
            runtime=0.25,
            failure_reason=None,
            evidence=VerificationEvidence(
                original_code_execution=ExecutionResult(
                    success=False,
                    exit_code=1,
                    stdout="",
                    stderr="NameError",
                    execution_time=0.01,
                    timeout_occurred=False,
                    traceback=None,
                ),
                patched_code_execution=ExecutionResult(
                    success=True,
                    exit_code=0,
                    stdout="ok\n",
                    stderr="",
                    execution_time=0.01,
                    timeout_occurred=False,
                    traceback=None,
                ),
                test_results=TestSuiteResultResponse(
                    total_tests=1,
                    passed=1,
                    failed=0,
                    skipped=0,
                    duration=0.1,
                    test_results=[
                        TestResultResponse(
                            test_name="test_add",
                            passed=True,
                            failed=False,
                            skipped=False,
                            duration=0.1,
                            error_message=None,
                        )
                    ],
                    output="",
                    error=None,
                ),
                execution_comparison={
                    "original_success": False,
                    "patched_success": True,
                    "success_improved": True,
                    "success_regressed": False,
                },
            ),
        )
        pipeline.verification_engine.verify_patch = MagicMock(
            return_value=internal_report
        )

        expected_verification_response = _verification_report_response()
        mock_convert_verification_report.return_value = expected_verification_response

        result = await pipeline.execute(code="x = undefined_var", api_key="gsk_test_key_12345")

        assert result.error_type == "UndefinedVariable"
        assert result.explanation == "LLM explanation"
        assert result.confidence_score == 0.88
        assert result.patch_status == "generated"
        assert result.validation_result == "valid"
        assert result.candidate_patch is not None
        assert result.candidate_patch.original_code == patch_response.original_code
        assert result.candidate_patch.patched_code == patch_response.patched_code
        assert result.candidate_patch.validation_passed is True
        assert result.verification_report == expected_verification_response
        assert result.metadata.get("llm_duration_ms") is not None
        assert result.metadata.get("patch_generation_duration_ms") is not None
        assert result.metadata.get("verification_duration_ms") is not None
        llm_client.generate_patch.assert_awaited_once()
        pipeline.verification_engine.verify_patch.assert_called_once()
