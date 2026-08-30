"""
Evidence-Based Candidate Patch Ranker.

Ranks candidate patches using empirical verification evidence:
1. AST Syntax Validation
2. Subprocess Execution & Test Verification
3. Test Suite Pass Ratio
4. Execution Latency & Regression Absence

Verified candidates strictly outrank unverified/plausible candidates.
Invalid/malformed patches are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.responses import PatchResponse
from services.diff_service import DiffService
from services.patch_validator import PatchValidator
from services.verification_engine import VerificationEngine, VerificationReport, VerificationStatus
from utils.logging import get_logger

logger = get_logger("neurodebug.patch_ranker")


@dataclass
class CandidateEvaluation:
    """Individual candidate patch evaluation and score."""

    candidate_id: str
    source: str  # e.g. "llm", "deterministic", "rule_engine"
    patched_code: str
    diff: str
    validation_passed: bool
    validation_error: str | None
    verification_report: VerificationReport | None
    verification_status: str
    evidence_score: float  # 0.0 to 100.0
    rank: int = 0
    selection_reason: str = ""


@dataclass
class PatchRankingResult:
    """Complete patch ranking result."""

    best_candidate: CandidateEvaluation | None
    all_candidates: list[CandidateEvaluation] = field(default_factory=list)
    ranking_rationale: str = ""


class PatchRanker:
    """Ranks candidate patches using deterministic verification evidence."""

    def __init__(
        self,
        validator: PatchValidator | None = None,
        verification_engine: VerificationEngine | None = None,
        diff_service: DiffService | None = None,
    ):
        self.validator = validator or PatchValidator()
        self.verification_engine = verification_engine or VerificationEngine()
        self.diff_service = diff_service or DiffService()

    def rank_candidates(
        self,
        original_code: str,
        candidates: list[dict[str, Any]],
        test_code: str | None = None,
    ) -> PatchRankingResult:
        """
        Rank a collection of candidate patches based on actual verification evidence.

        Args:
            original_code: The original buggy Python source.
            candidates: List of dicts, each with 'patched_code', 'source' (e.g. 'llm', 'deterministic').
            test_code: Optional pytest verification test suite.

        Returns:
            PatchRankingResult with the best candidate and detailed rankings.
        """
        if not candidates:
            return PatchRankingResult(
                best_candidate=None,
                all_candidates=[],
                ranking_rationale="No candidate patches were provided for ranking.",
            )

        evaluated: list[CandidateEvaluation] = []
        seen_codes: set[str] = set()

        for idx, cand in enumerate(candidates, start=1):
            source = cand.get("source", f"candidate_{idx}")
            patched_code = cand.get("patched_code", "").strip()
            cand_id = f"{source}_{idx}"

            if not patched_code or patched_code in seen_codes:
                continue
            seen_codes.add(patched_code)

            # 1. AST Syntax Validation
            is_valid, val_err = self.validator.validate_patch(original_code, patched_code)
            diff = self.diff_service.generate_unified_diff(original_code, patched_code)

            verif_report = None
            verif_status = VerificationStatus.INVALID_PATCH.value
            score = 0.0
            reason = "Syntax validation failed"

            if is_valid:
                # 2. Subprocess Execution & Test Verification
                try:
                    verif_report = self.verification_engine.verify_patch(
                        original_code=original_code,
                        patched_code=patched_code,
                        test_code=test_code,
                    )
                    verif_status = verif_report.verification_status.value
                    score, reason = self._compute_evidence_score(verif_report)
                except Exception as exc:
                    logger.warning("Verification execution error on candidate %s: %s", cand_id, exc)
                    verif_status = VerificationStatus.EXECUTION_ERROR.value
                    score = 10.0
                    reason = f"Execution error during verification: {exc}"
            else:
                score = 0.0
                reason = f"Invalid Python syntax: {val_err}"

            evaluated.append(
                CandidateEvaluation(
                    candidate_id=cand_id,
                    source=source,
                    patched_code=patched_code,
                    diff=diff,
                    validation_passed=is_valid,
                    validation_error=val_err,
                    verification_report=verif_report,
                    verification_status=verif_status,
                    evidence_score=score,
                    selection_reason=reason,
                )
            )

        if not evaluated:
            return PatchRankingResult(
                best_candidate=None,
                all_candidates=[],
                ranking_rationale="All candidate patches were empty or duplicates.",
            )

        # Sort by evidence score descending (higher score = better rank)
        evaluated.sort(key=lambda c: c.evidence_score, reverse=True)

        for rank_idx, cand in enumerate(evaluated, start=1):
            cand.rank = rank_idx

        best = evaluated[0]
        rationale = f"Selected candidate '{best.candidate_id}' (Source: {best.source}) with verification status '{best.verification_status}' (Evidence Score: {best.evidence_score:.1f}/100.0). Reason: {best.selection_reason}."

        logger.info(
            "Ranked %d candidates. Best: %s (status=%s, score=%.1f)",
            len(evaluated),
            best.candidate_id,
            best.verification_status,
            best.evidence_score,
        )

        return PatchRankingResult(
            best_candidate=best,
            all_candidates=evaluated,
            ranking_rationale=rationale,
        )

    def _compute_evidence_score(
        self, report: VerificationReport
    ) -> tuple[float, str]:
        """
        Compute empirical evidence score (0-100) based on verification findings.

        Hierarchy:
        - VERIFIED (90-100 pts)
        - UNVERIFIED (50-70 pts)
        - FAILED_VERIFICATION / TEST_FAILURE (20-40 pts)
        - INVALID / TIMEOUT / ERROR (0-15 pts)
        """
        status = report.verification_status

        if status == VerificationStatus.VERIFIED:
            # Base 90 points for verification
            score = 90.0
            if report.evidence.test_results:
                passed = report.evidence.test_results.passed
                total = report.evidence.test_results.total_tests
                pass_ratio = (passed / total) if total > 0 else 1.0
                score += pass_ratio * 10.0
                return round(score, 1), f"Verified: Passed {passed}/{total} test assertions"
            return 95.0, "Verified: Resolved execution failure without regressions"

        if status in (VerificationStatus.UNVERIFIED, VerificationStatus.NOT_VERIFIABLE):
            # Succeeded syntactically and executed cleanly, but no tests were run
            return 60.0, "Unverified: Clean execution, awaiting test assertion evidence"

        if status == VerificationStatus.TEST_FAILURE:
            failed = report.evidence.test_results.failed if report.evidence.test_results else 1
            return 30.0, f"Failed Verification: {failed} test assertion(s) failed"

        if status in (VerificationStatus.FAILED, VerificationStatus.FAILED_VERIFICATION):
            return 25.0, f"Failed Verification: {report.failure_reason or 'Execution regression'}"

        if status in (VerificationStatus.TIMEOUT, VerificationStatus.EXECUTION_TIMEOUT):
            return 10.0, "Execution timed out"

        if status in (VerificationStatus.SANDBOX_ERROR, VerificationStatus.EXECUTION_ERROR):
            return 5.0, f"Sandbox error: {report.failure_reason or 'Execution error occurred'}"

        return 0.0, "Candidate rejected"
