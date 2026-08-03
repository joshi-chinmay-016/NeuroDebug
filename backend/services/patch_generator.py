"""
Patch Generator Service.

Orchestrates the generation of code patches using LLM and validation.
"""

import logging
import time
from typing import Optional, Dict, Any

from models.errors import LLMError, PatchGenerationError
from models.responses import PatchResponse
from llm.client import GroqClient
from services.patch_validator import PatchValidator
from services.diff_service import DiffService
from utils.logging import get_logger, log_pipeline_stage

logger = get_logger("neurodebug.patch_generator")


class PatchGenerator:
    """Service for generating and validating code patches."""

    def __init__(self, llm_client: Optional[GroqClient] = None):
        """
        Initialize the patch generator.

        Args:
            llm_client: Optional GroqClient instance. If not provided, creates one.
        """
        self.llm_client = llm_client
        self.validator = PatchValidator()
        self.diff_service = DiffService()

    async def generate_patch(
        self,
        code: str,
        symbolic_issues: list[Dict[str, Any]],
        api_key: Optional[str] = None
    ) -> PatchResponse:
        """
        Generate a patch for the given code based on detected issues.

        Args:
            code: The original Python code.
            symbolic_issues: List of detected symbolic issues.
            api_key: Optional user-provided Groq API key.

        Returns:
            PatchResponse containing the patch and validation results.

        Raises:
            PatchGenerationError: If patch generation fails.
        """
        start_time = time.time()

        # If no issues, return original code as-is
        if not symbolic_issues:
            logger.info("No issues detected, returning original code")
            return PatchResponse(
                original_code=code,
                patched_code=code,
                unified_diff="No changes - no issues detected.",
                validation_passed=True,
                validation_error=None
            )

        # Initialize LLM client if not provided
        if not self.llm_client:
            self.llm_client = GroqClient(api_key)

        # Check if LLM is available
        if not self.llm_client.is_available():
            logger.warning("LLM not available, cannot generate patch")
            raise PatchGenerationError(
                "LLM not available - cannot generate patch without API key"
            )

        try:
            # Generate patch using LLM
            logger.info("Generating patch with LLM")
            llm_start = time.time()
            patched_code = await self.llm_client.generate_patch(
                code=code,
                symbolic_issues=symbolic_issues
            )
            llm_duration = (time.time() - llm_start) * 1000
            log_pipeline_stage(logger, "llm_patch_generation", llm_duration)

            # Validate syntax
            logger.info("Validating patch syntax")
            val_start = time.time()
            is_valid, validation_error = self.validator.validate_patch(code, patched_code)
            val_duration = (time.time() - val_start) * 1000
            log_pipeline_stage(logger, "patch_validation", val_duration, "success" if is_valid else "failed")

            # Validate minimal change (heuristic)
            minimal_valid, minimal_error = self.validator.validate_minimal_change(code, patched_code)
            if not minimal_valid:
                logger.warning("Patch validation failed (minimal change): %s", minimal_error)
                if not validation_error:
                    validation_error = minimal_error

            # Generate unified diff
            logger.info("Generating unified diff")
            diff_start = time.time()
            unified_diff = self.diff_service.generate_unified_diff(code, patched_code)
            diff_duration = (time.time() - diff_start) * 1000
            log_pipeline_stage(logger, "diff_generation", diff_duration)

            total_duration = (time.time() - start_time) * 1000
            logger.info(
                "Patch generation complete: valid=%s duration_ms=%.2f",
                is_valid,
                total_duration
            )

            return PatchResponse(
                original_code=code,
                patched_code=patched_code,
                unified_diff=unified_diff,
                validation_passed=is_valid,
                validation_error=validation_error
            )

        except LLMError as exc:
            logger.error("LLM error during patch generation: %s", exc)
            raise PatchGenerationError(f"LLM error: {exc.message}") from exc
        except Exception as exc:
            logger.exception("Unexpected error during patch generation: %s", exc)
            raise PatchGenerationError(f"Unexpected error: {exc}") from exc

    def generate_patch_fallback(
        self,
        code: str,
        symbolic_issues: list[Dict[str, Any]]
    ) -> PatchResponse:
        """
        Generate a fallback patch when LLM is not available.

        This returns the original code with a note that no patch was generated.

        Args:
            code: The original Python code.
            symbolic_issues: List of detected symbolic issues.

        Returns:
            PatchResponse with original code and appropriate message.
        """
        logger.info("Generating fallback patch (LLM unavailable)")

        return PatchResponse(
            original_code=code,
            patched_code=code,
            unified_diff="No patch generated - LLM unavailable.",
            validation_passed=True,
            validation_error=None
        )
