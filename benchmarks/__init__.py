"""NeuroDebug Root Benchmark Package (re-exports backend/benchmarks)."""

import sys
from pathlib import Path

# Add backend directory to sys.path if not present
backend_dir = str(Path(__file__).resolve().parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.benchmarks.benchmark_runner import BenchmarkRunner, BenchmarkSummary, run_cli_benchmark
from backend.benchmarks.dataset import BENCHMARK_DATASET, BenchmarkSnippet

__all__ = [
    "BENCHMARK_DATASET",
    "BenchmarkRunner",
    "BenchmarkSnippet",
    "BenchmarkSummary",
    "run_cli_benchmark",
]

if __name__ == "__main__":
    run_cli_benchmark()
