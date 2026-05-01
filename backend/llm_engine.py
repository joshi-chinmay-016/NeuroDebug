"""
llm.py — Neural Debugging Layer
Sends code and symbolic analysis findings to the Groq API
and returns a structured JSON response.
"""

import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI, AuthenticationError, RateLimitError, APIConnectionError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Environment Config
# ──────────────────────────────────────────────

GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")

# ──────────────────────────────────────────────
# System Prompt
# ──────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are a neural debugging assistant. Analyze the provided code and symbolic findings.

STRICT OUTPUT RULE: Respond ONLY with a single valid JSON object — no explanation,
no markdown, no code fences. The JSON must contain exactly these keys:

{
  "error_type":       "<short label for the error category>",
  "explanation":      "<clear explanation of the root cause>",
  "suggested_fix":    "<actionable fix or refactor suggestion>",
  "confidence_score": <float between 0.0 and 1.0>
}

If you cannot determine an issue, still return valid JSON with best-effort values.
""".strip()


# ──────────────────────────────────────────────
# Main Function
# ──────────────────────────────────────────────

async def get_llm_analysis(
    code: str,
    symbolic_issues: list[dict],
    api_key: Optional[str] = None,
) -> dict:
    """
    Send code and symbolic analysis findings to the Groq API.

    Args:
        code:             The source code to debug.
        symbolic_issues:  A list of issue dicts from symbolic analysis.
        api_key:          Optional caller-supplied Groq API key.
                          Takes priority over the .env key.

    Returns:
        A structured dict with keys: error_type, explanation,
        suggested_fix, confidence_score.
    """
    # Key resolution: caller key > env key
    resolved_key = api_key or GROQ_API_KEY

    if not resolved_key:
        logger.warning("No Groq API key found — falling back to symbolic analysis.")
        return _fallback_response(symbolic_issues)

    if not resolved_key.startswith("gsk_"):
        logger.error("Invalid Groq API key format (must start with 'gsk_').")
        return _error_response("invalid_key", "API key must start with 'gsk_'.")

    client = AsyncOpenAI(
        api_key=resolved_key,
        base_url=GROQ_BASE_URL,
    )

    user_prompt = _build_user_prompt(code, symbolic_issues)

    try:
        logger.info("Sending request to Groq API (model: %s).", GROQ_MODEL)
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
        )
        raw_text = response.choices[0].message.content or ""
        logger.info("Received response from Groq API.")
        return _parse_llm_response(raw_text)

    except AuthenticationError as exc:
        logger.error("Authentication failed: %s", exc)
        return _error_response("auth_error", str(exc))

    except RateLimitError as exc:
        logger.error("Rate limit exceeded: %s", exc)
        return _error_response("rate_limit", str(exc))

    except APIConnectionError as exc:
        logger.error("API connection error: %s", exc)
        return _error_response("connection_error", str(exc))

    except Exception as exc:
        logger.exception("Unexpected Groq API failure: %s", exc)
        return _fallback_response(symbolic_issues)


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def _build_user_prompt(code: str, symbolic_issues: list[dict]) -> str:
    """
    Format the user's code and symbolic findings into a readable prompt string.

    Args:
        code:            The source code snippet.
        symbolic_issues: List of symbolic analysis issue dicts.

    Returns:
        A formatted multi-line prompt string.
    """
    findings_block = "\n".join(
        f"  - [{i + 1}] {issue}" for i, issue in enumerate(symbolic_issues)
    ) or "  (none reported)"

    return (
        f"## Code Under Analysis\n\n"
        f"```\n{code}\n```\n\n"
        f"## Symbolic Findings\n\n"
        f"{findings_block}\n\n"
        f"Analyze the code in light of the symbolic findings and return the JSON."
    )


def _parse_llm_response(raw: str) -> dict:
    """
    Safely parse the LLM's raw string output into a Python dict.

    Strips markdown code fences if present before parsing.

    Args:
        raw: The raw string returned by the LLM.

    Returns:
        A parsed dict, or an error_response dict on failure.
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
        required = {"error_type", "explanation", "suggested_fix", "confidence_score"}
        missing  = required - parsed.keys()
        if missing:
            logger.warning("LLM response missing keys: %s", missing)
        return parsed
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM response as JSON: %s", exc)
        return _error_response("parse_error", f"Could not decode JSON: {exc}")


def _fallback_response(symbolic_issues: list[dict]) -> dict:
    """
    Generate a best-guess response from symbolic issues when no API key
    is available or when the API call fails entirely.

    Args:
        symbolic_issues: The list of symbolic analysis findings.

    Returns:
        A structured dict approximating LLM output.
    """
    if not symbolic_issues:
        return {
            "error_type":       "unknown",
            "explanation":      "No symbolic issues were provided and no LLM key is available.",
            "suggested_fix":    "Provide a valid Groq API key or add symbolic analysis findings.",
            "confidence_score": 0.0,
        }

    first_issue   = symbolic_issues[0]
    issue_summary = (
        ", ".join(f"{k}: {v}" for k, v in first_issue.items())
        if isinstance(first_issue, dict)
        else str(first_issue)
    )

    return {
        "error_type":    "symbolic_inference",
        "explanation":   (
            f"Based on {len(symbolic_issues)} symbolic finding(s), "
            f"the most likely issue is: {issue_summary}."
        ),
        "suggested_fix":    "Review the flagged symbolic findings and apply targeted refactoring.",
        "confidence_score": round(0.4 + min(len(symbolic_issues) * 0.05, 0.3), 2),
    }


def _error_response(error_type: str, detail: str) -> dict:
    """
    Return a standardised error dictionary for LLM-layer failures.

    Args:
        error_type: A short identifier for the error category.
        detail:     A human-readable description of what went wrong.

    Returns:
        A structured dict with zeroed confidence and error metadata.
    """
    return {
        "error_type":       error_type,
        "explanation":      detail,
        "suggested_fix":    "Check your Groq API key, network connectivity, or rate limit quota.",
        "confidence_score": 0.0,
    }