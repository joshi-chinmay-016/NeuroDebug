"""
Unit tests for the symbolic AST parser layer (backend/analysis/ast_parser.py).
"""

from analysis.ast_parser import analyze_code_ast


class TestASTParser:
    """Comprehensive test suite for AST parser analysis."""

    def test_parse_valid_code(self):
        """Test analysis of valid Python code."""
        code = "x = 1\ny = 2\nz = x + y\nprint(z)\n"
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert result["syntax_error"] is None
        assert result["syntax_error_line"] is None
        assert "x" in result["variables"]
        assert "y" in result["variables"]
        assert "z" in result["variables"]
        assert len(result["undefined_names"]) == 0

    def test_parse_syntax_error(self):
        """Test analysis with syntax error."""
        code = "def foo(\n    return 42"
        result = analyze_code_ast(code)
        assert result["success"] is False
        assert result["syntax_error"] is not None
        assert "SyntaxError" in result["syntax_error"]
        assert result["syntax_error_line"] is not None

    def test_detect_undefined_variable(self):
        """Test detection of an undefined variable."""
        code = "print(unknown_symbol)\n"
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert "unknown_symbol" in result["undefined_names"]
        assert result["undefined_name_lines"]["unknown_symbol"] == [1]

    def test_function_parameters_recognized_as_defined(self):
        """Test that function positional, keyword, vararg, and kwarg params are not undefined."""
        code = """
def calculate(a, b, *extra, scale=1.0, **metadata):
    total = (a + b + sum(extra)) * scale
    if "debug" in metadata:
        print(metadata["debug"])
    return total
"""
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert "calculate" in result["functions"]
        assert len(result["undefined_names"]) == 0

    def test_lambda_parameters_recognized(self):
        """Test that lambda parameters are recognized as defined."""
        code = "multiply = lambda x, y: x * y\nresult = multiply(2, 3)\n"
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert len(result["undefined_names"]) == 0

    def test_comprehension_variables_recognized(self):
        """Test that comprehension targets in list/dict/set/generator are defined."""
        code = """
items = [1, 2, 3]
squares = [x * x for x in items]
mapping = {k: v for k, v in enumerate(items)}
evens = {n for n in items if n % 2 == 0}
gen = (g * 2 for g in items)
"""
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert len(result["undefined_names"]) == 0

    def test_with_statement_target_recognized(self):
        """Test that context manager target variable is defined."""
        code = """
with open("test.txt") as fp:
    content = fp.read()
"""
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert len(result["undefined_names"]) == 0

    def test_except_handler_target_recognized(self):
        """Test that except clause alias (e) is defined."""
        code = """
try:
    x = 1 / 1
except Exception as err:
    print(err)
"""
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert len(result["undefined_names"]) == 0

    def test_walrus_operator_recognized(self):
        """Test that walrus operator := assigns variables in scope."""
        code = """
items = [1, 2, 3, 4]
if (n := len(items)) > 2:
    print(n)
"""
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert "n" in result["variables"]
        assert len(result["undefined_names"]) == 0

    def test_import_aliases_recognized(self):
        """Test that import aliases (as np, as p) are recognized as defined."""
        code = """
import numpy as np
from os.path import exists as file_exists

arr = np.zeros(5)
is_present = file_exists("data.csv")
"""
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert len(result["undefined_names"]) == 0

    def test_builtins_recognized(self):
        """Test that standard Python built-ins are recognized."""
        code = """
a = len([1, 2, 3])
b = sum([1, 2])
c = isinstance(a, int)
d = range(10)
e = any([True, False])
f = all([True, True])
g = abs(-5)
"""
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert len(result["undefined_names"]) == 0

    def test_detect_mutable_defaults(self):
        """Test detection of mutable default arguments in function definitions."""
        code = """
def append_item(item, target=[]):
    target.append(item)
    return target

def set_config(opts={}):
    return opts
"""
        result = analyze_code_ast(code)
        assert result["success"] is True
        assert "append_item" in result["mutable_defaults"]
        assert "set_config" in result["mutable_defaults"]
        assert len(result["mutable_default_details"]) == 2

    def test_detect_division_by_zero(self):
        """Test detection of literal division by zero."""
        code = "val = 10 / 0\n"
        result = analyze_code_ast(code)
        assert result["division_by_zero_risk"] is True
        assert result["division_by_zero_lines"] == [1]

    def test_detect_infinite_loop(self):
        """Test detection of while True loop without break."""
        code = """
while True:
    print("running forever")
"""
        result = analyze_code_ast(code)
        assert result["infinite_loop_risk"] is True
        assert result["infinite_loop_lines"] == [2]

    def test_infinite_loop_with_break_is_safe(self):
        """Test that while True with break is not flagged as infinite loop."""
        code = """
while True:
    if True:
        break
"""
        result = analyze_code_ast(code)
        assert result["infinite_loop_risk"] is False

    def test_detect_return_outside_function(self):
        """Test detection of top-level return statement."""
        code = "x = 10\nreturn x\n"
        result = analyze_code_ast(code)
        assert result["return_outside_function"] is True
        assert result["return_outside_function_lines"] == [2]

    def test_detect_bare_except(self):
        """Test detection of bare except: clause."""
        code = """
try:
    x = 1
except:
    pass
"""
        result = analyze_code_ast(code)
        assert result["bare_excepts"] == 1
        assert result["bare_except_lines"] == [4]
