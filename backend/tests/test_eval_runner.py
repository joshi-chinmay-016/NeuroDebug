"""
Tests for Evaluation Runner and Honest Metrics Calculator.
"""

import pytest

from benchmarks.dataset import BENCHMARK_DATASET
from benchmarks.eval_runner import EvaluationRunner
from benchmarks.metrics import MetricsCalculator


@pytest.mark.asyncio
async def test_eval_runner_ast_only_mode():
    """Verify evaluation runner in ast_only mode."""
    runner = EvaluationRunner(dataset=BENCHMARK_DATASET[:5])
    report = await runner.run_evaluation(modes=["ast_only"])

    assert report.dataset_size == 5
    assert "ast_only" in report.modes
    ast_summary = report.modes["ast_only"]
    assert ast_summary.total_cases == 5
    assert ast_summary.avg_latency_ms > 0.0
    assert ast_summary.detection_rate > 0.0


@pytest.mark.asyncio
async def test_eval_runner_verification_mode():
    """Verify evaluation runner in ast_llm_verify mode."""
    # Test with syntax and mutable default cases that have test suites
    subset = [s for s in BENCHMARK_DATASET if s.id in ("SYN-01", "MUT-01")]
    runner = EvaluationRunner(dataset=subset)
    report = await runner.run_evaluation(modes=["ast_llm_verify"])

    assert "ast_llm_verify" in report.modes
    summary = report.modes["ast_llm_verify"]
    assert summary.total_cases == 2
    assert summary.patch_validity_rate == 100.0


def test_metrics_calculator_summary():
    """Test metric computations on mock case results."""
    mock_results = [
        {
            "case_id": "SYN-01",
            "category": "SyntaxError",
            "detected": True,
            "patch_generated": True,
            "patch_valid": True,
            "verification_status": "VERIFIED",
            "latency_ms": 10.5,
            "llm_calls": 1,
        },
        {
            "case_id": "RUN-01",
            "category": "RuntimeError",
            "detected": False,
            "patch_generated": False,
            "patch_valid": False,
            "verification_status": "UNVERIFIED",
            "latency_ms": 5.0,
            "llm_calls": 0,
        },
    ]
    summary = MetricsCalculator.compute_mode_summary("test_mode", mock_results)
    assert summary.total_cases == 2
    assert summary.detected_count == 1
    assert summary.detection_rate == 50.0
    assert summary.patch_validity_rate == 50.0
    assert summary.verified_fix_count == 1
    assert summary.verified_fix_rate == 50.0
    assert summary.avg_latency_ms == 7.75
    assert summary.total_llm_calls == 1
