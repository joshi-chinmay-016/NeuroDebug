"""
Unit tests for Prompt Builder.
"""

import pytest
from llm.prompt_builder import PromptBuilder


class TestPromptBuilder:
    """Test suite for PromptBuilder."""

    def test_build_patch_prompt_with_issues(self):
        """Test building patch prompt with detected issues."""
        code = "x = undefined_var\nprint(x)"
        issues = [
            {
                "rule_id": "R002",
                "severity": "error",
                "category": "UndefinedVariable",
                "message": "Name 'undefined_var' is used but never defined",
                "line": 1
            }
        ]
        prompt = PromptBuilder.build_patch_prompt(code, issues)
        assert "## Original Code" in prompt
        assert "## Detected Issues" in prompt
        assert "undefined_var" in prompt
        assert "UndefinedVariable" in prompt

    def test_build_patch_prompt_no_issues(self):
        """Test building patch prompt with no issues."""
        code = "x = 1\nprint(x)"
        issues = []
        prompt = PromptBuilder.build_patch_prompt(code, issues)
        assert "## Original Code" in prompt
        assert "(no issues detected)" in prompt

    def test_build_analysis_prompt(self):
        """Test building analysis prompt."""
        code = "x = 1\nprint(x)"
        issues = [
            {
                "rule_id": "R001",
                "severity": "error",
                "category": "SyntaxError",
                "message": "Invalid syntax",
                "line": 1
            }
        ]
        prompt = PromptBuilder.build_analysis_prompt(code, issues)
        assert "## Code Under Analysis" in prompt
        assert "## Symbolic Findings" in prompt
        assert "return the JSON" in prompt

    def test_format_findings_single_issue(self):
        """Test formatting a single issue."""
        issues = [
            {
                "rule_id": "R002",
                "severity": "error",
                "category": "UndefinedVariable",
                "message": "Name 'x' is not defined",
                "line": 1
            }
        ]
        formatted = PromptBuilder._format_findings(issues)
        assert "[1]" in formatted
        assert "[ERROR]" in formatted
        assert "UndefinedVariable" in formatted

    def test_format_findings_multiple_issues(self):
        """Test formatting multiple issues."""
        issues = [
            {
                "rule_id": "R002",
                "severity": "error",
                "category": "UndefinedVariable",
                "message": "Name 'x' is not defined",
                "line": 1
            },
            {
                "rule_id": "R004",
                "severity": "warning",
                "category": "BareExcept",
                "message": "Bare except clause",
                "line": 2
            }
        ]
        formatted = PromptBuilder._format_findings(issues)
        assert "[1]" in formatted
        assert "[2]" in formatted
        assert "[ERROR]" in formatted
        assert "[WARNING]" in formatted

    def test_format_findings_issue_with_line(self):
        """Test formatting issue with line number."""
        issues = [
            {
                "rule_id": "R002",
                "severity": "error",
                "category": "UndefinedVariable",
                "message": "Name 'x' is not defined",
                "line": 5
            }
        ]
        formatted = PromptBuilder._format_findings(issues)
        assert "(line 5)" in formatted

    def test_format_findings_issue_without_line(self):
        """Test formatting issue without line number."""
        issues = [
            {
                "rule_id": "R002",
                "severity": "error",
                "category": "UndefinedVariable",
                "message": "Name 'x' is not defined",
                "line": None
            }
        ]
        formatted = PromptBuilder._format_findings(issues)
        # Should not include line info
        assert "(line" not in formatted

    def test_patch_generation_system_prompt(self):
        """Test patch generation system prompt exists and is non-empty."""
        prompt = PromptBuilder.PATCH_GENERATION_SYSTEM
        assert len(prompt) > 0
        assert "minimal" in prompt.lower()
        assert "python code" in prompt.lower()

    def test_analysis_system_prompt(self):
        """Test analysis system prompt exists and is non-empty."""
        prompt = PromptBuilder.ANALYSIS_SYSTEM
        assert len(prompt) > 0
        assert "json" in prompt.lower()
        assert "error_type" in prompt
