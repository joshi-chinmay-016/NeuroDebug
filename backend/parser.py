"""
NeuroDebug — Symbolic Layer (AST Parser)

Statically analyses Python source code using the built-in `ast` module.
No code is ever executed — only the parse tree is inspected.
"""

import ast
import logging
from typing import Any

logger = logging.getLogger("neurodebug.parser")


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
        "tree": ast.Module | None,
        "imports": list[str],
        "functions": list[str],
        "classes": list[str],
        "variables": list[str],
        "undefined_names": list[str],
        "return_outside_function": bool,
        "bare_excepts": int,
        "mutable_defaults": list[str],
        "division_by_zero_risk": bool,
        "infinite_loop_risk": bool,
    }
    """
    result: dict[str, Any] = {
        "success": False,
        "syntax_error": None,
        "tree": None,
        "imports": [],
        "functions": [],
        "classes": [],
        "variables": [],
        "undefined_names": [],
        "return_outside_function": False,
        "bare_excepts": 0,
        "mutable_defaults": [],
        "division_by_zero_risk": False,
        "infinite_loop_risk": False,
    }

    # ── Attempt to parse ──────────────────────────────────────────
    try:
        tree = ast.parse(code)
        result["tree"] = tree
        result["success"] = True
    except SyntaxError as exc:
        result["syntax_error"] = f"SyntaxError at line {exc.lineno}: {exc.msg}"
        logger.warning("Syntax error: %s", result["syntax_error"])
        return result

    # ── Walk the AST ─────────────────────────────────────────────
    visitor = _ASTVisitor()
    visitor.visit(tree)

    result["imports"]               = visitor.imports
    result["functions"]             = visitor.functions
    result["classes"]               = visitor.classes
    result["variables"]             = list(visitor.assignments)
    result["undefined_names"]       = _find_undefined_names(tree, visitor)
    result["return_outside_function"] = visitor.return_outside_function
    result["bare_excepts"]          = visitor.bare_excepts
    result["mutable_defaults"]      = visitor.mutable_defaults
    result["division_by_zero_risk"] = visitor.division_by_zero_risk
    result["infinite_loop_risk"]    = visitor.infinite_loop_risk

    logger.debug("AST analysis OK: %d functions, %d classes", len(result["functions"]), len(result["classes"]))
    return result


# ──────────────────────────────────────────────────────────────────
# Internal visitor
# ──────────────────────────────────────────────────────────────────

class _ASTVisitor(ast.NodeVisitor):
    """Collect structural information from the AST."""

    def __init__(self):
        self.imports:               list[str] = []
        self.functions:             list[str] = []
        self.classes:               list[str] = []
        self.assignments:           set[str]  = set()
        self.parameters:            set[str]  = set()
        self.used_names:            set[str]  = set()
        self.return_outside_function: bool    = False
        self.bare_excepts:          int       = 0
        self.mutable_defaults:      list[str] = []
        self.division_by_zero_risk: bool      = False
        self.infinite_loop_risk:    bool      = False
        self._function_depth:       int       = 0

    # ── imports ──────────────────────────────────────────────────
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)

    # ── function defs ─────────────────────────────────────────────
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.functions.append(node.name)
        self._collect_parameters(node)
        self._check_mutable_defaults(node)
        self._function_depth += 1
        self.generic_visit(node)
        self._function_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef  # handle async too

    def _collect_parameters(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        args = [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]
        if node.args.vararg:
            args.append(node.args.vararg)
        if node.args.kwarg:
            args.append(node.args.kwarg)

        for arg in args:
            self.parameters.add(arg.arg)

    def _check_mutable_defaults(self, node):
        mutable_types = (ast.List, ast.Dict, ast.Set)
        for default in node.args.defaults + node.args.kw_defaults:
            if default and isinstance(default, mutable_types):
                self.mutable_defaults.append(node.name)

    # ── class defs ───────────────────────────────────────────────
    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.append(node.name)
        self.generic_visit(node)

    # ── assignments ──────────────────────────────────────────────
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assignments.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self.assignments.add(node.target.id)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        if isinstance(node.target, ast.Name):
            self.assignments.add(node.target.id)
        self.generic_visit(node)

    # ── name usage ───────────────────────────────────────────────
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    # ── return outside function ───────────────────────────────────
    def visit_Return(self, node: ast.Return):
        if self._function_depth == 0:
            self.return_outside_function = True
        self.generic_visit(node)

    # ── bare except ──────────────────────────────────────────────
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.bare_excepts += 1
        self.generic_visit(node)

    # ── division by zero ─────────────────────────────────────────
    def visit_BinOp(self, node: ast.BinOp):
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                self.division_by_zero_risk = True
        self.generic_visit(node)

    # ── infinite while True ──────────────────────────────────────
    def visit_While(self, node: ast.While):
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            # Check if there's a break somewhere inside
            has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
            if not has_break:
                self.infinite_loop_risk = True
        self.generic_visit(node)


# ──────────────────────────────────────────────────────────────────
# Undefined-name detection
# ──────────────────────────────────────────────────────────────────

_BUILTINS = {
    # built-in functions
    "print", "len", "range", "type", "isinstance", "issubclass",
    "int", "float", "str", "bool", "list", "dict", "set", "tuple",
    "input", "open", "enumerate", "zip", "map", "filter", "sorted",
    "reversed", "sum", "min", "max", "abs", "round", "pow", "divmod",
    "hex", "oct", "bin", "ord", "chr", "id", "hash", "repr", "vars",
    "dir", "getattr", "setattr", "hasattr", "delattr", "callable",
    "iter", "next", "any", "all", "format", "super", "object", "property",
    "staticmethod", "classmethod",
    # constants / special names
    "None", "True", "False", "__name__", "__file__", "__doc__",
    "NotImplemented", "Ellipsis",
    # common exceptions
    "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
    "AttributeError", "NameError", "RuntimeError", "StopIteration",
    "GeneratorExit", "SystemExit", "KeyboardInterrupt", "ImportError",
    "FileNotFoundError", "OSError", "IOError", "OverflowError",
    "ZeroDivisionError", "MemoryError", "RecursionError", "NotImplementedError",
    # other globals often present
    "self", "cls",
}


def _find_undefined_names(tree: ast.Module, visitor: _ASTVisitor) -> list[str]:
    """
    Return names that are *used* but not *defined* in the snippet.
    This is a heuristic — imports, function names, class names, and
    builtins are all treated as defined.
    """
    defined = (
        visitor.assignments
        | visitor.parameters
        | set(visitor.functions)
        | set(visitor.classes)
        | _BUILTINS
        | {alias.split(".")[-1] for alias in visitor.imports}
    )

    # Also treat for-loop variables as defined
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.comprehension)):
            target = node.target if isinstance(node, ast.For) else node.target
            for n in ast.walk(target):
                if isinstance(n, ast.Name):
                    defined.add(n.id)
        elif isinstance(node, ast.withitem):
            if node.optional_vars and isinstance(node.optional_vars, ast.Name):
                defined.add(node.optional_vars.id)
        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                defined.add(node.name)

    undefined = visitor.used_names - defined
    return sorted(undefined)
