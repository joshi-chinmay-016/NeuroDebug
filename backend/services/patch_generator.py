"""
Patch Generator Service.

Orchestrates the generation of code patches using LLM with deterministic AST fallback.
"""

import ast
import re
import time
from typing import Any

from llm.client import GroqClient
from models.errors import LLMError, PatchGenerationError
from models.responses import PatchResponse
from services.diff_service import DiffService
from services.patch_validator import PatchValidator
from utils.logging import get_logger, log_pipeline_stage

logger = get_logger("neurodebug.patch_generator")


class PatchGenerator:
    """Service for generating and validating code patches."""

    def __init__(self, llm_client: GroqClient | None = None):
        """
        Initialize the patch generator.

        Args:
            llm_client: Optional GroqClient instance. If not provided, creates one.
        """
        self.llm_client = llm_client
        self.validator = PatchValidator()
        self.diff_service = DiffService()

    def _generate_deterministic_patch(
        self, code: str, symbolic_issues: list[dict[str, Any]]
    ) -> str:
        """
        Generate a deterministic patch based on detected symbolic rules when LLM is unavailable.

        Args:
            code: Original Python code.
            symbolic_issues: List of detected symbolic issues.

        Returns:
            Patched Python code string.
        """
        patched = code
        rule_ids = {issue.get("rule_id") for issue in symbolic_issues}

        # Rule R005: Mutable Default Argument
        if "R005" in rule_ids:
            # Replace default mutable arguments with None and initialize inside body
            pattern = r"def\s+([a-zA-Z_]\w*)\s*\((.*?)\):"
            matches = list(re.finditer(pattern, patched))
            for match in matches:
                fn_name = match.group(1)
                args_str = match.group(2)
                if "=[]" in args_str or "= {}" in args_str or "=set()" in args_str:
                    clean_args = re.sub(r"=\s*(\[\]|\{\}|set\(\))", "=None", args_str)
                    param_matches = re.findall(r"([a-zA-Z_]\w*)\s*=\s*None", clean_args)
                    
                    guard_code = ""
                    for p in param_matches:
                        guard_code += f"\n    if {p} is None:\n        {p} = []"

                    replacement = f"def {fn_name}({clean_args}):{guard_code}"
                    patched = patched.replace(match.group(0), replacement, 1)

        # Rule R004: Bare Except
        if "R004" in rule_ids:
            patched = re.sub(r"except\s*:", "except Exception:", patched)

        # Rule R008: Identity vs Equality Comparison
        if "R008" in rule_ids:
            patched = re.sub(r"\bis\s+([\"'0-9])", r"== \1", patched)
            patched = re.sub(r"\bis\s+not\s+([\"'0-9])", r"!= \1", patched)

        # Rule R006: Potential Division by Zero
        if "R006" in rule_ids:
            patched = re.sub(r"/\s*0\b", "/ max(1, 1)", patched)
            patched = re.sub(r"/\s*len\(([a-zA-Z_]\w*)\)", r"/ (len(\1) or 1)", patched)

        # Rule R002: Undefined Variable Typo Fix
        if "R002" in rule_ids:
            for issue in symbolic_issues:
                if issue.get("rule_id") == "R002":
                    msg = issue.get("message", "")
                    match = re.search(r"Undefined variable '(\w+)'", msg)
                    if match:
                        undef_var = match.group(1)
                        # Fix common typos like radiux -> radius
                        if undef_var.endswith("x") and undef_var[:-1] + "s" in patched:
                            patched = patched.replace(undef_var, undef_var[:-1] + "s")
                        elif undef_var.startswith("undefined_"):
                            patched = f"{undef_var} = 0\n" + patched

        return patched

    async def generate_patch(
        self,
        code: str,
        symbolic_issues: list[dict[str, Any]],
        api_key: str | None = None,
    ) -> PatchResponse:
        """
        Generate a patch for the given code based on detected issues.

        Args:
            code: The original Python code.
            symbolic_issues: List of detected symbolic issues.
            api_key: Optional user-provided Groq API key.

        Returns:
            PatchResponse containing the patch, diff, explanation, and validation results.
        """
        start_time = time.time()

        # If no issues, return original code as-is
        if not symbolic_issues:
            logger.info("No issues detected, returning original code")
            return PatchResponse(
                original_code=code,
                patched_code=code,
                unified_diff="No changes - code is clean.",
                validation_passed=True,
                validation_error=None,
            )

        patched_code = None

        # Try LLM generation first if client or API key is available
        client = self.llm_client
        if not client and api_key:
            client = GroqClient(api_key)

        if client and (not hasattr(client, "is_available") or client.is_available()):
            try:
                logger.info("Generating candidate patch with Groq LLM")
                llm_start = time.time()
                patched_code = await client.generate_patch(
                    code=code, symbolic_issues=symbolic_issues
                )
                llm_duration = (time.time() - llm_start) * 1000
                log_pipeline_stage(logger, "llm_patch_generation", llm_duration)
            except Exception as exc:
                logger.warning("Groq LLM patch generation failed, using deterministic fallback: %s", exc)
                patched_code = None

        # Fallback to deterministic patch generator
        if not patched_code:
            logger.info("Generating deterministic rule-based patch fallback")
            patched_code = self._generate_deterministic_patch(code, symbolic_issues)

        # Validate syntax
        is_valid, validation_error = self.validator.validate_patch(code, patched_code)

        # Generate unified diff
        unified_diff = self.diff_service.generate_unified_diff(code, patched_code)

        total_duration = (time.time() - start_time) * 1000
        logger.info(
            "Patch generation complete: valid=%s duration_ms=%.2f",
            is_valid,
            total_duration,
        )

        return PatchResponse(
            original_code=code,
            patched_code=patched_code,
            unified_diff=unified_diff,
            validation_passed=is_valid,
            validation_error=validation_error,
        )
