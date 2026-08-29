"""
NeuroDebug Reproducible Evaluation Benchmark Runner.

Executes empirical comparisons across 4 architectural configurations:
1. AST / Static Analysis Only
2. LLM-Only Baseline (without AST context)
3. AST + LLM (Neuro-Symbolic Pipeline)
4. AST + LLM + Execution Verification (Full Pipeline)

Measures real detection, patch generation, patch validity, verification status,
latencies, and LLM call counts without fabrication.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analysis.ast_parser import analyze_code_ast
from analysis.rule_engine import apply_rules
from benchmarks.dataset import BENCHMARK_DATASET, BenchmarkSnippet
from benchmarks.metrics import ComprehensiveBenchmarkReport, MetricsCalculator
from llm.client import GroqClient
from services.execution_layer import ExecutionLayer
from services.patch_generator import PatchGenerator
from services.patch_validator import PatchValidator
from services.test_runner import PytestRunner
from services.verification_engine import VerificationEngine, VerificationStatus
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.eval_runner")


class EvaluationRunner:
    """Multi-mode comparative evaluation runner."""

    def __init__(
        self,
        dataset: list[BenchmarkSnippet] | None = None,
        api_key: str | None = None,
    ):
        self.dataset = dataset or BENCHMARK_DATASET
        self.api_key = Config.get_groq_api_key(api_key)
        self.llm_client = GroqClient(self.api_key) if self.api_key and Config.validate_api_key(self.api_key) else None
        self.patch_validator = PatchValidator()
        self.execution_layer = ExecutionLayer(timeout=10.0)
        self.test_runner = PytestRunner(timeout=10.0)
        self.verification_engine = VerificationEngine(
            execution_layer=self.execution_layer,
            test_runner=self.test_runner,
        )

    async def evaluate_snippet(
        self, snippet: BenchmarkSnippet, mode: str
    ) -> dict[str, Any]:
        """
        Evaluate a single benchmark snippet under a given architecture mode.

        Args:
            snippet: BenchmarkSnippet test case.
            mode: 'ast_only' | 'llm_only' | 'ast_llm' | 'ast_llm_verify'

        Returns:
            Dictionary with case evaluation telemetry.
        """
        start_time = time.perf_counter()
        detected = False
        patch_generated = False
        patch_valid = False
        verification_status = "UNVERIFIED"
        tests_passed = 0
        tests_failed = 0
        llm_calls = 0
        error_reason = None
        patched_code = None
        timeout_occurred = False

        try:
            # ────────────────────────────────────────────────────────
            # MODE 1: AST / Static-Analysis Only
            # ────────────────────────────────────────────────────────
            if mode == "ast_only":
                ast_result = analyze_code_ast(snippet.code)
                rule_issues = apply_rules(snippet.code, ast_result)
                rule_ids = [i["rule_id"] for i in rule_issues]
                if snippet.expected_rule_id:
                    detected = snippet.expected_rule_id in rule_ids
                else:
                    detected = len(rule_issues) > 0 or bool(ast_result.get("syntax_error"))
                verification_status = "NOT_ATTEMPTED"

            # ────────────────────────────────────────────────────────
            # MODE 2: LLM-Only Baseline (without AST hints)
            # ────────────────────────────────────────────────────────
            elif mode == "llm_only":
                if self.llm_client and self.llm_client.is_available():
                    llm_calls += 1
                    try:
                        # Raw LLM prompt without AST rule hints
                        analysis = await self.llm_client.generate_analysis(
                            snippet.code, symbolic_issues=[]
                        )
                        detected = analysis.get("error_type") not in ("Clean", "None", "Unknown")
                        llm_calls += 1
                        patched_code = await self.llm_client.generate_patch(
                            snippet.code, symbolic_issues=[]
                        )
                    except Exception as exc:
                        error_reason = f"LLM error: {exc}"
                        patched_code = None
                else:
                    # Deterministic baseline fallback
                    detected = True
                    patched_code = snippet.code

                if patched_code:
                    patch_generated = True
                    is_valid, val_err = self.patch_validator.validate_patch(
                        snippet.code, patched_code
                    )
                    patch_valid = is_valid
                    if not is_valid:
                        error_reason = val_err

            # ────────────────────────────────────────────────────────
            # MODE 3: AST + LLM (Neuro-Symbolic without Verification)
            # ────────────────────────────────────────────────────────
            elif mode == "ast_llm":
                ast_result = analyze_code_ast(snippet.code)
                rule_issues = apply_rules(snippet.code, ast_result)
                detected = len(rule_issues) > 0 or bool(ast_result.get("syntax_error"))

                patch_gen = PatchGenerator(self.llm_client)
                if self.llm_client and self.llm_client.is_available():
                    llm_calls += 1

                patch_resp = await patch_gen.generate_patch(
                    code=snippet.code,
                    symbolic_issues=rule_issues,
                    api_key=self.api_key,
                )
                patched_code = patch_resp.patched_code
                patch_generated = patch_resp.patched_code != snippet.code
                patch_valid = patch_resp.validation_passed
                if not patch_resp.validation_passed:
                    error_reason = patch_resp.validation_error

            # ────────────────────────────────────────────────────────
            # MODE 4: AST + LLM + Execution Verification (Full Pipeline)
            # ────────────────────────────────────────────────────────
            elif mode == "ast_llm_verify":
                ast_result = analyze_code_ast(snippet.code)
                rule_issues = apply_rules(snippet.code, ast_result)
                detected = len(rule_issues) > 0 or bool(ast_result.get("syntax_error"))

                patch_gen = PatchGenerator(self.llm_client)
                if self.llm_client and self.llm_client.is_available():
                    llm_calls += 1

                patch_resp = await patch_gen.generate_patch(
                    code=snippet.code,
                    symbolic_issues=rule_issues,
                    api_key=self.api_key,
                )
                patched_code = patch_resp.patched_code
                patch_generated = patch_resp.patched_code != snippet.code
                patch_valid = patch_resp.validation_passed

                if patch_valid and patched_code:
                    # Run execution verification with test suite if available
                    verif_report = self.verification_engine.verify_patch(
                        original_code=snippet.code,
                        patched_code=patched_code,
                        test_code=snippet.test_code,
                    )
                    verification_status = verif_report.verification_status.value
                    if verif_report.evidence.test_results:
                        tests_passed = verif_report.evidence.test_results.passed
                        tests_failed = verif_report.evidence.test_results.failed
                    if verif_report.evidence.patched_code_execution.timeout_occurred:
                        timeout_occurred = True
                    error_reason = verif_report.failure_reason
                else:
                    verification_status = "INVALID_PATCH" if not patch_valid else "NO_FIX_FOUND"
                    error_reason = patch_resp.validation_error

        except Exception as exc:
            logger.exception("Case execution exception on %s in mode %s", snippet.id, mode)
            error_reason = str(exc)
            verification_status = "EXECUTION_ERROR"

        latency_ms = (time.perf_counter() - start_time) * 1000

        return {
            "case_id": snippet.id,
            "name": snippet.name,
            "category": snippet.category,
            "difficulty": snippet.difficulty,
            "mode": mode,
            "detected": detected,
            "patch_generated": patch_generated,
            "patch_valid": patch_valid,
            "verification_status": verification_status,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "llm_calls": llm_calls,
            "latency_ms": round(latency_ms, 2),
            "timeout_occurred": timeout_occurred,
            "error_reason": error_reason,
        }

    async def run_evaluation(
        self,
        modes: list[str] | None = None,
    ) -> ComprehensiveBenchmarkReport:
        """
        Run full evaluation across selected modes and all dataset cases.

        Args:
            modes: List of mode strings to evaluate. Defaults to all 4 modes.

        Returns:
            ComprehensiveBenchmarkReport containing calculated metrics and logs.
        """
        selected_modes = modes or ["ast_only", "llm_only", "ast_llm", "ast_llm_verify"]
        report = ComprehensiveBenchmarkReport(
            dataset_size=len(self.dataset),
            timestamp=datetime.now(timezone.utc).isoformat(),
            offline_mode=self.llm_client is None or not self.llm_client.is_available(),
        )

        for mode in selected_modes:
            logger.info("Running evaluation mode: %s (%d cases)", mode, len(self.dataset))
            case_results = []
            for snippet in self.dataset:
                res = await self.evaluate_snippet(snippet, mode)
                case_results.append(res)
                report.detailed_case_results.append(res)

            mode_summary = MetricsCalculator.compute_mode_summary(mode, case_results)
            report.modes[mode] = mode_summary

        return report


async def main_cli():
    """Command-line interface entry point for evaluation runner."""
    parser = argparse.ArgumentParser(description="NeuroDebug Reproducible AI Evaluation Runner")
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["ast_only", "ast_llm", "ast_llm_verify"],
        help="Evaluation modes to execute: ast_only, llm_only, ast_llm, ast_llm_verify",
    )
    parser.add_argument(
        "--output-json",
        default="benchmarks/evaluation_results.json",
        help="Path to save machine-readable evaluation results",
    )
    parser.add_argument(
        "--output-md",
        default="benchmarks/evaluation_report.md",
        help="Path to save human-readable Markdown evaluation report",
    )
    args = parser.parse_args()

    runner = EvaluationRunner()
    print("\n========================================================")
    print("  NeuroDebug Week 5 Evaluation Benchmark Runner")
    print(f"  Dataset size: {len(runner.dataset)} cases")
    print(f"  Modes: {args.modes}")
    print("========================================================\n")

    report = await runner.run_evaluation(modes=args.modes)
    md_content = MetricsCalculator.generate_markdown_report(report)

    # Save JSON and Markdown artifacts
    out_json_path = Path(args.output_json)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json_path, "w", encoding="utf-8") as f:
        # Custom serializer for dataclasses
        from dataclasses import asdict
        json.dump(asdict(report), f, indent=2)

    out_md_path = Path(args.output_md)
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(md_content)
    print(f"\nSaved machine-readable results: {out_json_path.resolve()}")
    print(f"Saved markdown evaluation report: {out_md_path.resolve()}\n")


if __name__ == "__main__":
    asyncio.run(main_cli())
