"""
Tests for AST / LLM Agreement Signal Analyzer.
"""

from services.agreement_analyzer import AgreementAnalyzer, ConsensusStatus


def test_agreement_clean_consensus():
    """Verify clean consensus when both AST and LLM report no issues."""
    signal = AgreementAnalyzer.analyze_agreement(
        ast_result={"syntax_error": None},
        symbolic_issues=[],
        llm_analysis={"error_type": "Clean", "root_cause": "No errors found"},
    )
    assert signal.consensus_status == ConsensusStatus.CLEAN_CONSENSUS
    assert signal.agreement_score == 1.0
    assert signal.calibrated_confidence >= 0.95


def test_agreement_full_consensus():
    """Verify full consensus when both AST and LLM detect matching syntax/rule error."""
    ast_result = {"syntax_error": None}
    symbolic_issues = [{
        "rule_id": "R005",
        "category": "MutableDefaultArgument",
        "message": "Mutable default argument in function def",
        "line": 1,
    }]
    llm_analysis = {
        "error_type": "Mutable Default Argument",
        "root_cause": "Function uses mutable list as default argument",
        "line_number": 1,
        "confidence": 0.95,
    }

    signal = AgreementAnalyzer.analyze_agreement(ast_result, symbolic_issues, llm_analysis)
    assert signal.consensus_status == ConsensusStatus.FULL_CONSENSUS
    assert signal.agreement_score >= 0.90
    assert len(signal.matched_issues) == 1
    assert signal.calibrated_confidence >= 0.95


def test_agreement_llm_dominated_semantic_bug():
    """Verify LLM-dominated state for runtime/logic bugs beyond static AST rules."""
    ast_result = {"syntax_error": None}
    symbolic_issues = []
    llm_analysis = {
        "error_type": "IndexError",
        "root_cause": "Index out of range on empty list",
        "line_number": 2,
        "confidence": 0.85,
    }

    signal = AgreementAnalyzer.analyze_agreement(ast_result, symbolic_issues, llm_analysis)
    assert signal.consensus_status == ConsensusStatus.LLM_DOMINATED
    assert len(signal.llm_only_issues) == 1
    assert signal.calibrated_confidence > 0.70


def test_agreement_ast_dominated():
    """Verify AST-dominated state when AST flags syntax error but LLM misses it."""
    ast_result = {"syntax_error": "SyntaxError at line 1: '(' was never closed", "syntax_error_line": 1}
    symbolic_issues = []
    llm_analysis = {"error_type": "Clean", "root_cause": "Code looks good"}

    signal = AgreementAnalyzer.analyze_agreement(ast_result, symbolic_issues, llm_analysis)
    assert signal.consensus_status == ConsensusStatus.AST_DOMINATED
    assert signal.agreement_score < 0.30
    assert len(signal.ast_only_issues) == 1
