"""
Patch Validator Service.

Validates generated code patches using Python AST parsing.
"""

import ast
import logging
from typing import Tuple

from models.errors import ValidationError
from utils.logging import get_logger

logger = get_logger("neurodebug.patch_validator")


class PatchValidator:
    """Validates Python code patches using AST parsing."""

    @staticmethod
    def validate_syntax(code: str) -> Tuple[bool, str | None]:
        """
        Validate Python code syntax using AST parsing.

        Args:
            code: The Python code to validate.

        Returns:
            A tuple of (is_valid, error_message).
            is_valid is True if the code has valid syntax.
            error_message is None if valid, otherwise contains the syntax error.
        """
        try:
            ast.parse(code)
            logger.debug("Code validation passed: syntax is valid")
            return True, None
        except SyntaxError as exc:
            error_msg = f"SyntaxError at line {exc.lineno}: {exc.msg}"
            logger.warning("Code validation failed: %s", error_msg)
            return False, error_msg
        except Exception as exc:
            error_msg = f"Unexpected validation error: {exc}"
            logger.error("Code validation failed: %s", error_msg)
            return False, error_msg

    @staticmethod
    def validate_patch(
        original_code: str,
        patched_code: str
    ) -> Tuple[bool, str | None]:
        """
        Validate a patch by checking that the patched code has valid syntax.

        Args:
            original_code: The original code (for reference).
            patched_code: The patched code to validate.

        Returns:
            A tuple of (is_valid, error_message).
        """
        is_valid, error = PatchValidator.validate_syntax(patched_code)
        return is_valid, error

    @staticmethod
    def validate_minimal_change(
        original_code: str,
        patched_code: str,
        max_line_ratio: float = 0.5
    ) -> Tuple[bool, str | None]:
        """
        Validate that the patch makes minimal changes to the original code.

        This is a heuristic check to prevent the LLM from rewriting the entire program.

        Args:
            original_code: The original code.
            patched_code: The patched code.
            max_line_ratio: Maximum allowed ratio of changed lines to total lines.

        Returns:
            A tuple of (is_valid, error_message).
        """
        original_lines = original_code.splitlines()
        patched_lines = patched_code.splitlines()

        # If code is very short, allow more flexibility
        if len(original_lines) <= 5:
            return True, None

        # Count changed lines
        max_lines = max(len(original_lines), len(patched_lines))
        changed_lines = sum(
            1 for i in range(max_lines)
            if i >= len(original_lines) or i >= len(patched_lines)
            or original_lines[i].strip() != patched_lines[i].strip()
        )

        change_ratio = changed_lines / max_lines

        if change_ratio > max_line_ratio:
            error_msg = (
                f"Patch changes too many lines ({changed_lines}/{max_lines} = {change_ratio:.1%}). "
                f"Maximum allowed: {max_line_ratio:.1%}. "
                "The patch should only modify the minimum necessary lines."
            )
            logger.warning("Minimal change validation failed: %s", error_msg)
            return False, error_msg

        logger.debug("Minimal change validation passed: %d/%d lines changed", changed_lines, max_lines)
        return True, None
