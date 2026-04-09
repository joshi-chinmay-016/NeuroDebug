"""
NeuroDebug — Neural Layer (LLM Engine)

Sends the user's code plus symbolic findings to the Groq API
and returns a structured explanation + suggested fix.
"""

import os
import json
import logging
import asyncio
from typing import Any

import groq
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()  # load GROQ_API_KEY from .env

logger = logging.getLogger("neurodebug.llm")

# Server-level fallback client (used only if user doesn't supply a key)
_server_key = os.getenv("GROQ_API_KEY", "")
_server_client = AsyncGroq(api_key=_server_key) if _server_key else None

# ──────────────────────────────────────────────────────────────────
# Prompt templates
# ──────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are NeuroDebug, an expert Python code analyser and debugger.
You combine symbolic AST analysis with deep reasoning to help developers fix their code.

Your response MUST be valid JSON with exactly these keys:
{
  "error_type":        "<concise category, e.g. 'SyntaxError', 'LogicError', 'Clean'>",
  "explanation":       "<detailed explanation of what is wrong and why>",
  "suggested_fix":     "<the entire corrected Python code snippet, properly formatted line-by-line>",
  "confidence_score":  <float 0.0–1.0>
}

Rules:
- If the code looks correct, set error_type to "Clean" and confidence_score to 0.95+.
- confidence_score reflects how certain you are that the issues you identified are real.
- suggested_fix MUST contain the exact, corrected Python code formatted cleanly. Do not write a prose description here; only output the actual fixed code.
- Be concise but thorough. Avoid hallucinating bugs that don't exist.
"""

_TEST_GENERATION_SYSTEM_PROMPT = """You are NeuroDebug's test generation expert. Your task is to generate comprehensive pytest test cases for Python code.

Your response MUST be valid JSON with exactly these keys:
{
  "test_cases": [
    {
      "test_name": "<descriptive test function name following pytest conventions>",
      "test_code": "<the complete test code as a string, properly formatted>",
      "description": "<brief description of what this test checks>"
    }
  ],
  "imports": "<string containing all necessary imports for the tests>",
  "setup_code": "<optional setup code to run before tests, or empty string>"
}

Rules:
- Generate at least 5 diverse test cases covering:
  * Happy path scenarios (normal valid inputs)
  * Edge cases (boundary values, empty inputs, None, etc.)
  * Error handling (invalid inputs, exceptions)
  * Type variations (if applicable)
- Each test_code must be a single, self-contained function definition string
- The imports string should contain all pytest and other imports needed
- setup_code can contain fixture definitions or helper functions
- Use descriptive assertion messages
- Follow pytest naming conventions (test_* function names)
"""

# ──────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────

async def get_llm_analysis(
    code: str,
    symbolic_issues: list[dict],
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Call Groq and return parsed JSON response.

    Key resolution order:
      1. User-supplied key (api_key argument)  ← preferred
      2. Server .env key                        ← fallback (optional)
      3. No key available                       ← symbolic-only fallback
    """
    # Pick which key to use
    key_to_use = (api_key or "").strip() or _server_key

    if not key_to_use:
        logger.warning("No API key provided — returning symbolic fallback.")
        return _fallback_response(symbolic_issues)

    # Validate key looks plausible before hitting the API
    if not key_to_use.startswith("gsk_"):
        return _error_response(
            "That doesn't look like a valid Groq key (should start with 'gsk_'). "
            "Please check and try again."
        )

    # Build a request-scoped client so each user is billed to their own account
    client = AsyncGroq(api_key=key_to_use)
    source = "user_key" if (api_key or "").strip() else "server_key"
    logger.info("LLM call using %s", source)

    user_prompt = _build_user_prompt(code, symbolic_issues)

    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        logger.debug("Raw LLM response: %s", raw[:200])
        return _parse_llm_response(raw)

    except groq.AuthenticationError:
        logger.error("Groq authentication failed — invalid key supplied by user.")
        return _error_response(
            "Invalid Groq API key. Please double-check the key you entered."
        )
    except groq.RateLimitError:
        logger.error("Groq rate limit exceeded.")
        return _error_response(
            "Groq rate limit exceeded on your key. Try again in a moment."
        )
    except groq.APIConnectionError as exc:
        logger.error("Groq connection error: %s", exc)
        return _error_response(f"Could not connect to Groq: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected LLM error: %s", exc)
        return _fallback_response(symbolic_issues)


async def generate_test_cases(
    code: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Generate comprehensive pytest test cases for the given code.

    Returns a dict with test_cases, imports, and setup_code.
    """
    # Pick which key to use
    key_to_use = (api_key or "").strip() or _server_key

    if not key_to_use:
        logger.warning("No API key provided — cannot generate tests without LLM.")
        return _test_generation_error("No API key provided. Please supply a Groq API key.")

    # Validate key looks plausible
    if not key_to_use.startswith("gsk_"):
        return _test_generation_error(
            "That doesn't look like a valid Groq key (should start with 'gsk_'). "
            "Please check and try again."
        )

    client = AsyncGroq(api_key=key_to_use)
    source = "user_key" if (api_key or "").strip() else "server_key"
    logger.info("Test generation LLM call using %s", source)

    user_prompt = _build_test_generation_prompt(code)

    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _TEST_GENERATION_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        logger.debug("Raw test generation response: %s", raw[:200])
        return _parse_test_generation_response(raw)

    except groq.AuthenticationError:
        logger.error("Groq authentication failed for test generation.")
        return _test_generation_error("Invalid Groq API key.")
    except groq.RateLimitError:
        logger.error("Groq rate limit exceeded for test generation.")
        return _test_generation_error("Groq rate limit exceeded. Try again in a moment.")
    except groq.APIConnectionError as exc:
        logger.error("Groq connection error during test generation: %s", exc)
        return _test_generation_error(f"Could not connect to Groq: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during test generation: %s", exc)
        return _test_generation_error(f"Test generation failed: {exc}")


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _build_user_prompt(code: str, symbolic_issues: list[dict]) -> str:
    issues_text = ""
    if symbolic_issues:
        issues_text = "\n\nSymbolic analysis found these issues:\n"
        for iss in symbolic_issues:
            sev = iss.get("severity", "info").upper()
            issues_text += f"  [{sev}] ({iss.get('rule_id','?')}) {iss.get('message','')}\n"
    else:
        issues_text = "\n\nSymbolic analysis found no issues."

    return f"""Please analyse the following Python code:{issues_text}

```python
{code}
```

Return your analysis as JSON."""


def _parse_llm_response(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
        return {
            "error_type":      str(data.get("error_type", "Unknown")),
            "explanation":     str(data.get("explanation", "")),
            "suggested_fix":   str(data.get("suggested_fix", "")),
            "confidence_score": float(data.get("confidence_score", 0.5)),
            "source": "llm",
        }
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse LLM JSON: %s", exc)
        return _error_response("LLM returned malformed JSON.")


def _fallback_response(symbolic_issues: list[dict]) -> dict[str, Any]:
    """Used when the LLM is unreachable — synthesise a response from symbolic data."""
    if not symbolic_issues:
        return {
            "error_type":       "Clean",
            "explanation":      "No issues detected by the symbolic analyser.",
            "suggested_fix":    "Code appears correct.",
            "confidence_score": 0.75,
            "source":           "symbolic_fallback",
        }

    error_issues = [i for i in symbolic_issues if i["severity"] == "error"]
    top = error_issues[0] if error_issues else symbolic_issues[0]

    return {
        "error_type":       top["category"],
        "explanation":      f"(LLM unavailable) Symbolic analysis: {top['message']}",
        "suggested_fix":    "Fix the reported symbolic issues. Add GROQ_API_KEY for AI-powered suggestions.",
        "confidence_score": 0.6,
        "source":           "symbolic_fallback",
    }


def _error_response(msg: str) -> dict[str, Any]:
    return {
        "error_type":       "LLMError",
        "explanation":      msg,
        "suggested_fix":    "Please check your API key and network connection.",
        "confidence_score": 0.0,
        "source":           "error",
    }


def _build_test_generation_prompt(code: str) -> str:
    """Build the prompt for test case generation."""
    return f"""Please generate comprehensive pytest test cases for the following Python code:

```python
{code}
```

Analyse the code's functions, methods, and edge cases. Generate at least 5 diverse test cases covering:
1. Happy path scenarios with valid inputs
2. Edge cases and boundary values
3. Error conditions and invalid inputs
4. Type variations if applicable

Return your test cases as JSON."""


def _parse_test_generation_response(raw: str) -> dict[str, Any]:
    """Parse the LLM response for test generation."""
    try:
        data = json.loads(raw)
        return {
            "test_cases": data.get("test_cases", []),
            "imports": str(data.get("imports", "import pytest")),
            "setup_code": str(data.get("setup_code", "")),
            "source": "llm",
            "success": True,
        }
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse test generation JSON: %s", exc)
        return _test_generation_error("LLM returned malformed JSON for test cases.")


def _test_generation_error(msg: str) -> dict[str, Any]:
    """Return error response for test generation."""
    return {
        "test_cases": [],
        "imports": "",
        "setup_code": "",
        "error": msg,
        "source": "error",
        "success": False,
    }
