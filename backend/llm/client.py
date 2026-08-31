"""
Groq LLM Client wrapper.

Provides a clean, resilient interface for interacting with the Groq API
with robust JSON and Python markdown code block extraction.
"""

import json
import re
from typing import Any

from openai import APIConnectionError, AsyncOpenAI, AuthenticationError, RateLimitError

from models.errors import LLMError
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.llm_client")


class GroqClient:
    """Client for Groq API interactions."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Groq client.

        Args:
            api_key: Optional API key. If not provided, uses Config.GROQ_API_KEY.
        """
        resolved_key = api_key or Config.GROQ_API_KEY

        if not resolved_key:
            logger.warning("No Groq API key provided")
            self.client = None
            self.api_key = None
            return

        if not Config.validate_api_key(resolved_key):
            raise LLMError(
                "Invalid Groq API key format (must start with 'gsk_')",
                error_type="invalid_key",
            )

        self.api_key = resolved_key
        self.client = AsyncOpenAI(
            api_key=resolved_key,
            base_url=Config.GROQ_BASE_URL,
        )
        logger.info("Groq client initialized successfully")

    async def generate_patch(
        self,
        code: str,
        symbolic_issues: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a code patch using the LLM.

        Args:
            code: The original Python code.
            symbolic_issues: List of detected symbolic issues.
            system_prompt: Optional custom system prompt.

        Returns:
            The patched code as a string.
        """
        if not self.client:
            raise LLMError("No Groq API key available", error_type="no_api_key")

        from llm.prompt_builder import PromptBuilder

        system = system_prompt or PromptBuilder.PATCH_GENERATION_SYSTEM
        user_prompt = PromptBuilder.build_patch_prompt(code, symbolic_issues)

        try:
            logger.info("Sending patch generation request to Groq API (model=%s)", Config.GROQ_MODEL)
            response = await self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content or ""
            logger.info("Received candidate patch from Groq API")
            return self._parse_code_response(raw_text)

        except AuthenticationError as exc:
            logger.error("Groq Authentication failed: %s", exc)
            raise LLMError("Authentication failed", "auth_error", str(exc))

        except RateLimitError as exc:
            logger.error("Groq Rate limit exceeded: %s", exc)
            raise LLMError("Rate limit exceeded", "rate_limit", str(exc))

        except APIConnectionError as exc:
            logger.error("Groq API connection error: %s", exc)
            raise LLMError("API connection error", "connection_error", str(exc))

        except Exception as exc:
            logger.exception("Unexpected Groq API failure: %s", exc)
            raise LLMError("Unexpected API failure", "api_error", str(exc))

    async def generate_analysis(
        self,
        code: str,
        symbolic_issues: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate code analysis (explanation) using the LLM.

        Args:
            code: The Python code to analyze.
            symbolic_issues: List of detected symbolic issues.
            system_prompt: Optional custom system prompt.

        Returns:
            A dict with keys: error_type, explanation, suggested_fix, confidence_score.
        """
        if not self.client:
            raise LLMError("No Groq API key available", error_type="no_api_key")

        from llm.prompt_builder import PromptBuilder

        system = system_prompt or PromptBuilder.ANALYSIS_SYSTEM
        user_prompt = PromptBuilder.build_analysis_prompt(code, symbolic_issues)

        try:
            logger.info("Sending analysis reasoning request to Groq API (model=%s)", Config.GROQ_MODEL)
            response = await self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content or ""
            logger.info("Received analysis reasoning from Groq API")
            return self._parse_json_response(raw_text)

        except AuthenticationError as exc:
            logger.error("Groq Authentication failed: %s", exc)
            raise LLMError("Authentication failed", "auth_error", str(exc))

        except RateLimitError as exc:
            logger.error("Groq Rate limit exceeded: %s", exc)
            raise LLMError("Rate limit exceeded", "rate_limit", str(exc))

        except APIConnectionError as exc:
            logger.error("Groq API connection error: %s", exc)
            raise LLMError("API connection error", "connection_error", str(exc))

        except Exception as exc:
            logger.exception("Unexpected Groq API failure: %s", exc)
            raise LLMError("Unexpected API failure", "api_error", str(exc))

    @staticmethod
    def _parse_code_response(raw: str) -> str:
        """
        Parse LLM response as Python code, extracting clean code blocks.
        """
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Match ```python ... ``` or ``` ... ```
        match = re.search(r"```(?:python)?\s*\n?(.*?)```", cleaned, re.DOTALL)
        if match:
            return match.group(1).strip()
        return cleaned.strip()

    @staticmethod
    def _parse_json_response(raw: str) -> dict[str, Any]:
        """
        Parse LLM response as JSON, extracting json blocks and objects cleanly.
        """
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
        content = match.group(1).strip() if match else cleaned.strip()

        # If not starting directly with {, find the outer JSON object
        if not content.startswith("{"):
            json_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON is not an object")

            return {
                "error_type": parsed.get("error_type", "BugDetected"),
                "explanation": parsed.get("explanation", raw.strip()),
                "suggested_fix": parsed.get("suggested_fix", "Apply verified candidate patch"),
                "confidence_score": float(parsed.get("confidence_score", 0.90)),
            }
        except Exception as exc:
            logger.warning("JSON decoding fallback triggered: %s", exc)
            return {
                "error_type": "DefectAnalysis",
                "explanation": raw.strip(),
                "suggested_fix": "Apply candidate fix",
                "confidence_score": 0.85,
            }

    def is_available(self) -> bool:
        """Check if the client is available (has valid API key)."""
        return self.client is not None
