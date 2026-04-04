"""
NeuroDebug — Rule-Based Engine

Applies deterministic symbolic rules on top of the AST analysis output.
Each rule returns a structured issue dict when triggered.
"""

import re
import logging
from typing import Any

logger = logging.getLogger("neurodebug.rules")


# ──────────────────────────────────────────────────────────────────
# Issue schema helper
# ──────────────────────────────────────────────────────────────────

def _issue(rule_id: str, severity: str, category: str, message: str, line: int | None = None) -> dict:
    return {
        "rule_id":  rule_id,
        "severity": severity,       # "error" | "warning" | "info"
        "category": category,
        "message":  message,
        "line":     line,
    }


# ──────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────

def apply_rules(code: str, ast_result: dict[str, Any]) -> list[dict]:
    """
    Run all symbolic rules against the code + AST analysis.
    Returns a list of issue dicts (may be empty).
    """
    issues: list[dict] = []

    issues.extend(_rule_syntax_error(ast_result))
    issues.extend(_rule_undefined_variables(ast_result))
    issues.extend(_rule_return_outside_function(ast_result))
    issues.extend(_rule_bare_except(ast_result))
    issues.extend(_rule_mutable_defaults(ast_result))
    issues.extend(_rule_division_by_zero(ast_result))
    issues.extend(_rule_infinite_loop(ast_result))
    issues.extend(_rule_print_without_parens(code))
    issues.extend(_rule_comparison_with_none(code))
    issues.extend(_rule_comparison_with_bool(code))
    issues.extend(_rule_shadowed_builtins(ast_result))
    issues.extend(_rule_empty_except_body(code))
    issues.extend(_rule_unused_imports(ast_result, code))

    logger.debug("Rules fired: %d issues", len(issues))
    return issues


# ──────────────────────────────────────────────────────────────────
# Individual rules
# ──────────────────────────────────────────────────────────────────

def _rule_syntax_error(ast_result: dict) -> list[dict]:
    if ast_result.get("syntax_error"):
        return [_issue(
            "R001", "error", "SyntaxError",
            ast_result["syntax_error"],
        )]
    return []


def _rule_undefined_variables(ast_result: dict) -> list[dict]:
    issues = []
    for name in ast_result.get("undefined_names", []):
        issues.append(_issue(
            "R002", "error", "UndefinedVariable",
            f"Name '{name}' is used but never defined in this snippet.",
        ))
    return issues


def _rule_return_outside_function(ast_result: dict) -> list[dict]:
    if ast_result.get("return_outside_function"):
        return [_issue(
            "R003", "error", "ReturnOutsideFunction",
            "'return' statement found outside of any function definition.",
        )]
    return []


def _rule_bare_except(ast_result: dict) -> list[dict]:
    count = ast_result.get("bare_excepts", 0)
    if count:
        return [_issue(
            "R004", "warning", "BareExcept",
            f"Found {count} bare 'except:' clause(s). Always catch a specific exception type.",
        )]
    return []


def _rule_mutable_defaults(ast_result: dict) -> list[dict]:
    issues = []
    for fname in ast_result.get("mutable_defaults", []):
        issues.append(_issue(
            "R005", "warning", "MutableDefaultArgument",
            f"Function '{fname}' uses a mutable default argument (list/dict/set). "
            "This can cause unexpected behaviour across calls — use None and initialise inside the function.",
        ))
    return issues


def _rule_division_by_zero(ast_result: dict) -> list[dict]:
    if ast_result.get("division_by_zero_risk"):
        return [_issue(
            "R006", "error", "DivisionByZero",
            "Literal division by zero detected (e.g. x / 0). This will raise ZeroDivisionError at runtime.",
        )]
    return []


def _rule_infinite_loop(ast_result: dict) -> list[dict]:
    if ast_result.get("infinite_loop_risk"):
        return [_issue(
            "R007", "warning", "InfiniteLoop",
            "'while True:' loop detected with no 'break' statement. This may cause an infinite loop.",
        )]
    return []


def _rule_print_without_parens(code: str) -> list[dict]:
    """Detect Python 2-style `print x` (without parentheses)."""
    issues = []
    for i, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip()
        # Matches `print something` where `something` doesn't start with `(`
        if re.match(r"^print\s+[^(]", stripped):
            issues.append(_issue(
                "R008", "warning", "Python2Print",
                f"Line {i}: `print` used without parentheses. Use print() for Python 3.",
                line=i,
            ))
    return issues


def _rule_comparison_with_none(code: str) -> list[dict]:
    """Detect `== None` / `!= None` instead of `is None` / `is not None`."""
    issues = []
    for i, line in enumerate(code.splitlines(), start=1):
        if re.search(r"[!=]=\s*None", line):
            issues.append(_issue(
                "R009", "warning", "NoneComparison",
                f"Line {i}: Use `is None` or `is not None` instead of `== None` / `!= None`.",
                line=i,
            ))
    return issues


def _rule_comparison_with_bool(code: str) -> list[dict]:
    """Detect `== True` / `== False`."""
    issues = []
    for i, line in enumerate(code.splitlines(), start=1):
        if re.search(r"[!=]=\s*(True|False)", line):
            issues.append(_issue(
                "R010", "warning", "BoolComparison",
                f"Line {i}: Avoid comparing to True/False with ==. Use the value directly or `is True/False`.",
                line=i,
            ))
    return issues


_SHADOW_BUILTINS = {
    "list", "dict", "set", "tuple", "str", "int", "float", "bool",
    "type", "input", "open", "id", "hash", "sum", "min", "max",
    "len", "range", "print", "object", "format", "filter", "map",
    "zip", "sorted", "reversed", "enumerate",
}


def _rule_shadowed_builtins(ast_result: dict) -> list[dict]:
    issues = []
    for var in ast_result.get("variables", []):
        if var in _SHADOW_BUILTINS:
            issues.append(_issue(
                "R011", "warning", "ShadowedBuiltin",
                f"Variable '{var}' shadows a Python built-in. Rename it to avoid confusion.",
            ))
    return issues


def _rule_empty_except_body(code: str) -> list[dict]:
    """Detect `except ...: pass` — silently swallowing exceptions."""
    issues = []
    lines = code.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("except") and stripped.endswith(":"):
            # Look at the next non-empty line
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip() == "pass":
                issues.append(_issue(
                    "R012", "warning", "SilentException",
                    f"Line {i + 1}: Exception silently swallowed with `pass`. "
                    "Log or handle the error rather than ignoring it.",
                    line=i + 1,
                ))
    return issues


def _rule_unused_imports(ast_result: dict, code: str) -> list[dict]:
    """Warn about imports whose top-level name never appears in the source."""
    issues = []
    for imp in ast_result.get("imports", []):
        # Use the last component (e.g. `os.path` → check for `path`)
        top_name = imp.split(".")[0]
        # If top_name doesn't appear in code at all after the import line → unused
        if top_name not in code.replace(f"import {top_name}", "", 1):
            issues.append(_issue(
                "R013", "info", "UnusedImport",
                f"Import '{imp}' appears to be unused in this code snippet.",
            ))
    return issues
