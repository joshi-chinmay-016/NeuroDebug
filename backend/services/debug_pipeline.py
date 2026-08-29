"""
Debug Pipeline - Orchestration Layer.

Orchestrates the complete debug pipeline including verification:
User Code → AST Analysis → Rule Engine → Candidate Patch → Syntax Validation
→ Verification Engine → Execution Report → Structured API
"""

import time
import uuid
from typing import Any

from analysis.ast_parser import analyze_code_ast
from analysis.rule_engine import apply_rules
from llm.client import GroqClient
from models.errors import AnalysisError, LLMError, PatchGenerationError
from models.responses import DebugResponse, PatchResponse, SymbolicIssue
from services.patch_generator import PatchGenerator
from services.verification_engine import VerificationEngine
from utils.config import Config
from utils.logging import get_logger, log_pipeline_stage, set_request_id

logger = get_logger("neurodebug.debug_pipeline")


class DebugPipeline:
    """
    Orchestrates the complete debug pipeline with verification.

    Pipeline:
    1. AST Analysis
    2. Rule Engine
    3. LLM Analysis (if API key available)
    4. Patch Generation (if issues detected)
    5. Patch Validation
    6. Diff Generation
    7. **Verification** (if patch generated)
    8. Structured Response
    """

    def __init__(
        self,
        llm_client: GroqClient | None = None,
        verification_engine: VerificationEngine | None = None,
    ):
        """
        Initialize the debug pipeline.

        Args:
            llm_client: Optional GroqClient instance.
            verification_engine: Optional VerificationEngine instance.
        """
        self.llm_client = llm_client
        self.patch_generator = PatchGenerator(llm_client)
        self.verification_engine = verification_engine or VerificationEngine()

    async def execute(self, code: str, api_key: str | None = None) -> DebugResponse:
        """
        Execute the complete debug pipeline with verification.

        Args:
            code: The Python code to debug.
            api_key: Optional user-provided Groq API key.

        Returns:
            DebugResponse with analysis results, patch, and verification report.
        """
        # Set request ID for logging
        request_id = str(uuid.uuid4())[:8]
        set_request_id(request_id)
        logger.info("=== Starting debug pipeline [request_id=%s] ===", request_id)

        start_time = time.time()
        metadata = {}

        # Step 1: AST Analysis
        logger.info("Step 1: Running AST analysis")
        ast_start = time.time()
        try:
            ast_result = analyze_code_ast(code)
            ast_duration = (time.time() - ast_start) * 1000
            metadata["ast_duration_ms"] = round(ast_duration, 2)
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
            metadata["rule_duration_ms"] = round(rule_duration, 2)
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

        # Convert to SymbolicIssue models
        symbolic_issues = [SymbolicIssue(**issue) for issue in rule_issues]

        # Determine error type and confidence
        error_type, confidence = self._determine_error_type(ast_result, rule_issues)

        # Step 3: LLM Analysis (if available)
        explanation = self._generate_explanation(ast_result, rule_issues)
        llm_duration = 0

        resolved_api_key = Config.get_groq_api_key(api_key)
        if resolved_api_key and Config.validate_api_key(resolved_api_key):
            logger.info("Step 3: Running LLM analysis")
            try:
                llm_client = GroqClient(resolved_api_key)
                llm_start = time.time()
                llm_analysis = await llm_client.generate_analysis(code, rule_issues)
                llm_duration = (time.time() - llm_start) * 1000
                metadata["llm_duration_ms"] = round(llm_duration, 2)
                log_pipeline_stage(logger, "llm_analysis", llm_duration)

                # Use LLM results if available
                if llm_analysis.get("explanation"):
                    explanation = llm_analysis["explanation"]
                if (
                    llm_analysis.get("error_type")
                    and llm_analysis["error_type"] != "Unknown"
                ):
                    error_type = llm_analysis["error_type"]
                if llm_analysis.get("confidence_score"):
                    confidence = llm_analysis["confidence_score"]

                # Update patch generator with this client
                self.patch_generator = PatchGenerator(llm_client)

            except LLMError as exc:
                logger.warning("LLM analysis failed: %s", exc.message)
                metadata["llm_error"] = exc.error_type

        # Step 4: Patch Generation (if issues detected)
        candidate_patch: PatchResponse | None = None
        patch_status = "not_generated"
        validation_result = "not_attempted"
        verification_report = None

        if rule_issues or ast_result.get("syntax_error"):
            logger.info("Step 4: Generating candidate patch")
            try:
                patch_start = time.time()
                candidate_patch = await self.patch_generator.generate_patch(
                    code=code,
                    symbolic_issues=rule_issues,
                    api_key=resolved_api_key if resolved_api_key and Config.validate_api_key(resolved_api_key) else None,
                )
                patch_duration = (time.time() - patch_start) * 1000
                metadata["patch_generation_duration_ms"] = round(patch_duration, 2)
                log_pipeline_stage(logger, "patch_generation", patch_duration)

                patch_status = (
                    "generated"
                    if candidate_patch.validation_passed
                    else "generated_invalid"
                )
                validation_result = (
                    "valid" if candidate_patch.validation_passed else "invalid"
                )

                # Step 5: Verification (if patch was generated and valid)
                if candidate_patch.validation_passed:
                    logger.info("Step 5: Running verification engine")
                    try:
                        verif_start = time.time()
                        verification_report = self.verification_engine.verify_patch(
                            original_code=code,
                            patched_code=candidate_patch.patched_code,
                            test_code=None,
                        )
                        verif_duration = (time.time() - verif_start) * 1000
                        metadata["verification_duration_ms"] = round(verif_duration, 2)
                        log_pipeline_stage(
                            logger,
                            "verification",
                            verif_duration,
                            verification_report.verification_status.value,
                        )

                        # Convert to response model
                        from routes.debug import (
                            _convert_verification_report_to_response,
                        )

                        verification_report = _convert_verification_report_to_response(
                            verification_report
                        )

                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Verification failed: %s", exc)
                        metadata["verification_error"] = str(exc)

            except Exception as exc:
                logger.warning("Patch generation failed: %s", exc)
                patch_status = "failed"
                validation_result = "failed"
                metadata["patch_error"] = str(exc)

        # Final response
        total_duration = (time.time() - start_time) * 1000
        metadata["total_duration_ms"] = round(total_duration, 2)

        logger.info(
            "=== Debug pipeline complete [request_id=%s] === "
            "error_type=%s confidence=%.2f patch_status=%s validation=%s verification=%s duration_ms=%.2f",
            request_id,
            error_type,
            confidence,
            patch_status,
            validation_result,
            verification_report.verification_status if verification_report else "none",
            total_duration,
        )

        return DebugResponse(
            detected_issues=symbolic_issues,
            candidate_patch=candidate_patch,
            error_type=error_type,
            explanation=explanation,
            confidence_score=confidence,
            patch_status=patch_status,
            validation_result=validation_result,
            verification_report=verification_report,
            metadata=metadata,
        )

    def _determine_error_type(
        self, ast_result: dict[str, Any], rule_issues: list[dict[str, Any]]
    ) -> tuple[str, float]:
        """
        Determine the dominant error type and confidence from analysis results.

        Args:
            ast_result: AST analysis result.
            rule_issues: List of rule engine issues.

        Returns:
            Tuple of (error_type, confidence_score).
        """
        # Syntax error dominates
        if ast_result.get("syntax_error"):
            return "SyntaxError", 1.0

        # Use the first error-severity issue
        error_issues = [i for i in rule_issues if i.get("severity") == "error"]
        if error_issues:
            return error_issues[0].get("category", "Unknown"), 0.9

        # Use the first warning-severity issue
        warning_issues = [i for i in rule_issues if i.get("severity") == "warning"]
        if warning_issues:
            return warning_issues[0].get("category", "Unknown"), 0.7

        # No issues
        return "Clean", 1.0

    def _generate_explanation(
        self, ast_result: dict[str, Any], rule_issues: list[dict[str, Any]]
    ) -> str:
        """
        Generate an explanation from symbolic analysis results.

        Args:
            ast_result: AST analysis result.
            rule_issues: List of rule engine issues.

        Returns:
            Explanation string.
        """
        if ast_result.get("syntax_error"):
            return ast_result["syntax_error"]

        if not rule_issues:
            return "No issues detected in the code."

        # Build explanation from rule issues
        parts = []
        for issue in rule_issues[:3]:  # Limit to top 3 issues
            parts.append(f"- {issue.get('message', '')}")

        explanation = "Detected issues:\n" + "\n".join(parts)
        if len(rule_issues) > 3:
            explanation += f"\n... and {len(rule_issues) - 3} more issue(s)."

        return explanation
