"""
Unified Diff Service.

Generates unified diff format for code patches using difflib.
"""

import difflib

from utils.logging import get_logger

logger = get_logger("neurodebug.diff_service")


class DiffService:
    """Service for generating unified diffs between code versions."""

    @staticmethod
    def generate_unified_diff(
        original_code: str,
        patched_code: str,
        original_filename: str = "original.py",
        patched_filename: str = "patched.py",
        context_lines: int = 3,
    ) -> str:
        """
        Generate a unified diff between original and patched code.

        Args:
            original_code: The original code.
            patched_code: The patched code.
            original_filename: Filename for the original (for diff header).
            patched_filename: Filename for the patched (for diff header).
            context_lines: Number of context lines to include in the diff.

        Returns:
            Unified diff string.
        """
        original_lines = original_code.splitlines(keepends=True)
        patched_lines = patched_code.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            patched_lines,
            fromfile=original_filename,
            tofile=patched_filename,
            lineterm="",
            n=context_lines,
        )

        diff_text = "\n".join(diff)

        if not diff_text:
            logger.debug("No differences detected between original and patched code")
            return "No changes detected."

        logger.debug("Generated unified diff: %d lines", len(diff_text.splitlines()))
        return diff_text

    @staticmethod
    def count_changed_lines(original_code: str, patched_code: str) -> dict:
        """
        Count the number of added, removed, and changed lines.

        Args:
            original_code: The original code.
            patched_code: The patched code.

        Returns:
            A dict with keys: added, removed, changed.
        """
        original_lines = original_code.splitlines()
        patched_lines = patched_code.splitlines()

        matcher = difflib.SequenceMatcher(None, original_lines, patched_lines)

        added = 0
        removed = 0
        changed = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                changed += max(i2 - i1, j2 - j1)
            elif tag == "insert":
                added += j2 - j1
            elif tag == "delete":
                removed += i2 - i1

        return {"added": added, "removed": removed, "changed": changed}

    @staticmethod
    def has_changes(original_code: str, patched_code: str) -> bool:
        """
        Check if there are any changes between original and patched code.

        Args:
            original_code: The original code.
            patched_code: The patched code.

        Returns:
            True if there are changes, False otherwise.
        """
        return original_code.strip() != patched_code.strip()
