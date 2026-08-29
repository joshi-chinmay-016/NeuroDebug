"""
NeuroDebug — Honest Evaluation Metrics Engine.

Calculates mathematically grounded, empirical evaluation metrics for
neuro-symbolic debugging runs without fabricated numbers.
"""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ModeEvaluationSummary:
    """Metrics summary for a specific evaluation mode."""

    mode: str
    total_cases: int = 0
    detected_count: int = 0
    detection_rate: float = 0.0
    patch_generated_count: int = 0
    patch_generation_rate: float = 0.0
    patch_valid_count: int = 0
    patch_validity_rate: float = 0.0
    verified_fix_count: int = 0
    verified_fix_rate: float = 0.0
    unverified_count: int = 0
    unverified_rate: float = 0.0
    failure_count: int = 0
    failure_rate: float = 0.0
    timeout_count: int = 0
    timeout_rate: float = 0.0
    avg_latency_ms: float = 0.0
    median_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    total_llm_calls: int = 0
    avg_llm_calls_per_case: float = 0.0
    category_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class ComprehensiveBenchmarkReport:
    """Multi-mode comparative evaluation report."""

    dataset_size: int
    modes: dict[str, ModeEvaluationSummary] = field(default_factory=dict)
    detailed_case_results: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""
    offline_mode: bool = False


class MetricsCalculator:
    """Computes honest evaluation metrics from evaluation run records."""

    @staticmethod
    def compute_mode_summary(mode: str, case_results: list[dict[str, Any]]) -> ModeEvaluationSummary:
        """
        Compute aggregate metrics for a single mode over evaluated cases.

        Args:
            mode: Identifier of evaluation mode.
            case_results: List of raw result dicts from runner.

        Returns:
            ModeEvaluationSummary dataclass with metrics.
        """
        total = len(case_results)
        if total == 0:
            return ModeEvaluationSummary(mode=mode)

        detected = sum(1 for r in case_results if r.get("detected", False))
        patch_gen = sum(1 for r in case_results if r.get("patch_generated", False))
        patch_valid = sum(1 for r in case_results if r.get("patch_valid", False))
        verified = sum(1 for r in case_results if r.get("verification_status") == "VERIFIED")
        unverified = sum(1 for r in case_results if r.get("verification_status") == "UNVERIFIED")
        failed = sum(
            1 for r in case_results if r.get("verification_status") in ("FAILED", "FAILED_VERIFICATION", "INVALID_PATCH")
        )
        timeouts = sum(
            1 for r in case_results if r.get("timeout_occurred", False) or r.get("verification_status") == "EXECUTION_TIMEOUT"
        )
        llm_calls = sum(r.get("llm_calls", 0) for r in case_results)

        latencies = [r.get("latency_ms", 0.0) for r in case_results if r.get("latency_ms") is not None]
        avg_latency = round(statistics.mean(latencies), 2) if latencies else 0.0
        med_latency = round(statistics.median(latencies), 2) if latencies else 0.0
        
        # 95th percentile latency
        if len(latencies) >= 2:
            sorted_lat = sorted(latencies)
            idx = int(0.95 * len(sorted_lat))
            p95_latency = round(sorted_lat[min(idx, len(sorted_lat) - 1)], 2)
        else:
            p95_latency = avg_latency

        # Category breakdown
        category_stats: dict[str, dict[str, Any]] = {}
        for r in case_results:
            cat = r.get("category", "General")
            c_entry = category_stats.setdefault(
                cat,
                {"total": 0, "detected": 0, "verified": 0, "valid_patch": 0},
            )
            c_entry["total"] += 1
            if r.get("detected"):
                c_entry["detected"] += 1
            if r.get("verification_status") == "VERIFIED":
                c_entry["verified"] += 1
            if r.get("patch_valid"):
                c_entry["valid_patch"] += 1

        for cat, stats in category_stats.items():
            tot = stats["total"]
            stats["detection_rate"] = round((stats["detected"] / tot) * 100, 1) if tot else 0.0
            stats["verified_rate"] = round((stats["verified"] / tot) * 100, 1) if tot else 0.0

        return ModeEvaluationSummary(
            mode=mode,
            total_cases=total,
            detected_count=detected,
            detection_rate=round((detected / total) * 100, 2),
            patch_generated_count=patch_gen,
            patch_generation_rate=round((patch_gen / total) * 100, 2),
            patch_valid_count=patch_valid,
            patch_validity_rate=round((patch_valid / total) * 100, 2),
            verified_fix_count=verified,
            verified_fix_rate=round((verified / total) * 100, 2),
            unverified_count=unverified,
            unverified_rate=round((unverified / total) * 100, 2),
            failure_count=failed,
            failure_rate=round((failed / total) * 100, 2),
            timeout_count=timeouts,
            timeout_rate=round((timeouts / total) * 100, 2),
            avg_latency_ms=avg_latency,
            median_latency_ms=med_latency,
            p95_latency_ms=p95_latency,
            total_llm_calls=llm_calls,
            avg_llm_calls_per_case=round(llm_calls / total, 2),
            category_breakdown=category_stats,
        )

    @staticmethod
    def generate_markdown_report(report: ComprehensiveBenchmarkReport) -> str:
        """Generate formatted GitHub-flavored markdown report."""
        lines = [
            "# NeuroDebug AI Evaluation & Benchmark Report",
            "",
            f"**Evaluation Date/Time:** `{report.timestamp}`  ",
            f"**Dataset Size:** `{report.dataset_size} real Python debugging cases`  ",
            f"**Execution Mode:** `{'Offline / Deterministic Fallback' if report.offline_mode else 'Live Groq LLM + Subprocess Verification'}`  ",
            "",
            "## Comparative Evaluation Across Architectures",
            "",
            "| Architecture Mode | Detection Rate | Patch Validity | Verified Fix Rate | Avg Latency | P95 Latency | LLM Calls/Case |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        mode_labels = {
            "ast_only": "1. AST / Static Analysis Only",
            "llm_only": "2. LLM-Only Baseline",
            "ast_llm": "3. AST + LLM (Neuro-Symbolic)",
            "ast_llm_verify": "4. AST + LLM + Execution Verification",
        }

        for mode_key, summary in report.modes.items():
            label = mode_labels.get(mode_key, mode_key)
            lines.append(
                f"| **{label}** | {summary.detection_rate:.1f}% ({summary.detected_count}/{summary.total_cases}) | "
                f"{summary.patch_validity_rate:.1f}% | {summary.verified_fix_rate:.1f}% ({summary.verified_fix_count}/{summary.total_cases}) | "
                f"{summary.avg_latency_ms:.2f} ms | {summary.p95_latency_ms:.2f} ms | {summary.avg_llm_calls_per_case:.1f} |"
            )

        lines.extend([
            "",
            "## Category-Level Detection & Verification Breakdown",
            "",
        ])

        # Pick the most complete mode for category breakdown
        primary_mode = report.modes.get("ast_llm_verify") or next(iter(report.modes.values()), None)
        if primary_mode and primary_mode.category_breakdown:
            lines.extend([
                f"### Mode: `{primary_mode.mode}`",
                "",
                "| Bug Category | Cases | Detected | Verified Fixes | Detection Rate | Verification Rate |",
                "| :--- | :--- | :--- | :--- | :--- | :--- |",
            ])
            for cat, stats in sorted(primary_mode.category_breakdown.items()):
                lines.append(
                    f"| `{cat}` | {stats['total']} | {stats['detected']} | {stats['verified']} | "
                    f"{stats.get('detection_rate', 0.0):.1f}% | {stats.get('verified_rate', 0.0):.1f}% |"
                )

        lines.extend([
            "",
            "## Methodology & Verification Caveats",
            "",
            "- **Distinction of Signals:** Detection rate measures whether a defect was surfaced; Patch Validity measures syntax correctness via AST; Verification Rate measures whether the candidate patch executes cleanly and satisfies pytest test assertions.",
            "- **Behavioral Evidence vs Semantic Proof:** Passing a pytest suite constitutes verifiable empirical evidence of defect resolution within tested invariants, not universal semantic proof.",
            "- **Persistence Guarantee:** Results are calculated from actual execution runs without fabrication.",
        ])

        return "\n".join(lines)
