"""
NeuroDebug — Backend Test Suite
Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

# Import after creating test .env
import os
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from main import app

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────────────────────────
def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# ──────────────────────────────────────────────────────────────────
# Empty input validation
# ──────────────────────────────────────────────────────────────────
def test_empty_code_returns_400():
    resp = client.post("/debug", json={"code": ""})
    assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────
# AST parser tests
# ──────────────────────────────────────────────────────────────────
from parser import analyze_code_ast

def test_parse_clean_code():
    code = "x = 1\nprint(x)\n"
    result = analyze_code_ast(code)
    assert result["success"] is True
    assert result["syntax_error"] is None

def test_parse_syntax_error():
    code = "def foo(\n    pass"
    result = analyze_code_ast(code)
    assert result["success"] is False
    assert result["syntax_error"] is not None

def test_detect_undefined_variable():
    code = "print(undefined_var)\n"
    result = analyze_code_ast(code)
    assert "undefined_var" in result["undefined_names"]

def test_detect_division_by_zero():
    code = "x = 10 / 0\n"
    result = analyze_code_ast(code)
    assert result["division_by_zero_risk"] is True

def test_detect_mutable_default():
    code = "def foo(items=[]):\n    items.append(1)\n    return items\n"
    result = analyze_code_ast(code)
    assert "foo" in result["mutable_defaults"]

def test_detect_infinite_loop():
    code = "while True:\n    print('hello')\n"
    result = analyze_code_ast(code)
    assert result["infinite_loop_risk"] is True

def test_infinite_loop_with_break_is_ok():
    code = "while True:\n    x = input()\n    if x == 'quit':\n        break\n"
    result = analyze_code_ast(code)
    assert result["infinite_loop_risk"] is False


# ──────────────────────────────────────────────────────────────────
# Rules engine tests
# ──────────────────────────────────────────────────────────────────
from rules import apply_rules

def test_rule_syntax_error():
    ast_r = {"success": False, "syntax_error": "SyntaxError at line 1: invalid syntax",
             "undefined_names": [], "return_outside_function": False,
             "bare_excepts": 0, "mutable_defaults": [], "division_by_zero_risk": False,
             "infinite_loop_risk": False, "imports": [], "variables": []}
    issues = apply_rules("", ast_r)
    assert any(i["rule_id"] == "R001" for i in issues)

def test_rule_none_comparison():
    code = "if x == None:\n    pass\n"
    ast_r = analyze_code_ast(code)
    issues = apply_rules(code, ast_r)
    assert any(i["rule_id"] == "R009" for i in issues)

def test_rule_bool_comparison():
    code = "if x == True:\n    pass\n"
    ast_r = analyze_code_ast(code)
    issues = apply_rules(code, ast_r)
    assert any(i["rule_id"] == "R010" for i in issues)

def test_no_issues_for_clean_code():
    code = """
def add(a: int, b: int) -> int:
    return a + b

result = add(2, 3)
print(result)
"""
    ast_r = analyze_code_ast(code)
    issues = apply_rules(code, ast_r)
    error_issues = [i for i in issues if i["severity"] == "error"]
    assert len(error_issues) == 0
