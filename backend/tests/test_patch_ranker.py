"""
Unit tests for Evidence-Based Patch Ranker and Verification State Transitions.
"""

from services.patch_ranker import PatchRanker
from services.verification_engine import VerificationStatus


def test_patch_ranker_prefers_verified_candidate():
    """Verify that a verified candidate strictly outranks unverified/invalid candidates."""
    ranker = PatchRanker()
    original_code = "def add(a, b):\n    return a - b\n"
    test_code = "def test_add():\n    from code_under_test import add\n    assert add(2, 3) == 5\n"

    candidates = [
        {"source": "invalid_candidate", "patched_code": "def add(a, b:\n    return a + b\n"},  # Syntax error
        {"source": "wrong_fix", "patched_code": "def add(a, b):\n    return a * b\n"},  # Fails test
        {"source": "verified_fix", "patched_code": "def add(a, b):\n    return a + b\n"},  # Passes test
    ]

    result = ranker.rank_candidates(original_code, candidates, test_code=test_code)

    assert result.best_candidate is not None
    assert result.best_candidate.source == "verified_fix"
    assert result.best_candidate.verification_status == VerificationStatus.VERIFIED.value
    assert result.best_candidate.rank == 1
    assert len(result.all_candidates) == 3

    # Ensure ranking order: verified > test_failure > invalid
    statuses = [c.verification_status for c in result.all_candidates]
    assert statuses[0] == VerificationStatus.VERIFIED.value
    assert statuses[1] == VerificationStatus.TEST_FAILURE.value
    assert statuses[2] == VerificationStatus.INVALID_PATCH.value


def test_patch_ranker_handles_empty_candidates():
    """Verify safe fallback on empty candidates list."""
    ranker = PatchRanker()
    result = ranker.rank_candidates("x = 1", [])
    assert result.best_candidate is None
    assert len(result.all_candidates) == 0


def test_patch_ranker_unverified_clean_execution():
    """Verify unverified state when no test suite is available but code executes cleanly."""
    ranker = PatchRanker()
    original_code = "def greet(name):\n    return f'Hi {name}'\n"
    candidates = [{"source": "llm", "patched_code": "def greet(name):\n    return f'Hello {name}'\n"}]

    result = ranker.rank_candidates(original_code, candidates, test_code=None)
    assert result.best_candidate is not None
    assert result.best_candidate.verification_status == VerificationStatus.UNVERIFIED.value
    assert result.best_candidate.evidence_score >= 50.0
