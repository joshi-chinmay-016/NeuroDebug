"""
Prompt Builder for LLM interactions.

Provides reusable prompt templates for code analysis and patch generation.
"""

from typing import Any


class PromptBuilder:
    """Builder for structured LLM prompts."""

    # System prompt for patch generation
    PATCH_GENERATION_SYSTEM = """
You are a neural code repair assistant. Your task is to generate minimal, targeted patches for Python code.

STRICT OUTPUT RULES:
1. Respond ONLY with valid Python code — no markdown, no code fences, no explanations
2. Fix ONLY the detected issues listed in the symbolic findings
3. Preserve all original formatting, indentation, and style
4. Preserve all behavior that is not related to the detected issues
5. Avoid unnecessary refactoring or code improvements
6. Never rename variables unless required to fix the issue
7. Never invent new features or functionality
8. Return the complete, patched code (not just the changed lines)

If no issues are detected, return the original code unchanged.
""".strip()

    # System prompt for analysis (explanation only)
    ANALYSIS_SYSTEM = """
You are a neural debugging assistant. Analyze the provided code and symbolic findings.

STRICT OUTPUT RULE: Respond ONLY with a single valid JSON object — no explanation,
no markdown, no code fences. The JSON must contain exactly these keys:

{
  "error_type":       "<short label for the error category>",
  "explanation":      "<clear explanation of the root cause>",
  "suggested_fix":    "<actionable fix or refactor suggestion>",
  "confidence_score": <float between 0.0 and 1.0>
}

If you cannot determine an issue, still return valid JSON with best-effort values.
""".strip()

    @staticmethod
    def build_patch_prompt(code: str, symbolic_issues: list[dict[str, Any]]) -> str:
        """
        Build a prompt for patch generation.

        Args:
            code: The original Python code.
            symbolic_issues: List of detected symbolic issues.

        Returns:
            Formatted prompt string.
        """
        findings_block = PromptBuilder._format_findings(symbolic_issues)

        return (
            f"## Original Code\n\n"
            f"```\n{code}\n```\n\n"
            f"## Detected Issues\n\n"
            f"{findings_block}\n\n"
            f"Generate a minimal patch that fixes ONLY the detected issues above. "
            f"Return the complete patched code as valid Python only."
        )

    @staticmethod
    def build_analysis_prompt(code: str, symbolic_issues: list[dict[str, Any]]) -> str:
        """
        Build a prompt for code analysis (explanation generation).

        Args:
            code: The Python code to analyze.
            symbolic_issues: List of detected symbolic issues.

        Returns:
            Formatted prompt string.
        """
        findings_block = PromptBuilder._format_findings(symbolic_issues)

        return (
            f"## Code Under Analysis\n\n"
            f"```\n{code}\n```\n\n"
            f"## Symbolic Findings\n\n"
            f"{findings_block}\n\n"
            f"Analyze the code in light of the symbolic findings and return the JSON."
        )

    @staticmethod
    def _format_findings(issues: list[dict[str, Any]]) -> str:
        """Format symbolic findings into a readable block."""
        if not issues:
            return "  (no issues detected)"

        formatted = []
        for i, issue in enumerate(issues, 1):
            severity = issue.get("severity", "unknown").upper()
            category = issue.get("category", "Unknown")
            message = issue.get("message", "")
            line = issue.get("line")
            line_info = f" (line {line})" if line else ""
            formatted.append(f"  [{i}] [{severity}] {category}: {message}{line_info}")
        return "\n".join(formatted)
