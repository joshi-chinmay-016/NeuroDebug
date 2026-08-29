"""
Unit tests for the deterministic symbolic rule engine (backend/analysis/rule_engine.py).
Tests all 13 rules (R001 — R013) for positive and negative cases.
"""

from analysis.ast_parser import analyze_code_ast
from analysis.rule_engine import apply_rules


class TestRuleEngine:
    """Comprehensive test suite for symbolic rules R001 to R013."""

    def test_clean_code_no_rules_triggered(self):
        """Test that well-formed Python code triggers zero issues."""
        code = """
import math

def calculate_hypotenuse(a: float, b: float) -> float:
    return math.sqrt(a ** 2 + b ** 2)

result = calculate_hypotenuse(3.0, 4.0)
print(result)
"""
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        assert len(issues) == 0

    def test_r001_syntax_error(self):
        """Test R001: Syntax Error detection."""
        code = "def broken(\n    pass"
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r001 = [i for i in issues if i["rule_id"] == "R001"]
        assert len(r001) == 1
        assert r001[0]["severity"] == "error"
        assert r001[0]["category"] == "SyntaxError"

    def test_r002_undefined_variable(self):
        """Test R002: Undefined variable reference."""
        code = "print(non_existent_var)\n"
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r002 = [i for i in issues if i["rule_id"] == "R002"]
        assert len(r002) == 1
        assert r002[0]["severity"] == "error"
        assert "non_existent_var" in r002[0]["message"]

    def test_r003_return_outside_function(self):
        """Test R003: Return statement outside function."""
        code = "x = 42\nreturn x\n"
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r003 = [i for i in issues if i["rule_id"] == "R003"]
        assert len(r003) == 1
        assert r003[0]["severity"] == "error"
        assert r003[0]["category"] == "ReturnOutsideFunction"

    def test_r004_bare_except(self):
        """Test R004: Bare except clause."""
        code = """
try:
    val = int("abc")
except:
    val = 0
"""
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r004 = [i for i in issues if i["rule_id"] == "R004"]
        assert len(r004) == 1
        assert r004[0]["severity"] == "warning"
        assert r004[0]["category"] == "BareExcept"

    def test_r005_mutable_default(self):
        """Test R005: Mutable default argument."""
        code = """
def add_item(item, basket=[]):
    basket.append(item)
    return basket
"""
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r005 = [i for i in issues if i["rule_id"] == "R005"]
        assert len(r005) == 1
        assert r005[0]["severity"] == "warning"
        assert r005[0]["category"] == "MutableDefaultArgument"

    def test_r006_division_by_zero(self):
        """Test R006: Literal division by zero."""
        code = "result = 100 / 0\n"
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r006 = [i for i in issues if i["rule_id"] == "R006"]
        assert len(r006) == 1
        assert r006[0]["severity"] == "error"
        assert r006[0]["category"] == "DivisionByZero"

    def test_r007_infinite_loop(self):
        """Test R007: Infinite while True loop without break."""
        code = """
while True:
    print("tick")
"""
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r007 = [i for i in issues if i["rule_id"] == "R007"]
        assert len(r007) == 1
        assert r007[0]["severity"] == "warning"
        assert r007[0]["category"] == "InfiniteLoop"

    def test_r008_python2_print(self):
        """Test R008: Python 2-style print without parentheses."""
        code = 'print "Hello World"\n'
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r008 = [i for i in issues if i["rule_id"] == "R008"]
        assert len(r008) == 1
        assert r008[0]["severity"] == "warning"
        assert r008[0]["category"] == "Python2Print"

    def test_r009_none_comparison(self):
        """Test R009: Equality comparison with None."""
        code = """
x = None
if x == None:
    print("is none")
"""
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r009 = [i for i in issues if i["rule_id"] == "R009"]
        assert len(r009) == 1
        assert r009[0]["severity"] == "warning"
        assert r009[0]["category"] == "NoneComparison"

    def test_r010_bool_comparison(self):
        """Test R010: Equality comparison with True or False."""
        code = """
flag = True
if flag == True:
    print("flag is true")
"""
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r010 = [i for i in issues if i["rule_id"] == "R010"]
        assert len(r010) == 1
        assert r010[0]["severity"] == "warning"
        assert r010[0]["category"] == "BoolComparison"

    def test_r011_shadowed_builtin(self):
        """Test R011: Shadowing built-in names."""
        code = "list = [1, 2, 3]\nprint(list)\n"
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r011 = [i for i in issues if i["rule_id"] == "R011"]
        assert len(r011) == 1
        assert r011[0]["severity"] == "warning"
        assert r011[0]["category"] == "ShadowedBuiltin"

    def test_r012_silent_exception(self):
        """Test R012: Silent exception swallowing."""
        code = """
try:
    x = int("invalid")
except ValueError:
    pass
"""
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r012 = [i for i in issues if i["rule_id"] == "R012"]
        assert len(r012) == 1
        assert r012[0]["severity"] == "warning"
        assert r012[0]["category"] == "SilentException"

    def test_r013_unused_import(self):
        """Test R013: Unused import statement."""
        code = """
import os
import sys

print(sys.version)
"""
        ast_result = analyze_code_ast(code)
        issues = apply_rules(code, ast_result)
        r013 = [i for i in issues if i["rule_id"] == "R013"]
        assert len(r013) == 1
        assert r013[0]["severity"] == "info"
        assert r013[0]["category"] == "UnusedImport"
        assert "os" in r013[0]["message"]
