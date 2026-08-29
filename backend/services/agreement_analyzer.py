"""
AST / LLM Agreement Signal & Consensus Analyzer.

Calculates structured agreement metrics between deterministic symbolic analysis
(AST & Rule Engine) and stochastic neural reasoning (LLM explanation/classification).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from utils.logging import get_logger

logger = get_logger("neurodebug.agreement_analyzer")


class ConsensusStatus(str, Enum):
    """Consensus status between symbolic AST and neural LLM."""

    FULL_CONSENSUS = "FULL_CONSENSUS"
    PARTIAL_AGREEMENT = "PARTIAL_AGREEMENT"
    AST_DOMINATED = "AST_DOMINATED"
    LLM_DOMINATED = "LLM_DOMINATED"
    DISAGREEMENT = "DISAGREEMENT"
    CLEAN_CONSENSUS = "CLEAN_CONSENSUS"


@dataclass
class AgreementSignal:
    """Structured agreement signal between AST and LLM."""

    agreement_score: float  # 0.0 to 1.0
    consensus_status: ConsensusStatus
    matched_issues: list[dict[str, Any]] = field(default_factory=list)
    ast_only_issues: list[dict[str, Any]] = field(default_factory=list)
    llm_only_issues: list[dict[str, Any]] = field(default_factory=list)
    calibrated_confidence: float = 0.0  # 0.0 to 1.0
    synthesis_summary: str = ""


# Mapping table between AST rule IDs / categories and LLM error type keywords
CATEGORY_ALIASES = {
    "syntaxerror": {"syntaxerror", "syntax", "r001", "invalid syntax", "parse error"},
    "undefinedvariable": {"undefinedvariable", "nameerror", "r002", "unbound", "undefined variable"},
    "mutabledefaultargument": {"mutabledefaultargument", "r005", "mutable default", "default argument"},
    "bareexcept": {"bareexcept", "r004", "broad except", "exception handling"},
    "divisionbyzero": {"divisionbyzero", "zerodivisionerror", "r006", "divide by zero"},
    "infiniteloop": {"infiniteloop", "r007", "infinite loop", "while loop"},
    "nonecomparison": {"nonecomparison", "r009", "comparison with none"},
    "boolcomparison": {"boolcomparison", "r010", "comparison with bool"},
    "shadowedbuiltin": {"shadowedbuiltin", "r011", "builtin shadow"},
    "unusedimport": {"unusedimport", "r013", "unused import"},
    "runtimeerror": {"runtimeerror", "indexerror", "keyerror", "typeerror", "attributeerror"},
    "logicerror": {"logicerror", "off by one", "operator error", "logic bug"},
}


class AgreementAnalyzer:
    """Computes consensus and disagreement signals between AST and LLM."""

    @staticmethod
    def analyze_agreement(
        ast_result: dict[str, Any] | None,
        symbolic_issues: list[dict[str, Any]] | None,
        llm_analysis: dict[str, Any] | None,
    ) -> AgreementSignal:
        """
        Compute agreement score, matched findings, and calibrated confidence.

        Args:
            ast_result: Dictionary returned by analyze_code_ast.
            symbolic_issues: List of rule violation dicts from rule_engine.
            llm_analysis: Dictionary containing LLM analysis (error_type, root_cause, line_number, confidence).

        Returns:
            AgreementSignal object.
        """
        ast_issues = list(symbolic_issues or [])
        if ast_result and ast_result.get("syntax_error"):
            ast_issues.append({
                "rule_id": "R001",
                "category": "SyntaxError",
                "message": ast_result["syntax_error"],
                "line": ast_result.get("syntax_error_line", 1),
                "severity": "critical",
            })

        has_ast = len(ast_issues) > 0
        llm_error_type = (llm_analysis.get("error_type") if llm_analysis else "") or ""
        llm_clean = not llm_error_type or llm_error_type.lower() in ("clean", "none", "no error", "unknown")
        has_llm = not llm_clean and bool(llm_analysis)

        # Case 1: Both agree code is clean
        if not has_ast and not has_llm:
            return AgreementSignal(
                agreement_score=1.0,
                consensus_status=ConsensusStatus.CLEAN_CONSENSUS,
                matched_issues=[],
                ast_only_issues=[],
                llm_only_issues=[],
                calibrated_confidence=0.98,
                synthesis_summary="Both AST static analysis and LLM confirm the code has no detectable defects.",
            )

        # Case 2: AST found issues, LLM says clean (Disagreement - AST takes precedence for syntax/rules)
        if has_ast and not has_llm:
            return AgreementSignal(
                agreement_score=0.1,
                consensus_status=ConsensusStatus.AST_DOMINATED,
                matched_issues=[],
                ast_only_issues=ast_issues,
                llm_only_issues=[],
                calibrated_confidence=0.85,
                synthesis_summary=f"AST static rules detected {len(ast_issues)} deterministic issue(s) which the LLM overlooked.",
            )

        # Case 3: LLM found semantic/runtime issue, AST rules clean (LLM-dominated valid semantic bug)
        if not has_ast and has_llm:
            llm_conf = float(llm_analysis.get("confidence", 0.8) or 0.8) if llm_analysis else 0.8
            llm_item = {
                "category": llm_error_type,
                "message": llm_analysis.get("root_cause", ""),
                "line": llm_analysis.get("line_number"),
                "confidence": llm_conf,
            }
            return AgreementSignal(
                agreement_score=0.5,
                consensus_status=ConsensusStatus.LLM_DOMINATED,
                matched_issues=[],
                ast_only_issues=[],
                llm_only_issues=[llm_item],
                calibrated_confidence=round(llm_conf * 0.9, 2),
                synthesis_summary=f"LLM identified a semantic/runtime defect ({llm_error_type}) that is beyond deterministic AST pattern scope.",
            )

        # Case 4: Both detected issues — evaluate overlap
        matched: list[dict[str, Any]] = []
        ast_only: list[dict[str, Any]] = []
        llm_norm = llm_error_type.lower().replace(" ", "").replace("_", "")
        llm_line = llm_analysis.get("line_number") if llm_analysis else None

        for issue in ast_issues:
            rule_id = (issue.get("rule_id") or "").lower()
            cat = (issue.get("category") or "").lower()
            issue_line = issue.get("line")

            # Check for category alias overlap
            alias_set = CATEGORY_ALIASES.get(cat, {cat, rule_id})
            cat_match = (
                llm_norm in alias_set
                or any(alias in llm_norm for alias in alias_set)
                or cat in llm_norm
            )
            line_match = (llm_line is not None and issue_line is not None and abs(llm_line - issue_line) <= 2)

            if cat_match or line_match:
                matched.append({
                    "ast_issue": issue,
                    "llm_category": llm_error_type,
                    "category_match": cat_match,
                    "line_match": line_match,
                })
            else:
                ast_only.append(issue)

        total_issues = len(ast_issues)
        match_ratio = len(matched) / total_issues if total_issues > 0 else 0.0

        if match_ratio >= 0.8:
            status = ConsensusStatus.FULL_CONSENSUS
            score = 0.95
            calibrated_conf = 0.98
            summary = f"Strong consensus: AST and LLM agree on defect root cause ({llm_error_type})."
        elif match_ratio > 0.0:
            status = ConsensusStatus.PARTIAL_AGREEMENT
            score = round(0.5 + (match_ratio * 0.4), 2)
            calibrated_conf = 0.88
            summary = f"Partial agreement: AST and LLM overlap on key defect characteristics ({len(matched)} matched)."
        else:
            status = ConsensusStatus.DISAGREEMENT
            score = 0.25
            calibrated_conf = 0.70
            summary = f"Disagreement: AST flagged '{ast_issues[0].get('category')}' while LLM identified '{llm_error_type}'."

        return AgreementSignal(
            agreement_score=score,
            consensus_status=status,
            matched_issues=matched,
            ast_only_issues=ast_only,
            llm_only_issues=[] if matched else [{"category": llm_error_type}],
            calibrated_confidence=calibrated_conf,
            synthesis_summary=summary,
        )
