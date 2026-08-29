"""
NeuroDebug Reproducible Evaluation Benchmark Dataset.

Contains real buggy Python snippets spanning deterministic syntax, semantic,
scope, typing, runtime, and algorithmic bug categories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkSnippet:
    """Benchmark test case for evaluation."""

    id: str
    name: str
    category: str
    expected_rule_id: str | None
    code: str
    expected_fixed_behavior: str
    test_code: str | None = None


BENCHMARK_DATASET: list[BenchmarkSnippet] = [
    # ── Category 1: Syntax Errors (R001) ───────────────────────────
    BenchmarkSnippet(
        id="SYN-01",
        name="Unclosed Parenthesis in Function Header",
        category="SyntaxError",
        expected_rule_id="R001",
        code="def add_numbers(a, b:\n    return a + b\n",
        expected_fixed_behavior="Syntax is valid and function compiles.",
    ),
    BenchmarkSnippet(
        id="SYN-02",
        name="Missing Colon in If Statement",
        category="SyntaxError",
        expected_rule_id="R001",
        code="x = 10\nif x > 5\n    print('greater')\n",
        expected_fixed_behavior="Colon added after conditional expression.",
    ),
    BenchmarkSnippet(
        id="SYN-03",
        name="Invalid Keyword in Assignment",
        category="SyntaxError",
        expected_rule_id="R001",
        code="class = 'Mathematics'\nprint(class)\n",
        expected_fixed_behavior="Variable renamed to not collide with keyword 'class'.",
    ),

    # ── Category 2: Undefined Variables (R002) ─────────────────────
    BenchmarkSnippet(
        id="UND-01",
        name="Undeclared Loop Counter",
        category="UndefinedVariable",
        expected_rule_id="R002",
        code="total = 0\nfor i in range(5):\n    total += count\n",
        expected_fixed_behavior="Uses loop variable 'i' instead of undefined 'count'.",
    ),
    BenchmarkSnippet(
        id="UND-02",
        name="Typo in Variable Name",
        category="UndefinedVariable",
        expected_rule_id="R002",
        code="user_name = 'Alice'\nprint(usr_name)\n",
        expected_fixed_behavior="Reference 'usr_name' corrected to 'user_name'.",
    ),
    BenchmarkSnippet(
        id="UND-03",
        name="Undeclared Function Call",
        category="UndefinedVariable",
        expected_rule_id="R002",
        code="val = compute_hash('data')\n",
        expected_fixed_behavior="Function defined or imported before call.",
    ),

    # ── Category 3: Return Outside Function (R003) ─────────────────
    BenchmarkSnippet(
        id="RET-01",
        name="Top-Level Return in Script",
        category="ReturnOutsideFunction",
        expected_rule_id="R003",
        code="x = 10\ny = 20\nreturn x + y\n",
        expected_fixed_behavior="Wrapped in function or replaced with print/variable.",
    ),
    BenchmarkSnippet(
        id="RET-02",
        name="Return in Module Body After Loop",
        category="ReturnOutsideFunction",
        expected_rule_id="R003",
        code="for i in range(3):\n    pass\nreturn i\n",
        expected_fixed_behavior="Return placed inside function scope.",
    ),

    # ── Category 4: Bare Except (R004) ─────────────────────────────
    BenchmarkSnippet(
        id="EXC-01",
        name="Bare Except Clause Catching All",
        category="BareExcept",
        expected_rule_id="R004",
        code="try:\n    num = int('invalid')\nexcept:\n    num = 0\n",
        expected_fixed_behavior="Catches specific 'ValueError' or 'Exception'.",
    ),
    BenchmarkSnippet(
        id="EXC-02",
        name="Bare Except in File Read",
        category="BareExcept",
        expected_rule_id="R004",
        code="try:\n    with open('f.txt') as f:\n        data = f.read()\nexcept:\n    data = ''\n",
        expected_fixed_behavior="Catches 'OSError' or 'FileNotFoundError'.",
    ),

    # ── Category 5: Mutable Default Arguments (R005) ───────────────
    BenchmarkSnippet(
        id="MUT-01",
        name="List as Default Parameter",
        category="MutableDefaultArgument",
        expected_rule_id="R005",
        code="def add_item(item, items=[]):\n    items.append(item)\n    return items\n",
        expected_fixed_behavior="Default is None; list initialized inside function.",
    ),
    BenchmarkSnippet(
        id="MUT-02",
        name="Dictionary as Default Parameter",
        category="MutableDefaultArgument",
        expected_rule_id="R005",
        code="def update_cache(key, val, cache={}):\n    cache[key] = val\n    return cache\n",
        expected_fixed_behavior="Default is None; dictionary initialized inside function.",
    ),
    BenchmarkSnippet(
        id="MUT-03",
        name="Set as Default Parameter",
        category="MutableDefaultArgument",
        expected_rule_id="R005",
        code="def register_user(uid, registered=set()):\n    registered.add(uid)\n    return registered\n",
        expected_fixed_behavior="Default is None; set initialized inside function.",
    ),

    # ── Category 6: Division By Zero (R006) ────────────────────────
    BenchmarkSnippet(
        id="DIV-01",
        name="Literal Float Division by Zero",
        category="DivisionByZero",
        expected_rule_id="R006",
        code="rate = 100.0 / 0\n",
        expected_fixed_behavior="Divisor checked or non-zero value provided.",
    ),
    BenchmarkSnippet(
        id="DIV-02",
        name="Modulo by Literal Zero",
        category="DivisionByZero",
        expected_rule_id="R006",
        code="rem = 42 % 0\n",
        expected_fixed_behavior="Valid non-zero modulo divisor.",
    ),

    # ── Category 7: Infinite Loops (R007) ──────────────────────────
    BenchmarkSnippet(
        id="INF-01",
        name="While True Without Break",
        category="InfiniteLoop",
        expected_rule_id="R007",
        code="counter = 0\nwhile True:\n    counter += 1\n",
        expected_fixed_behavior="Break condition or termination statement added.",
    ),
    BenchmarkSnippet(
        id="INF-02",
        name="Infinite Polling Loop",
        category="InfiniteLoop",
        expected_rule_id="R007",
        code="while True:\n    status = 'pending'\n",
        expected_fixed_behavior="Break condition when status changes or timeout added.",
    ),

    # ── Category 8: Python 2 Print (R008) ──────────────────────────
    BenchmarkSnippet(
        id="PRN-01",
        name="Print Statement with String",
        category="Python2Print",
        expected_rule_id="R008",
        code="print 'Hello from Python 2'\n",
        expected_fixed_behavior="Converted to print('Hello from Python 2').",
    ),
    BenchmarkSnippet(
        id="PRN-02",
        name="Print Statement with Variables",
        category="Python2Print",
        expected_rule_id="R008",
        code="val = 42\nprint val\n",
        expected_fixed_behavior="Converted to print(val).",
    ),

    # ── Category 9: Comparison with None (R009) ────────────────────
    BenchmarkSnippet(
        id="NON-01",
        name="Equality Check == None",
        category="NoneComparison",
        expected_rule_id="R009",
        code="val = None\nif val == None:\n    print('empty')\n",
        expected_fixed_behavior="Replaced with 'val is None'.",
    ),
    BenchmarkSnippet(
        id="NON-02",
        name="Inequality Check != None",
        category="NoneComparison",
        expected_rule_id="R009",
        code="data = {'a': 1}\nif data != None:\n    print('has data')\n",
        expected_fixed_behavior="Replaced with 'data is not None'.",
    ),

    # ── Category 10: Comparison with Bool (R010) ───────────────────
    BenchmarkSnippet(
        id="BOL-01",
        name="Equality Check == True",
        category="BoolComparison",
        expected_rule_id="R010",
        code="is_ready = True\nif is_ready == True:\n    print('ready')\n",
        expected_fixed_behavior="Replaced with 'if is_ready:' or 'is_ready is True'.",
    ),
    BenchmarkSnippet(
        id="BOL-02",
        name="Equality Check == False",
        category="BoolComparison",
        expected_rule_id="R010",
        code="has_failed = False\nif has_failed == False:\n    print('success')\n",
        expected_fixed_behavior="Replaced with 'if not has_failed:' or 'has_failed is False'.",
    ),

    # ── Category 11: Shadowed Builtins (R011) ──────────────────────
    BenchmarkSnippet(
        id="SHD-01",
        name="Shadowing Built-in list",
        category="ShadowedBuiltin",
        expected_rule_id="R011",
        code="list = [1, 2, 3]\nprint(list)\n",
        expected_fixed_behavior="Variable renamed to 'items' or 'my_list'.",
    ),
    BenchmarkSnippet(
        id="SHD-02",
        name="Shadowing Built-in dict",
        category="ShadowedBuiltin",
        expected_rule_id="R011",
        code="dict = {'a': 1}\nprint(dict)\n",
        expected_fixed_behavior="Variable renamed to 'mapping' or 'my_dict'.",
    ),
    BenchmarkSnippet(
        id="SHD-03",
        name="Shadowing Built-in sum",
        category="ShadowedBuiltin",
        expected_rule_id="R011",
        code="sum = 10 + 20\nprint(sum)\n",
        expected_fixed_behavior="Variable renamed to 'total' or 'sum_val'.",
    ),

    # ── Category 12: Silent Exceptions (R012) ──────────────────────
    BenchmarkSnippet(
        id="SIL-01",
        name="Except Block with Only Pass",
        category="SilentException",
        expected_rule_id="R012",
        code="try:\n    res = int('abc')\nexcept ValueError:\n    pass\n",
        expected_fixed_behavior="Exception logged or handled appropriately.",
    ),
    BenchmarkSnippet(
        id="SIL-02",
        name="Except Block with Ellipsis",
        category="SilentException",
        expected_rule_id="R012",
        code="try:\n    res = 1 / 0\nexcept ZeroDivisionError:\n    ...\n",
        expected_fixed_behavior="Exception logged or fallback assigned.",
    ),

    # ── Category 13: Unused Imports (R013) ─────────────────────────
    BenchmarkSnippet(
        id="IMP-01",
        name="Unused OS Module Import",
        category="UnusedImport",
        expected_rule_id="R013",
        code="import os\nimport sys\n\nprint(sys.version)\n",
        expected_fixed_behavior="Unused 'import os' removed.",
    ),
    BenchmarkSnippet(
        id="IMP-02",
        name="Unused Submodule Import",
        category="UnusedImport",
        expected_rule_id="R013",
        code="import json\nimport math\n\nx = math.sqrt(16)\nprint(x)\n",
        expected_fixed_behavior="Unused 'import json' removed.",
    ),

    # ── Category 14: Complex Mixed Logic & Edge Cases ──────────────
    BenchmarkSnippet(
        id="MIX-01",
        name="Multiple Issues (Undefined + Bare Except)",
        category="Mixed",
        expected_rule_id="R002",
        code="try:\n    val = undefined_source.get()\nexcept:\n    val = None\n",
        expected_fixed_behavior="Defined source and specific exception type.",
    ),
    BenchmarkSnippet(
        id="MIX-02",
        name="Mutable Default with Division Risk",
        category="Mixed",
        expected_rule_id="R005",
        code="def compute(val, divisors=[0]):\n    return val / divisors[0]\n",
        expected_fixed_behavior="Safe default and non-zero divisor.",
    ),
]
