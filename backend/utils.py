"""
NeuroDebug — Utility Functions

Merges symbolic + neural outputs into a single, consistent response.
"""

import logging
from typing import Any

logger = logging.getLogger("neurodebug.utils")


# ──────────────────────────────────────────────────────────────────
# Merge logic
# ──────────────────────────────────────────────────────────────────

def merge_results(
    ast_result:     dict[str, Any],
    rule_issues:    list[dict],
    llm_result:     dict[str, Any],
) -> dict[str, Any]:
    """
    Combine symbolic and neural analysis into a single coherent result.

    Decision logic:
    - If AST found a hard SyntaxError, that dominates.
    - Otherwise, LLM error_type wins (it has more context).
    - Confidence is boosted when both layers agree, penalised when they disagree.
    """

    syntax_err = ast_result.get("syntax_error")
    symbolic_error_types = {i["category"] for i in rule_issues if i["severity"] == "error"}
    llm_error_type = llm_result.get("error_type", "Unknown")
    llm_confidence = float(llm_result.get("confidence_score", 0.5))

    # ── Pick dominant error type ─────────────────────────────────
    if syntax_err:
        final_error_type = "SyntaxError"
    elif llm_error_type not in ("Unknown", "LLMError", ""):
        final_error_type = llm_error_type
    elif symbolic_error_types:
        final_error_type = next(iter(symbolic_error_types))
    else:
        final_error_type = "Clean"

    # ── Adjust confidence ────────────────────────────────────────
    confidence = llm_confidence
    if symbolic_error_types and final_error_type in symbolic_error_types:
        confidence = min(1.0, confidence + 0.1)   # agreement boosts confidence
    elif symbolic_error_types and final_error_type not in symbolic_error_types:
        confidence = max(0.0, confidence - 0.05)  # disagreement reduces slightly

    # ── Build merged result ──────────────────────────────────────
    merged = {
        "error_type":      final_error_type,
        "explanation":     llm_result.get("explanation", _symbolic_explanation(rule_issues)),
        "suggested_fix":   llm_result.get("suggested_fix", ""),
        "confidence_score": round(confidence, 3),
        "symbolic_issues": rule_issues,
        "raw_errors": _collect_raw_errors(ast_result, rule_issues),
    }

    logger.debug("Merge complete: error_type=%s confidence=%.3f", merged["error_type"], merged["confidence_score"])
    return merged


def _symbolic_explanation(rule_issues: list[dict]) -> str:
    if not rule_issues:
        return "No issues detected by symbolic analysis."
    parts = [f"• [{i['severity'].upper()}] {i['message']}" for i in rule_issues]
    return "Symbolic analysis findings:\n" + "\n".join(parts)


def _collect_raw_errors(ast_result: dict, rule_issues: list[dict]) -> list[str]:
    errors = []
    if ast_result.get("syntax_error"):
        errors.append(ast_result["syntax_error"])
    for issue in rule_issues:
        if issue["severity"] == "error":
            errors.append(f"[{issue['rule_id']}] {issue['message']}")
    return errors


# ──────────────────────────────────────────────────────────────────
# Response formatter
# ──────────────────────────────────────────────────────────────────

def format_response(merged: dict[str, Any]) -> dict[str, Any]:
    """Ensure the final dict exactly matches the DebugResponse schema."""
    return {
        "error_type":      merged.get("error_type", "Unknown"),
        "explanation":     merged.get("explanation", ""),
        "suggested_fix":   merged.get("suggested_fix", ""),
        "confidence_score": float(merged.get("confidence_score", 0.0)),
        "symbolic_issues": merged.get("symbolic_issues", []),
        "raw_errors":      merged.get("raw_errors", []),
    }
