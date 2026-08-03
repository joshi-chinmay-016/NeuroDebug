"""
Unit tests for Debug Service.
"""

from unittest.mock import patch

import pytest

from models.errors import AnalysisError
from services.debug_service import DebugService


class TestDebugService:
    """Test suite for DebugService."""

    @pytest.fixture
    def debug_service(self):
        """Create a DebugService instance for testing."""
        return DebugService()

    def test_determine_error_type_syntax_error(self, debug_service):
        """Test error type determination with syntax error."""
        ast_result = {
            "syntax_error": "SyntaxError at line 1: invalid syntax",
            "success": False,
        }
        rule_issues = []
        error_type, confidence = debug_service._determine_error_type(
            ast_result, rule_issues
        )
        assert error_type == "SyntaxError"
        assert confidence == 1.0

    def test_determine_error_type_error_severity(self, debug_service):
        """Test error type determination with error-severity rule."""
        ast_result = {"syntax_error": None, "success": True}
        rule_issues = [
            {
                "rule_id": "R002",
                "severity": "error",
                "category": "UndefinedVariable",
                "message": "Name 'x' is not defined",
            }
        ]
        error_type, confidence = debug_service._determine_error_type(
            ast_result, rule_issues
        )
        assert error_type == "UndefinedVariable"
        assert confidence == 0.9

    def test_determine_error_type_warning_severity(self, debug_service):
        """Test error type determination with warning-severity rule."""
        ast_result = {"syntax_error": None, "success": True}
        rule_issues = [
            {
                "rule_id": "R004",
                "severity": "warning",
                "category": "BareExcept",
                "message": "Bare except clause",
            }
        ]
        error_type, confidence = debug_service._determine_error_type(
            ast_result, rule_issues
        )
        assert error_type == "BareExcept"
        assert confidence == 0.7

    def test_determine_error_type_no_issues(self, debug_service):
        """Test error type determination with no issues."""
        ast_result = {"syntax_error": None, "success": True}
        rule_issues = []
        error_type, confidence = debug_service._determine_error_type(
            ast_result, rule_issues
        )
        assert error_type == "Clean"
        assert confidence == 1.0

    def test_generate_explanation_syntax_error(self, debug_service):
        """Test explanation generation with syntax error."""
        ast_result = {
            "syntax_error": "SyntaxError at line 1: missing colon",
            "success": False,
        }
        rule_issues = []
        explanation = debug_service._generate_explanation(ast_result, rule_issues)
        assert "SyntaxError" in explanation
        assert "missing colon" in explanation

    def test_generate_explanation_no_issues(self, debug_service):
        """Test explanation generation with no issues."""
        ast_result = {"syntax_error": None, "success": True}
        rule_issues = []
        explanation = debug_service._generate_explanation(ast_result, rule_issues)
        assert "No issues detected" in explanation

    def test_generate_explanation_with_issues(self, debug_service):
        """Test explanation generation with rule issues."""
        ast_result = {"syntax_error": None, "success": True}
        rule_issues = [
            {
                "rule_id": "R002",
                "severity": "error",
                "category": "UndefinedVariable",
                "message": "Name 'x' is not defined",
            },
            {
                "rule_id": "R004",
                "severity": "warning",
                "category": "BareExcept",
                "message": "Bare except clause",
            },
        ]
        explanation = debug_service._generate_explanation(ast_result, rule_issues)
        assert "Detected issues" in explanation
        assert "Name 'x' is not defined" in explanation
        assert "Bare except clause" in explanation

    def test_generate_explanation_limits_to_top_3(self, debug_service):
        """Test explanation generation limits to top 3 issues."""
        ast_result = {"syntax_error": None, "success": True}
        rule_issues = [
            {
                "rule_id": f"R00{i}",
                "severity": "error",
                "category": f"Error{i}",
                "message": f"Error message {i}",
            }
            for i in range(1, 6)
        ]
        explanation = debug_service._generate_explanation(ast_result, rule_issues)
        assert "and 2 more issue" in explanation

    @pytest.mark.asyncio
    async def test_debug_code_empty_code(self, debug_service):
        """Test debug_code with empty code handles gracefully."""
        # Empty code is handled by the service
        result = await debug_service.debug_code("", None)
        # Should handle empty code without crashing
        assert result is not None

    @pytest.mark.asyncio
    @patch("services.debug_service.analyze_code_ast")
    @patch("services.debug_service.apply_rules")
    async def test_debug_code_ast_failure(
        self, mock_apply_rules, mock_analyze, debug_service
    ):
        """Test debug_code handles AST analysis failure."""
        mock_analyze.side_effect = Exception("AST parse failed")
        with pytest.raises(AnalysisError):
            await debug_service.debug_code("x = 1", None)

    @pytest.mark.asyncio
    @patch("services.debug_service.analyze_code_ast")
    @patch("services.debug_service.apply_rules")
    async def test_debug_code_rule_failure(
        self, mock_apply_rules, mock_analyze, debug_service
    ):
        """Test debug_code handles rule engine failure."""
        mock_analyze.return_value = {"success": True, "syntax_error": None}
        mock_apply_rules.side_effect = Exception("Rule engine failed")
        with pytest.raises(AnalysisError):
            await debug_service.debug_code("x = 1", None)
