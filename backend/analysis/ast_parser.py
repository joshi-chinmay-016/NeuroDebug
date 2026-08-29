"""
NeuroDebug — Symbolic Layer (AST Parser)

Statically analyses Python source code using the built-in `ast` module.
No code is ever executed — only the parse tree is inspected.
"""

from __future__ import annotations

import ast
from typing import Any

from utils.logging import get_logger

logger = get_logger("neurodebug.ast_parser")

# ──────────────────────────────────────────────────────────────────
# Python Built-in Identifiers
# ──────────────────────────────────────────────────────────────────

_BUILTINS: frozenset[str] = frozenset(
    {
        # Built-in functions
        "abs",
        "aiter",
        "all",
        "anext",
        "any",
        "ascii",
        "bin",
        "bool",
        "breakpoint",
        "bytearray",
        "bytes",
        "callable",
        "chr",
        "classmethod",
        "compile",
        "complex",
        "delattr",
        "dict",
        "dir",
        "divmod",
        "enumerate",
        "eval",
        "exec",
        "filter",
        "float",
        "format",
        "frozenset",
        "getattr",
        "globals",
        "hasattr",
        "hash",
        "help",
        "hex",
        "id",
        "input",
        "int",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "list",
        "locals",
        "map",
        "max",
        "memoryview",
        "min",
        "next",
        "object",
        "oct",
        "open",
        "ord",
        "pow",
        "print",
        "property",
        "range",
        "repr",
        "reversed",
        "round",
        "set",
        "setattr",
        "slice",
        "sorted",
        "staticmethod",
        "str",
        "sum",
        "super",
        "tuple",
        "type",
        "vars",
        "zip",
        "__import__",
        # Built-in constants
        "None",
        "True",
        "False",
        "Ellipsis",
        "NotImplemented",
        "__debug__",
        "__name__",
        "__file__",
        "__doc__",
        "__package__",
        "__annotations__",
        # Common exceptions
        "ArithmeticError",
        "AssertionError",
        "AttributeError",
        "BaseException",
        "BlockingIOError",
        "BrokenPipeError",
        "BufferError",
        "BytesWarning",
        "ChildProcessError",
        "ConnectionAbortedError",
        "ConnectionError",
        "ConnectionRefusedError",
        "ConnectionResetError",
        "DeprecationWarning",
        "EOFError",
        "EncodingWarning",
        "EnvironmentError",
        "Exception",
        "FileExistsError",
        "FileNotFoundError",
        "FloatingPointError",
        "FutureWarning",
        "GeneratorExit",
        "IOError",
        "ImportError",
        "ImportWarning",
        "IndentationError",
        "IndexError",
        "InterruptedError",
        "IsADirectoryError",
        "KeyError",
        "KeyboardInterrupt",
        "LookupError",
        "MemoryError",
        "ModuleNotFoundError",
        "NameError",
        "NotADirectoryError",
        "NotImplementedError",
        "OSError",
        "OverflowError",
        "PendingDeprecationWarning",
        "PermissionError",
        "ProcessLookupError",
        "RecursionError",
        "ReferenceError",
        "ResourceWarning",
        "RuntimeError",
        "RuntimeWarning",
        "StopAsyncIteration",
        "StopIteration",
        "SyntaxError",
        "SyntaxWarning",
        "SystemError",
        "SystemExit",
        "TabError",
        "TimeoutError",
        "TypeError",
        "UnboundLocalError",
        "UnicodeDecodeError",
        "UnicodeEncodeError",
        "UnicodeError",
        "UnicodeTranslateError",
        "UnicodeWarning",
        "UserWarning",
        "ValueError",
        "Warning",
        "ZeroDivisionError",
        # Method receivers & conventions
        "self",
        "cls",
    }
)


# ──────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────


def analyze_code_ast(code: str) -> dict[str, Any]:
    """
    Parse `code` and return a structured analysis dict.

    Returns
    -------
    {
        "success": bool,
        "syntax_error": str | None,
        "syntax_error_line": int | None,
        "tree": ast.Module | None,
        "imports": list[str],
        "import_aliases": dict[str, str],
        "functions": list[str],
        "classes": list[str],
        "variables": list[str],
        "variable_lines": dict[str, list[int]],
        "undefined_names": list[str],
        "undefined_name_lines": dict[str, list[int]],
        "return_outside_function": bool,
        "return_outside_function_lines": list[int],
        "bare_excepts": int,
        "bare_except_lines": list[int],
        "mutable_defaults": list[str],
        "mutable_default_details": list[dict[str, Any]],
        "division_by_zero_risk": bool,
        "division_by_zero_lines": list[int],
        "infinite_loop_risk": bool,
        "infinite_loop_lines": list[int],
        "comparison_with_none_lines": list[int],
        "comparison_with_bool_lines": list[int],
        "empty_except_lines": list[int],
    }
    """
    result: dict[str, Any] = {
        "success": False,
        "syntax_error": None,
        "syntax_error_line": None,
        "tree": None,
        "imports": [],
        "import_aliases": {},
        "functions": [],
        "classes": [],
        "variables": [],
        "variable_lines": {},
        "undefined_names": [],
        "undefined_name_lines": {},
        "return_outside_function": False,
        "return_outside_function_lines": [],
        "bare_excepts": 0,
        "bare_except_lines": [],
        "mutable_defaults": [],
        "mutable_default_details": [],
        "division_by_zero_risk": False,
        "division_by_zero_lines": [],
        "infinite_loop_risk": False,
        "infinite_loop_lines": [],
        "comparison_with_none_lines": [],
        "comparison_with_bool_lines": [],
        "empty_except_lines": [],
    }

    # ── Attempt to parse ──────────────────────────────────────────
    try:
        tree = ast.parse(code)
        result["tree"] = tree
        result["success"] = True
    except SyntaxError as exc:
        result["syntax_error"] = f"SyntaxError at line {exc.lineno}: {exc.msg}"
        result["syntax_error_line"] = exc.lineno
        logger.warning("Syntax error: %s", result["syntax_error"])
        return result

    # ── Walk the AST ─────────────────────────────────────────────
    visitor = _ASTVisitor()
    visitor.visit(tree)

    result["imports"] = visitor.imports
    result["import_aliases"] = visitor.import_aliases
    result["functions"] = visitor.functions
    result["classes"] = visitor.classes
    result["variables"] = sorted(visitor.assignments)
    result["variable_lines"] = visitor.variable_lines

    undefined_names, undefined_lines = _find_undefined_names(tree, visitor)
    result["undefined_names"] = undefined_names
    result["undefined_name_lines"] = undefined_lines

    result["return_outside_function"] = visitor.return_outside_function
    result["return_outside_function_lines"] = visitor.return_outside_function_lines
    result["bare_excepts"] = visitor.bare_excepts
    result["bare_except_lines"] = visitor.bare_except_lines
    result["mutable_defaults"] = visitor.mutable_defaults
    result["mutable_default_details"] = visitor.mutable_default_details
    result["division_by_zero_risk"] = visitor.division_by_zero_risk
    result["division_by_zero_lines"] = visitor.division_by_zero_lines
    result["infinite_loop_risk"] = visitor.infinite_loop_risk
    result["infinite_loop_lines"] = visitor.infinite_loop_lines
    result["comparison_with_none_lines"] = sorted(visitor.comparison_with_none_lines)
    result["comparison_with_bool_lines"] = sorted(visitor.comparison_with_bool_lines)
    result["empty_except_lines"] = sorted(visitor.empty_except_lines)

    logger.debug(
        "AST analysis OK: %d functions, %d classes, %d undefined names",
        len(result["functions"]),
        len(result["classes"]),
        len(result["undefined_names"]),
    )
    return result


# ──────────────────────────────────────────────────────────────────
# Internal Visitor
# ──────────────────────────────────────────────────────────────────


class _ASTVisitor(ast.NodeVisitor):
    """Collect structural information from the AST with line numbers."""

    def __init__(self) -> None:
        self.imports: list[str] = []
        self.import_aliases: dict[str, str] = {}
        self.functions: list[str] = []
        self.classes: list[str] = []
        self.assignments: set[str] = set()
        self.variable_lines: dict[str, list[int]] = {}
        self.used_names: dict[str, list[int]] = {}
        self.return_outside_function: bool = False
        self.return_outside_function_lines: list[int] = []
        self.bare_excepts: int = 0
        self.bare_except_lines: list[int] = []
        self.mutable_defaults: list[str] = []
        self.mutable_default_details: list[dict[str, Any]] = []
        self.division_by_zero_risk: bool = False
        self.division_by_zero_lines: list[int] = []
        self.infinite_loop_risk: bool = False
        self.infinite_loop_lines: list[int] = []
        self.comparison_with_none_lines: set[int] = set()
        self.comparison_with_bool_lines: set[int] = set()
        self.empty_except_lines: set[int] = set()
        self._function_depth: int = 0

    # ── imports ──────────────────────────────────────────────────
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
            bound_name = alias.asname or alias.name.split(".")[0]
            self.import_aliases[bound_name] = alias.name
            self.assignments.add(bound_name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(full_name)
            bound_name = alias.asname or alias.name
            self.import_aliases[bound_name] = full_name
            self.assignments.add(bound_name)
        self.generic_visit(node)

    # ── function defs ─────────────────────────────────────────────
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        self.assignments.add(node.name)
        self._check_mutable_defaults(node)
        self._function_depth += 1
        self.generic_visit(node)
        self._function_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.functions.append(node.name)
        self.assignments.add(node.name)
        self._check_mutable_defaults(node)
        self._function_depth += 1
        self.generic_visit(node)
        self._function_depth -= 1

    def _check_mutable_defaults(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        mutable_types = (ast.List, ast.Dict, ast.Set)
        # Check positional and keyword defaults
        all_defaults = list(node.args.defaults) + [
            d for d in node.args.kw_defaults if d is not None
        ]
        for default in all_defaults:
            is_mutable = isinstance(default, mutable_types) or (
                isinstance(default, ast.Call)
                and isinstance(default.func, ast.Name)
                and default.func.id in ("list", "dict", "set")
            )
            if is_mutable:
                if node.name not in self.mutable_defaults:
                    self.mutable_defaults.append(node.name)
                self.mutable_default_details.append(
                    {
                        "function_name": node.name,
                        "line": getattr(default, "lineno", node.lineno),
                    }
                )

    # ── class defs ───────────────────────────────────────────────
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        self.assignments.add(node.name)
        self.generic_visit(node)

    # ── assignments ──────────────────────────────────────────────
    def _record_assignment(self, name: str, lineno: int | None) -> None:
        self.assignments.add(name)
        if lineno is not None:
            self.variable_lines.setdefault(name, []).append(lineno)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._extract_target_names(target, getattr(node, "lineno", None))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._extract_target_names(node.target, getattr(node, "lineno", None))
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._extract_target_names(node.target, getattr(node, "lineno", None))
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        # Walrus operator :=
        self._extract_target_names(node.target, getattr(node, "lineno", None))
        self.generic_visit(node)

    def _extract_target_names(self, node: ast.AST, lineno: int | None) -> None:
        if isinstance(node, ast.Name):
            self._record_assignment(node.id, lineno)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                self._extract_target_names(elt, lineno)
        elif isinstance(node, ast.Starred):
            self._extract_target_names(node.value, lineno)

    # ── name usage ───────────────────────────────────────────────
    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            lineno = getattr(node, "lineno", 1)
            self.used_names.setdefault(node.id, []).append(lineno)
        self.generic_visit(node)

    # ── return outside function ───────────────────────────────────
    def visit_Return(self, node: ast.Return) -> None:
        if self._function_depth == 0:
            self.return_outside_function = True
            self.return_outside_function_lines.append(getattr(node, "lineno", 1))
        self.generic_visit(node)

    # ── except handler ───────────────────────────────────────────
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        lineno = getattr(node, "lineno", 1)
        if node.type is None:
            self.bare_excepts += 1
            self.bare_except_lines.append(lineno)

        # Check for empty except body (silent exception swallowing)
        if self._is_empty_or_pass_body(node.body):
            self.empty_except_lines.add(lineno)

        self.generic_visit(node)

    @staticmethod
    def _is_empty_or_pass_body(body: list[ast.stmt]) -> bool:
        if not body:
            return True
        if len(body) == 1:
            first = body[0]
            if isinstance(first, ast.Pass):
                return True
            # Expression with Ellipsis: ...
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and first.value.value is Ellipsis
            ):
                return True
        return False

    # ── division by zero ─────────────────────────────────────────
    def visit_BinOp(self, node: ast.BinOp) -> None:
        if (
            isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod))
            and isinstance(node.right, ast.Constant)
            and node.right.value == 0
        ):
            self.division_by_zero_risk = True
            self.division_by_zero_lines.append(getattr(node, "lineno", 1))
        self.generic_visit(node)

    # ── comparisons (== None, == True/False) ─────────────────────
    def visit_Compare(self, node: ast.Compare) -> None:
        lineno = getattr(node, "lineno", 1)
        all_values = [node.left] + list(node.comparators)
        for op in node.ops:
            if isinstance(op, (ast.Eq, ast.NotEq)):
                for val in all_values:
                    if isinstance(val, ast.Constant):
                        if val.value is None:
                            self.comparison_with_none_lines.add(lineno)
                        elif isinstance(val.value, bool):
                            self.comparison_with_bool_lines.add(lineno)
        self.generic_visit(node)

    # ── infinite while True ──────────────────────────────────────
    def visit_While(self, node: ast.While) -> None:
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            # Check if there's a break somewhere inside (excluding nested loops)
            has_break = self._has_direct_break(node.body) or self._has_direct_break(
                node.orelse
            )
            if not has_break:
                self.infinite_loop_risk = True
                self.infinite_loop_lines.append(getattr(node, "lineno", 1))
        self.generic_visit(node)

    @classmethod
    def _has_direct_break(cls, stmts: list[ast.stmt]) -> bool:
        for stmt in stmts:
            if isinstance(stmt, ast.Break):
                return True
            if isinstance(stmt, (ast.If, ast.Try, ast.With, ast.ExceptHandler)):
                for child in ast.iter_child_nodes(stmt):
                    if isinstance(child, list):
                        if cls._has_direct_break(child):
                            return True
                    elif isinstance(child, ast.Break):
                        return True
            # For nested loops, breaks belong to the inner loop
        return False


# ──────────────────────────────────────────────────────────────────
# Scope-Aware Undefined-Name Detection
# ──────────────────────────────────────────────────────────────────


def _find_undefined_names(
    tree: ast.Module, visitor: _ASTVisitor
) -> tuple[list[str], dict[str, list[int]]]:
    """
    Return sorted names and their line occurrences that are *used* but not *defined*.

    Handles:
    - Function arguments (posonly, regular, vararg, kwonly, kwarg)
    - Lambda arguments
    - Loop variables (for, comprehension)
    - Context managers (with)
    - Exception handlers (except ... as e)
    - Walrus operator bindings
    - Imports and import aliases
    - Built-in functions and constants
    """
    defined: set[str] = set(visitor.assignments) | set(visitor.functions) | set(visitor.classes) | _BUILTINS

    for bound_name in visitor.import_aliases:
        defined.add(bound_name)

    # Walk tree to gather all parameter and scope-defined names
    for node in ast.walk(tree):
        # 1. Function parameters
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            args = node.args
            for arg in (
                args.posonlyargs
                + args.args
                + args.kwonlyargs
                + ([args.vararg] if args.vararg else [])
                + ([args.kwarg] if args.kwarg else [])
            ):
                defined.add(arg.arg)

        # 2. For loops & comprehensions
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name):
                    defined.add(n.id)

        # 3. With statement items
        elif isinstance(node, ast.withitem):
            if node.optional_vars:
                for n in ast.walk(node.optional_vars):
                    if isinstance(n, ast.Name):
                        defined.add(n.id)

        # 4. Except handler variable
        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                defined.add(node.name)

        # 5. Global and nonlocal declarations
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                defined.add(name)

        # 6. Pattern matching (Python 3.10+)
        elif hasattr(ast, "MatchAs") and isinstance(node, ast.MatchAs):
            if node.name:
                defined.add(node.name)
        elif hasattr(ast, "MatchStar") and isinstance(node, ast.MatchStar):
            if node.name:
                defined.add(node.name)

    undefined_set = set(visitor.used_names.keys()) - defined
    sorted_undefined = sorted(undefined_set)
    undefined_lines = {name: visitor.used_names[name] for name in sorted_undefined}

    return sorted_undefined, undefined_lines
