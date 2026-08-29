"""
Unit and integration tests for the evaluation benchmark runner and dataset.
"""

from benchmarks.benchmark_runner import BenchmarkRunner
from benchmarks.dataset import BENCHMARK_DATASET


class TestBenchmarkEvaluation:
    """Test suite for reproducible evaluation benchmarks."""

    def test_benchmark_dataset_integrity(self):
        """Verify dataset size, distribution, and property completeness."""
        assert len(BENCHMARK_DATASET) >= 30
        categories = set()
        for snippet in BENCHMARK_DATASET:
            assert snippet.id
            assert snippet.name
            assert snippet.category
            assert snippet.code
            assert snippet.expected_fixed_behavior
            assert snippet.difficulty in ("easy", "medium", "hard")
            categories.add(snippet.category)

        # Must span across multiple representative bug categories
        assert len(categories) >= 7

    def test_deterministic_benchmark_execution(self):
        """Run benchmark runner and assert deterministic subset detection performance."""
        runner = BenchmarkRunner()
        summary = runner.run_deterministic_evaluation()

        assert summary.total_cases == len(BENCHMARK_DATASET)
        assert summary.successful_detections >= 20
        assert summary.avg_ast_duration_ms > 0.0
        assert summary.avg_rule_duration_ms > 0.0
        assert summary.avg_total_duration_ms < 50.0  # Must be sub-50ms deterministic speed
