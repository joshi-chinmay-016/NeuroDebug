"""
NeuroDebug Reproducible Evaluation Benchmark Runner.

Executes deterministic AST and symbolic rule engine evaluations against the
benchmark dataset, recording real detection accuracy, per-category precision,
and pipeline latencies without fabricated data.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from analysis.ast_parser import analyze_code_ast
from analysis.rule_engine import apply_rules
from benchmarks.dataset import BENCHMARK_DATASET, BenchmarkSnippet


@dataclass
class BenchmarkResult:
    """Result of running benchmark on a single snippet."""

    snippet_id: str
    name: str
    category: str
    expected_rule: str | None
    detected_rule_ids: list[str]
    detected_categories: list[str]
    detected: bool
    ast_duration_ms: float
    rule_duration_ms: float
    issues: list[dict[str, Any]]


@dataclass
class BenchmarkSummary:
    """Aggregated evaluation metrics across the benchmark suite."""

    total_cases: int = 0
    successful_detections: int = 0
    detection_rate: float = 0.0
    avg_ast_duration_ms: float = 0.0
    avg_rule_duration_ms: float = 0.0
    avg_total_duration_ms: float = 0.0
    category_breakdown: dict[str, dict[str, int]] = field(default_factory=dict)
    results: list[BenchmarkResult] = field(default_factory=list)


class BenchmarkRunner:
    """Runner for reproducible evaluation."""

    def __init__(self, dataset: list[BenchmarkSnippet] | None = None) -> None:
        self.dataset = dataset or BENCHMARK_DATASET

    def run_deterministic_evaluation(self) -> BenchmarkSummary:
        """Run deterministic evaluation pass on all benchmark snippets."""
        summary = BenchmarkSummary(total_cases=len(self.dataset))
        total_ast_time = 0.0
        total_rule_time = 0.0

        for snippet in self.dataset:
            # 1. Measure AST parsing
            t0 = time.perf_counter()
            ast_result = analyze_code_ast(snippet.code)
            t1 = time.perf_counter()
            ast_ms = (t1 - t0) * 1000

            # 2. Measure Rule Engine
            t2 = time.perf_counter()
            issues = apply_rules(snippet.code, ast_result)
            t3 = time.perf_counter()
            rule_ms = (t3 - t2) * 1000

            total_ast_time += ast_ms
            total_rule_time += rule_ms

            detected_rule_ids = [i["rule_id"] for i in issues]
            detected_categories = [i["category"] for i in issues]

            # Check if expected rule was detected
            if snippet.expected_rule_id:
                detected = snippet.expected_rule_id in detected_rule_ids
            else:
                detected = len(issues) > 0

            if detected:
                summary.successful_detections += 1

            # Category tracking
            cat_stats = summary.category_breakdown.setdefault(
                snippet.category, {"total": 0, "detected": 0}
            )
            cat_stats["total"] += 1
            if detected:
                cat_stats["detected"] += 1

            summary.results.append(
                BenchmarkResult(
                    snippet_id=snippet.id,
                    name=snippet.name,
                    category=snippet.category,
                    expected_rule=snippet.expected_rule_id,
                    detected_rule_ids=detected_rule_ids,
                    detected_categories=detected_categories,
                    detected=detected,
                    ast_duration_ms=round(ast_ms, 3),
                    rule_duration_ms=round(rule_ms, 3),
                    issues=issues,
                )
            )

        if summary.total_cases > 0:
            summary.detection_rate = round(
                (summary.successful_detections / summary.total_cases) * 100, 2
            )
            summary.avg_ast_duration_ms = round(
                total_ast_time / summary.total_cases, 3
            )
            summary.avg_rule_duration_ms = round(
                total_rule_time / summary.total_cases, 3
            )
            summary.avg_total_duration_ms = round(
                (total_ast_time + total_rule_time) / summary.total_cases, 3
            )

        return summary


def run_cli_benchmark() -> None:
    """CLI helper to execute and display benchmark results."""
    runner = BenchmarkRunner()
    summary = runner.run_deterministic_evaluation()

    print("\n" + "=" * 60)
    print("  NeuroDebug Deterministic Layer Benchmark Evaluation")
    print("=" * 60)
    print(f"Total Snippets Evaluated: {summary.total_cases}")
    print(f"Successful Detections:   {summary.successful_detections}")
    print(f"Overall Detection Rate:  {summary.detection_rate}%")
    print(f"Avg AST Parse Latency:   {summary.avg_ast_duration_ms:.3f} ms")
    print(f"Avg Rule Engine Latency: {summary.avg_rule_duration_ms:.3f} ms")
    print(f"Avg Total Latency:       {summary.avg_total_duration_ms:.3f} ms")
    print("-" * 60)
    print("Category Breakdown:")
    for cat, stats in sorted(summary.category_breakdown.items()):
        pct = (stats["detected"] / stats["total"]) * 100 if stats["total"] else 0
        print(f"  - {cat:25}: {stats['detected']}/{stats['total']} ({pct:.1f}%)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_cli_benchmark()
