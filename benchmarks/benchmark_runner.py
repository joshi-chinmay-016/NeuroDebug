"""NeuroDebug Root Benchmark Runner CLI entry point."""

import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.benchmarks.benchmark_runner import BenchmarkResult, BenchmarkRunner, BenchmarkSummary, run_cli_benchmark

if __name__ == "__main__":
    run_cli_benchmark()
