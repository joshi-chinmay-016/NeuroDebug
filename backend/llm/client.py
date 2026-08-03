"""
Groq LLM Client wrapper.

Provides a clean interface for interacting with the Groq API.
"""

import json
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
            return

        if not Config.validate_api_key(resolved_key):
            raise LLMError(
                "Invalid Groq API key format (must start with 'gsk_')",
                error_type="invalid_key",
            )

        self.client = AsyncOpenAI(
            api_key=resolved_key,
            base_url=Config.GROQ_BASE_URL,
        )
        logger.info("Groq client initialized")

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

        Raises:
            LLMError: If the API call fails.
        """
        if not self.client:
            raise LLMError("No Groq API key available", error_type="no_api_key")

        from llm.prompt_builder import PromptBuilder

        system = system_prompt or PromptBuilder.PATCH_GENERATION_SYSTEM
        user_prompt = PromptBuilder.build_patch_prompt(code, symbolic_issues)

        try:
            logger.info("Sending patch generation request to Groq API")
            response = await self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            raw_text = response.choices[0].message.content or ""
            logger.info("Received patch from Groq API")
            return self._parse_code_response(raw_text)

        except AuthenticationError as exc:
            logger.error("Authentication failed: %s", exc)
            raise LLMError("Authentication failed", "auth_error", str(exc))

        except RateLimitError as exc:
            logger.error("Rate limit exceeded: %s", exc)
            raise LLMError("Rate limit exceeded", "rate_limit", str(exc))

        except APIConnectionError as exc:
            logger.error("API connection error: %s", exc)
            raise LLMError("API connection error", "connection_error", str(exc))

        except Exception as exc:
            logger.exception("Unexpected Groq API failure")
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

        Raises:
            LLMError: If the API call fails.
        """
        if not self.client:
            raise LLMError("No Groq API key available", error_type="no_api_key")

        from llm.prompt_builder import PromptBuilder

        system = system_prompt or PromptBuilder.ANALYSIS_SYSTEM
        user_prompt = PromptBuilder.build_analysis_prompt(code, symbolic_issues)

        try:
            logger.info("Sending analysis request to Groq API")
            response = await self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            raw_text = response.choices[0].message.content or ""
            logger.info("Received analysis from Groq API")
            return self._parse_json_response(raw_text)

        except AuthenticationError as exc:
            logger.error("Authentication failed: %s", exc)
            raise LLMError("Authentication failed", "auth_error", str(exc))

        except RateLimitError as exc:
            logger.error("Rate limit exceeded: %s", exc)
            raise LLMError("Rate limit exceeded", "rate_limit", str(exc))

        except APIConnectionError as exc:
            logger.error("API connection error: %s", exc)
            raise LLMError("API connection error", "connection_error", str(exc))

        except Exception as exc:
            logger.exception("Unexpected Groq API failure")
            raise LLMError("Unexpected API failure", "api_error", str(exc))

    @staticmethod
    def _parse_code_response(raw: str) -> str:
        """
        Parse LLM response as code, stripping markdown fences if present.

        Args:
            raw: The raw string returned by the LLM.

        Returns:
            Cleaned code string.
        """
        cleaned = (
            raw.strip()
            .removeprefix("```python")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        return cleaned

    @staticmethod
    def _parse_json_response(raw: str) -> dict[str, Any]:
        """
        Parse LLM response as JSON, stripping markdown fences if present.

        Args:
            raw: The raw string returned by the LLM.

        Returns:
            Parsed dict.

        Raises:
            LLMError: If parsing fails.
        """
        cleaned = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

        try:
            parsed = json.loads(cleaned)
            required = {
                "error_type",
                "explanation",
                "suggested_fix",
                "confidence_score",
            }
            missing = required - parsed.keys()
            if missing:
                logger.warning("LLM response missing keys: %s", missing)
            return parsed
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM response as JSON: %s", exc)
            raise LLMError("Could not decode JSON response", "parse_error", str(exc))

    def is_available(self) -> bool:
        """Check if the client is available (has valid API key)."""
        return self.client is not None
