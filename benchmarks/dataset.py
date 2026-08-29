"""NeuroDebug Root Benchmark Dataset re-export."""

import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from benchmarks.dataset import BENCHMARK_DATASET, BenchmarkSnippet
except ImportError:
    from backend.benchmarks.dataset import BENCHMARK_DATASET, BenchmarkSnippet

__all__ = ["BENCHMARK_DATASET", "BenchmarkSnippet"]
