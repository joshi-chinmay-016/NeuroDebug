"""
NeuroDebug — Rule-Based Engine

Applies deterministic symbolic rules on top of the AST analysis output.
Each rule returns a structured issue dict when triggered with exact line diagnostics.
"""

from __future__ import annotations

import re
from typing import Any

from utils.logging import get_logger

logger = get_logger("neurodebug.rule_engine")

_SHADOW_BUILTINS: frozenset[str] = frozenset(
    {
        "list",
        "dict",
        "set",
        "tuple",
        "str",
        "int",
        "float",
        "bool",
        "type",
        "input",
        "open",
        "id",
        "hash",
        "sum",
        "min",
        "max",
        "len",
        "range",
        "print",
        "object",
        "format",
        "filter",
        "map",
        "zip",
        "sorted",
        "reversed",
        "enumerate",
    }
)


# ──────────────────────────────────────────────────────────────────
# Issue Schema Helper
# ──────────────────────────────────────────────────────────────────


def _issue(
    rule_id: str,
    severity: str,
    category: str,
    message: str,
    line: int | None = None,
) -> dict[str, Any]:
    """Create a standardized symbolic issue dictionary."""
    return {
        "rule_id": rule_id,
        "severity": severity,  # "error" | "warning" | "info"
        "category": category,
        "message": message,
        "line": line,
    }


# ──────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────


def apply_rules(code: str, ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Run all deterministic symbolic rules against the code + AST analysis.
    Returns a list of issue dicts (may be empty).
    """
    issues: list[dict[str, Any]] = []

    issues.extend(_rule_syntax_error(ast_result))
    issues.extend(_rule_undefined_variables(ast_result))
    issues.extend(_rule_return_outside_function(ast_result))
    issues.extend(_rule_bare_except(ast_result))
    issues.extend(_rule_mutable_defaults(ast_result))
    issues.extend(_rule_division_by_zero(ast_result))
    issues.extend(_rule_infinite_loop(ast_result))
    issues.extend(_rule_print_without_parens(code))
    issues.extend(_rule_comparison_with_none(code, ast_result))
    issues.extend(_rule_comparison_with_bool(code, ast_result))
    issues.extend(_rule_shadowed_builtins(ast_result))
    issues.extend(_rule_empty_except_body(code, ast_result))
    issues.extend(_rule_unused_imports(ast_result, code))

    logger.debug("Rules fired: %d issues", len(issues))
    return issues


# ──────────────────────────────────────────────────────────────────
# Individual Rules (R001 — R013)
# ──────────────────────────────────────────────────────────────────


def _rule_syntax_error(ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """R001: Python Syntax Error."""
    if ast_result.get("syntax_error"):
        line = ast_result.get("syntax_error_line")
        return [
            _issue(
                "R001",
                "error",
                "SyntaxError",
                ast_result["syntax_error"],
                line=line,
            )
        ]
    return []


def _rule_undefined_variables(ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """R002: Undefined Variable Reference."""
    issues = []
    lines_map = ast_result.get("undefined_name_lines", {})
    for name in ast_result.get("undefined_names", []):
        first_line = lines_map.get(name, [None])[0] if lines_map.get(name) else None
        issues.append(
            _issue(
                "R002",
                "error",
                "UndefinedVariable",
                f"Name '{name}' is used but never defined in this snippet.",
                line=first_line,
            )
        )
    return issues


def _rule_return_outside_function(ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """R003: Return Statement Outside Function."""
    if ast_result.get("return_outside_function"):
        lines = ast_result.get("return_outside_function_lines", [])
        line = lines[0] if lines else None
        return [
            _issue(
                "R003",
                "error",
                "ReturnOutsideFunction",
                "'return' statement found outside of any function definition.",
                line=line,
            )
        ]
    return []


def _rule_bare_except(ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """R004: Bare Except Clause."""
    count = ast_result.get("bare_excepts", 0)
    if count:
        lines = ast_result.get("bare_except_lines", [])
        line = lines[0] if lines else None
        return [
            _issue(
                "R004",
                "warning",
                "BareExcept",
                f"Found {count} bare 'except:' clause(s). Always catch a specific exception type.",
                line=line,
            )
        ]
    return []


def _rule_mutable_defaults(ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """R005: Mutable Default Arguments."""
    issues = []
    details = ast_result.get("mutable_default_details", [])
    if details:
        for detail in details:
            fname = detail.get("function_name")
            line = detail.get("line")
            issues.append(
                _issue(
                    "R005",
                    "warning",
                    "MutableDefaultArgument",
                    f"Function '{fname}' uses a mutable default argument (list/dict/set). "
                    "This can cause unexpected behaviour across calls — use None and initialise inside the function.",
                    line=line,
                )
            )
    else:
        for fname in ast_result.get("mutable_defaults", []):
            issues.append(
                _issue(
                    "R005",
                    "warning",
                    "MutableDefaultArgument",
                    f"Function '{fname}' uses a mutable default argument (list/dict/set). "
                    "This can cause unexpected behaviour across calls — use None and initialise inside the function.",
                )
            )
    return issues


def _rule_division_by_zero(ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """R006: Literal Division by Zero."""
    if ast_result.get("division_by_zero_risk"):
        lines = ast_result.get("division_by_zero_lines", [])
        line = lines[0] if lines else None
        return [
            _issue(
                "R006",
                "error",
                "DivisionByZero",
                "Literal division by zero detected (e.g. x / 0). This will raise ZeroDivisionError at runtime.",
                line=line,
            )
        ]
    return []


def _rule_infinite_loop(ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """R007: Infinite Loop without Break."""
    if ast_result.get("infinite_loop_risk"):
        lines = ast_result.get("infinite_loop_lines", [])
        line = lines[0] if lines else None
        return [
            _issue(
                "R007",
                "warning",
                "InfiniteLoop",
                "'while True:' loop detected with no 'break' statement. This may cause an infinite loop.",
                line=line,
            )
        ]
    return []


def _rule_print_without_parens(code: str) -> list[dict[str, Any]]:
    """R008: Detect Python 2-style `print x` (without parentheses)."""
    issues = []
    for i, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Matches `print something` where `something` doesn't start with `(` or `=`
        if re.match(r"^print\s+[^(=\s]", stripped):
            issues.append(
                _issue(
                    "R008",
                    "warning",
                    "Python2Print",
                    f"Line {i}: `print` used without parentheses. Use print() for Python 3.",
                    line=i,
                )
            )
    return issues


def _rule_comparison_with_none(
    code: str, ast_result: dict[str, Any]
) -> list[dict[str, Any]]:
    """R009: Detect `== None` / `!= None` instead of `is None` / `is not None`."""
    issues = []
    ast_lines = ast_result.get("comparison_with_none_lines", [])
    if ast_lines:
        for line_num in ast_lines:
            issues.append(
                _issue(
                    "R009",
                    "warning",
                    "NoneComparison",
                    f"Line {line_num}: Use `is None` or `is not None` instead of `== None` / `!= None`.",
                    line=line_num,
                )
            )
    else:
        for i, line in enumerate(code.splitlines(), start=1):
            if line.strip().startswith("#"):
                continue
            if re.search(r"[!=]=\s*None\b", line):
                issues.append(
                    _issue(
                        "R009",
                        "warning",
                        "NoneComparison",
                        f"Line {i}: Use `is None` or `is not None` instead of `== None` / `!= None`.",
                        line=i,
                    )
                )
    return issues


def _rule_comparison_with_bool(
    code: str, ast_result: dict[str, Any]
) -> list[dict[str, Any]]:
    """R010: Detect `== True` / `== False`."""
    issues = []
    ast_lines = ast_result.get("comparison_with_bool_lines", [])
    if ast_lines:
        for line_num in ast_lines:
            issues.append(
                _issue(
                    "R010",
                    "warning",
                    "BoolComparison",
                    f"Line {line_num}: Avoid comparing to True/False with ==. Use the value directly or `is True/False`.",
                    line=line_num,
                )
            )
    else:
        for i, line in enumerate(code.splitlines(), start=1):
            if line.strip().startswith("#"):
                continue
            if re.search(r"[!=]=\s*(True|False)\b", line):
                issues.append(
                    _issue(
                        "R010",
                        "warning",
                        "BoolComparison",
                        f"Line {i}: Avoid comparing to True/False with ==. Use the value directly or `is True/False`.",
                        line=i,
                    )
                )
    return issues


def _rule_shadowed_builtins(ast_result: dict[str, Any]) -> list[dict[str, Any]]:
    """R011: Shadowed Built-in Identifier."""
    issues = []
    var_lines = ast_result.get("variable_lines", {})
    for var in ast_result.get("variables", []):
        if var in _SHADOW_BUILTINS:
            first_line = var_lines.get(var, [None])[0] if var_lines.get(var) else None
            issues.append(
                _issue(
                    "R011",
                    "warning",
                    "ShadowedBuiltin",
                    f"Variable '{var}' shadows a Python built-in. Rename it to avoid confusion.",
                    line=first_line,
                )
            )
    return issues


def _rule_empty_except_body(
    code: str, ast_result: dict[str, Any]
) -> list[dict[str, Any]]:
    """R012: Empty Except Body (`pass` or empty swallowing exceptions)."""
    issues = []
    ast_lines = ast_result.get("empty_except_lines", [])
    if ast_lines:
        for line_num in ast_lines:
            issues.append(
                _issue(
                    "R012",
                    "warning",
                    "SilentException",
                    f"Line {line_num}: Exception silently swallowed with `pass`. "
                    "Log or handle the error rather than ignoring it.",
                    line=line_num,
                )
            )
    else:
        lines = code.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("except") and stripped.endswith(":"):
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and lines[j].strip() in ("pass", "..."):
                    issues.append(
                        _issue(
                            "R012",
                            "warning",
                            "SilentException",
                            f"Line {i + 1}: Exception silently swallowed with `pass`. "
                            "Log or handle the error rather than ignoring it.",
                            line=i + 1,
                        )
                    )
    return issues


def _rule_unused_imports(
    ast_result: dict[str, Any], code: str
) -> list[dict[str, Any]]:
    """R013: Warn about imports whose bound identifier is never referenced."""
    issues = []
    import_aliases = ast_result.get("import_aliases", {})

    for bound_name, full_import in import_aliases.items():
        # Check if the bound_name appears in code outside of its import statement
        # Remove the import line pattern
        pattern = rf"(import\s+{re.escape(bound_name)}|from\s+\S+\s+import\s+.*\b{re.escape(bound_name)}\b)"
        code_without_import = re.sub(pattern, "", code)

        # Word boundary check in remaining code
        if not re.search(rf"\b{re.escape(bound_name)}\b", code_without_import):
            issues.append(
                _issue(
                    "R013",
                    "info",
                    "UnusedImport",
                    f"Import '{full_import}' appears to be unused in this code snippet.",
                )
            )
    return issues
