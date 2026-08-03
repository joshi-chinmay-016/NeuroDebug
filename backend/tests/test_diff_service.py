"""
Unit tests for Diff Service.
"""

import pytest
from services.diff_service import DiffService


class TestDiffService:
    """Test suite for DiffService."""

    def test_generate_unified_diff_with_changes(self):
        """Test unified diff generation with actual changes."""
        original = "x = 1\nprint(x)"
        patched = "x = 2\nprint(x)"
        diff = DiffService.generate_unified_diff(original, patched)
        assert "--- original.py" in diff
        assert "+++ patched.py" in diff
        assert "-x = 1" in diff
        assert "+x = 2" in diff

    def test_generate_unified_diff_no_changes(self):
        """Test unified diff generation with no changes."""
        original = "x = 1\nprint(x)"
        patched = "x = 1\nprint(x)"
        diff = DiffService.generate_unified_diff(original, patched)
        assert "No changes detected" in diff

    def test_generate_unified_diff_custom_filenames(self):
        """Test unified diff with custom filenames."""
        original = "x = 1"
        patched = "x = 2"
        diff = DiffService.generate_unified_diff(
            original,
            patched,
            original_filename="file1.py",
            patched_filename="file2.py"
        )
        assert "--- file1.py" in diff
        assert "+++ file2.py" in diff

    def test_generate_unified_diff_multiline(self):
        """Test unified diff with multiline changes."""
        original = """def add(a, b):
    return a + b

result = add(2, 3)
print(result)"""
        patched = """def add(a, b):
    return a + b

result = add(5, 10)
print(result)"""
        diff = DiffService.generate_unified_diff(original, patched)
        assert "-result = add(2, 3)" in diff
        assert "+result = add(5, 10)" in diff

    def test_count_changed_lines_addition(self):
        """Test counting changed lines with additions."""
        original = "x = 1"
        patched = "x = 1\ny = 2\nz = 3"
        counts = DiffService.count_changed_lines(original, patched)
        assert counts["added"] == 2
        assert counts["removed"] == 0

    def test_count_changed_lines_removal(self):
        """Test counting changed lines with removals."""
        original = "x = 1\ny = 2\nz = 3"
        patched = "x = 1"
        counts = DiffService.count_changed_lines(original, patched)
        assert counts["added"] == 0
        assert counts["removed"] == 2

    def test_count_changed_lines_replacement(self):
        """Test counting changed lines with replacements."""
        original = "x = 1\ny = 2"
        patched = "a = 1\nb = 2"
        counts = DiffService.count_changed_lines(original, patched)
        assert counts["changed"] > 0

    def test_has_changes_true(self):
        """Test has_changes returns True when there are changes."""
        original = "x = 1"
        patched = "x = 2"
        has_changes = DiffService.has_changes(original, patched)
        assert has_changes is True

    def test_has_changes_false(self):
        """Test has_changes returns False when there are no changes."""
        original = "x = 1"
        patched = "x = 1"
        has_changes = DiffService.has_changes(original, patched)
        assert has_changes is False

    def test_has_changes_whitespace_only(self):
        """Test has_changes with whitespace differences."""
        original = "x = 1"
        patched = "x = 1   "
        has_changes = DiffService.has_changes(original, patched)
        assert has_changes is False  # Whitespace is stripped
