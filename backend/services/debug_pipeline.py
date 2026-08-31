"""
Debug Pipeline - Orchestration Layer.

Orchestrates the neuro-symbolic debug pipeline:
User Code → AST Analysis → Rule Engine → LLM Analysis (with Cache)
→ AST/LLM Agreement Signal → Multi-Candidate Patch Generation → Evidence-Based Ranking
→ Subprocess Verification → Structured Response with Telemetry.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from analysis.ast_parser import analyze_code_ast
from analysis.rule_engine import apply_rules
from llm.client import GroqClient
from models.errors import AnalysisError, LLMError
from models.responses import (
    AgreementSignalResponse,
    CandidateEvaluationResponse,
    DebugResponse,
    PatchResponse,
    SymbolicIssue,
)
from services.agreement_analyzer import AgreementAnalyzer
from services.llm_cache import compute_llm_cache_key, global_llm_cache
from services.patch_generator import PatchGenerator
from services.patch_ranker import PatchRanker
from services.verification_engine import VerificationEngine
from utils.config import Config
from utils.logging import (
    PipelineTelemetry,
    get_logger,
    get_request_id,
    log_pipeline_stage,
    set_request_id,
)

logger = get_logger("neurodebug.debug_pipeline")


class DebugPipeline:
    """
    Orchestrates the complete neuro-symbolic debug pipeline with verification and ranking.
    """

    def __init__(
        self,
        llm_client: GroqClient | None = None,
        verification_engine: VerificationEngine | None = None,
        patch_ranker: PatchRanker | None = None,
    ):
        self.llm_client = llm_client
        self.patch_generator = PatchGenerator(llm_client)
        self.verification_engine = verification_engine or VerificationEngine()
        self.patch_ranker = patch_ranker or PatchRanker(verification_engine=self.verification_engine)

    async def execute(
        self,
        code: str,
        api_key: str | None = None,
        test_code: str | None = None,
    ) -> DebugResponse:
        """
        Execute the complete debug pipeline.

        Args:
            code: The Python code to debug.
            api_key: Optional user-provided Groq API key.
            test_code: Optional pytest verification suite.

        Returns:
            DebugResponse with analysis, agreement signal, ranked candidates, and verification.
        """
        req_id = set_request_id()
        telemetry = PipelineTelemetry(request_id=req_id)
        start_time = time.time()
        logger.info("=== Starting debug pipeline [req_id=%s] ===", req_id)

        metadata: dict[str, Any] = {
            "request_id": req_id,
            "cache_hit": False,
            "llm_calls": 0,
        }

        # Step 1: AST Analysis
        logger.info("Step 1: Running AST analysis")
        ast_start = time.time()
        try:
            ast_result = analyze_code_ast(code)
            ast_duration = (time.time() - ast_start) * 1000
            telemetry.ast_duration_ms = round(ast_duration, 2)
            telemetry.stages_completed.append("ast_analysis")
            metadata["ast_duration_ms"] = telemetry.ast_duration_ms
            log_pipeline_stage(logger, "ast_analysis", ast_duration)
        except Exception as exc:
            logger.exception("AST analysis failed")
            raise AnalysisError(f"AST analysis failed: {exc}") from exc

        # Step 2: Rule Engine
        logger.info("Step 2: Running rule engine")
        rule_start = time.time()
        try:
            rule_issues = apply_rules(code, ast_result)
            rule_duration = (time.time() - rule_start) * 1000
            telemetry.rule_duration_ms = round(rule_duration, 2)
            telemetry.stages_completed.append("rule_engine")
            metadata["rule_duration_ms"] = telemetry.rule_duration_ms
            log_pipeline_stage(
                logger,
                "rule_engine",
                rule_duration,
                "success",
                issues_found=len(rule_issues),
            )
        except Exception as exc:
            logger.exception("Rule engine failed")
            raise AnalysisError(f"Rule engine failed: {exc}") from exc

        symbolic_issues = [SymbolicIssue(**issue) for issue in rule_issues]
        error_type, confidence = self._determine_error_type(ast_result, rule_issues)
        explanation = self._generate_explanation(ast_result, rule_issues)

        # Step 3: LLM Analysis with Cache
        llm_analysis = None
        resolved_api_key = Config.get_groq_api_key(api_key)
        if resolved_api_key and Config.validate_api_key(resolved_api_key):
            cache_key = compute_llm_cache_key(
                code=code,
                prompt_type="analysis",
                model_name=Config.GROQ_MODEL,
                symbolic_issues=rule_issues,
            )

            # Check L1 cache
            cached_data = await global_llm_cache.get(cache_key)
            if cached_data:
                logger.info("LLM Analysis Cache Hit [req_id=%s]", req_id)
                llm_analysis = cached_data
                metadata["cache_hit"] = True
                telemetry.cache_hit = True
            else:
                logger.info("Step 3: Executing LLM analysis [cache miss]")
                try:
                    llm_client = GroqClient(resolved_api_key)
                    llm_start = time.time()
                    llm_analysis = await llm_client.generate_analysis(code, rule_issues)
                    llm_duration = (time.time() - llm_start) * 1000
                    telemetry.llm_analysis_duration_ms = round(llm_duration, 2)
                    telemetry.llm_calls += 1
                    metadata["llm_calls"] = telemetry.llm_calls
                    metadata["llm_duration_ms"] = telemetry.llm_analysis_duration_ms
                    log_pipeline_stage(logger, "llm_analysis", llm_duration)

                    # Store in cache
                    await global_llm_cache.set(
                        cache_key,
                        llm_analysis,
                        ttl_seconds=Config.CACHE_TTL_SECONDS,
                        model_name=Config.GROQ_MODEL,
                    )
                    self.patch_generator = PatchGenerator(llm_client)

                except LLMError as exc:
                    logger.warning("LLM analysis failed: %s", exc.message)
                    metadata["llm_error"] = exc.error_type

            if llm_analysis:
                if llm_analysis.get("explanation"):
                    explanation = llm_analysis["explanation"]
                if llm_analysis.get("error_type") and llm_analysis["error_type"] != "Unknown":
                    error_type = llm_analysis["error_type"]
                if llm_analysis.get("confidence_score"):
                    confidence = llm_analysis["confidence_score"]

        # Step 4: AST / LLM Agreement Signal
        agreement_signal = AgreementAnalyzer.analyze_agreement(
            ast_result=ast_result,
            symbolic_issues=rule_issues,
            llm_analysis=llm_analysis,
        )
        agreement_response = AgreementSignalResponse(
            agreement_score=agreement_signal.agreement_score,
            consensus_status=agreement_signal.consensus_status.value,
            matched_issues_count=len(agreement_signal.matched_issues),
            calibrated_confidence=agreement_signal.calibrated_confidence,
            synthesis_summary=agreement_signal.synthesis_summary,
        )
        if not rule_issues and not ast_result.get("syntax_error") and not llm_analysis:
            confidence = 1.0
        else:
            confidence = (
                llm_analysis.get("confidence_score")
                if llm_analysis and llm_analysis.get("confidence_score") is not None
                else agreement_signal.calibrated_confidence
            )

        # Step 5: Candidate Patch Generation & Evidence Ranking
        candidate_patch: PatchResponse | None = None
        ranked_responses: list[CandidateEvaluationResponse] = []
        verification_report = None
        patch_status = "not_generated"
        validation_result = "not_attempted"

        if rule_issues or ast_result.get("syntax_error") or (llm_analysis and llm_analysis.get("error_type") not in ("Clean", "None")):
            logger.info("Step 5: Generating candidate patches for ranking")
            patch_start = time.time()
            candidates_to_rank: list[dict[str, Any]] = []

            # 1. Deterministic symbolic candidate
            det_patch = self.patch_generator._generate_deterministic_patch(code, rule_issues)
            if det_patch and det_patch != code:
                candidates_to_rank.append({"source": "deterministic_rule", "patched_code": det_patch})

            # 2. LLM neural candidate (if client available)
            if resolved_api_key and Config.validate_api_key(resolved_api_key):
                try:
                    effective_issues = list(rule_issues)
                    if not effective_issues and llm_analysis and llm_analysis.get("error_type") not in ("Clean", "None"):
                        effective_issues.append({
                            "rule_id": "LLM-001",
                            "severity": "error",
                            "category": llm_analysis.get("error_type", "LogicError"),
                            "message": llm_analysis.get("explanation", "Logic or runtime issue detected"),
                            "line": None,
                        })

                    patch_resp = await self.patch_generator.generate_patch(
                        code=code,
                        symbolic_issues=effective_issues,
                        api_key=resolved_api_key,
                    )
                    telemetry.llm_calls += 1
                    metadata["llm_calls"] = telemetry.llm_calls
                    if patch_resp.patched_code != code:
                        candidates_to_rank.append({"source": "neural_llm", "patched_code": patch_resp.patched_code})
                except Exception as p_exc:
                    logger.warning("LLM patch generation failed: %s", p_exc)

            patch_gen_duration = (time.time() - patch_start) * 1000
            telemetry.patch_generation_duration_ms = round(patch_gen_duration, 2)
            metadata["patch_generation_duration_ms"] = telemetry.patch_generation_duration_ms

            # 3. Evidence-Based Ranking
            if candidates_to_rank:
                logger.info("Step 6: Ranking %d candidate patches", len(candidates_to_rank))
                rank_start = time.time()
                ranking_res = self.patch_ranker.rank_candidates(
                    original_code=code,
                    candidates=candidates_to_rank,
                    test_code=test_code,
                )
                verif_dur = round((time.time() - rank_start) * 1000, 2)
                telemetry.ranking_duration_ms = verif_dur
                telemetry.verification_duration_ms = verif_dur
                metadata["ranking_duration_ms"] = verif_dur
                metadata["verification_duration_ms"] = verif_dur
                metadata["ranking_rationale"] = ranking_res.ranking_rationale

                for cand in ranking_res.all_candidates:
                    ranked_responses.append(
                        CandidateEvaluationResponse(
                            candidate_id=cand.candidate_id,
                            source=cand.source,
                            patched_code=cand.patched_code,
                            diff=cand.diff,
                            validation_passed=cand.validation_passed,
                            verification_status=cand.verification_status,
                            evidence_score=cand.evidence_score,
                            rank=cand.rank,
                            selection_reason=cand.selection_reason,
                        )
                    )

                if ranking_res.best_candidate:
                    best = ranking_res.best_candidate
                    candidate_patch = PatchResponse(
                        original_code=code,
                        patched_code=best.patched_code,
                        unified_diff=best.diff,
                        validation_passed=best.validation_passed,
                        validation_error=best.validation_error,
                    )
                    patch_status = "generated" if best.validation_passed else "generated_invalid"
                    validation_result = "valid" if best.validation_passed else "invalid"

                    # Map verification report to response
                    if best.verification_report:
                        from routes.debug import _convert_verification_report_to_response
                        verification_report = _convert_verification_report_to_response(
                            best.verification_report
                        )

        total_duration = (time.time() - start_time) * 1000
        telemetry.total_duration_ms = round(total_duration, 2)
        metadata["total_duration_ms"] = telemetry.total_duration_ms
        metadata["telemetry"] = {
            "ast_duration_ms": telemetry.ast_duration_ms,
            "rule_duration_ms": telemetry.rule_duration_ms,
            "llm_analysis_duration_ms": telemetry.llm_analysis_duration_ms,
            "patch_generation_duration_ms": telemetry.patch_generation_duration_ms,
            "ranking_duration_ms": telemetry.ranking_duration_ms,
            "total_duration_ms": telemetry.total_duration_ms,
            "stages_completed": telemetry.stages_completed,
        }

        return DebugResponse(
            detected_issues=symbolic_issues,
            candidate_patch=candidate_patch,
            error_type=error_type,
            explanation=explanation,
            confidence_score=confidence,
            patch_status=patch_status,
            validation_result=validation_result,
            verification_report=verification_report,
            agreement_signal=agreement_response,
            ranked_candidates=ranked_responses,
            metadata=metadata,
        )

    def _determine_error_type(
        self, ast_result: dict[str, Any], rule_issues: list[dict[str, Any]]
    ) -> tuple[str, float]:
        """Determine primary error type and baseline confidence from symbolic results."""
        if ast_result.get("syntax_error"):
            return "SyntaxError", 1.0

        if not rule_issues:
            return "Clean", 1.0

        priority_map = {
            "critical": 1.0,
            "error": 0.9,
            "warning": 0.7,
            "info": 0.5,
        }

        sorted_issues = sorted(
            rule_issues,
            key=lambda x: priority_map.get(x.get("severity", "info"), 0.5),
            reverse=True,
        )
        top_issue = sorted_issues[0]
        severity = top_issue.get("severity", "warning")
        return top_issue.get("category", "Unknown"), priority_map.get(severity, 0.7)

    def _generate_explanation(
        self, ast_result: dict[str, Any], rule_issues: list[dict[str, Any]]
    ) -> str:
        """Generate deterministic symbolic explanation."""
        if ast_result.get("syntax_error"):
            return ast_result["syntax_error"]

        if not rule_issues:
            return "No issues detected in the code."

        lines = ["Detected issues:"]
        for issue in rule_issues[:3]:
            lines.append(f"- {issue.get('message', '')}")

        if len(rule_issues) > 3:
            lines.append(f"... and {len(rule_issues) - 3} more issue(s).")

        return "\n".join(lines)
