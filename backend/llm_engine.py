"""
NeuroDebug — Neural Layer (LLM Engine)

Sends the user's code plus symbolic findings to the OpenAI Chat API
and returns a structured explanation + suggested fix.
"""

import os
import json
import logging
import asyncio
from typing import Any

import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()  # load OPENAI_API_KEY from .env

logger = logging.getLogger("neurodebug.llm")

# Server-level fallback client (used only if user doesn't supply a key)
_server_key = os.getenv("OPENAI_API_KEY", "")
_server_client = AsyncOpenAI(api_key=_server_key) if _server_key else None

# ──────────────────────────────────────────────────────────────────
# Prompt templates
# ──────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are NeuroDebug, an expert Python code analyser and debugger.
You combine symbolic AST analysis with deep reasoning to help developers fix their code.

Your response MUST be valid JSON with exactly these keys:
{
  "error_type":        "<concise category, e.g. 'SyntaxError', 'LogicError', 'Clean'>",
  "explanation":       "<detailed explanation of what is wrong and why>",
  "suggested_fix":     "<corrected code or description of fix>",
  "confidence_score":  <float 0.0–1.0>
}

Rules:
- If the code looks correct, set error_type to "Clean" and confidence_score to 0.95+.
- confidence_score reflects how certain you are that the issues you identified are real.
- suggested_fix should contain the corrected Python code when possible.
- Be concise but thorough. Avoid hallucinating bugs that don't exist.
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
    Call OpenAI and return parsed JSON response.

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
    if not key_to_use.startswith("sk-"):
        return _error_response(
            "That doesn't look like a valid OpenAI key (should start with 'sk-'). "
            "Please check and try again."
        )

    # Build a request-scoped client so each user is billed to their own account
    client = AsyncOpenAI(api_key=key_to_use)
    source = "user_key" if (api_key or "").strip() else "server_key"
    logger.info("LLM call using %s", source)

    user_prompt = _build_user_prompt(code, symbolic_issues)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
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

    except openai.AuthenticationError:
        logger.error("OpenAI authentication failed — invalid key supplied by user.")
        return _error_response(
            "Invalid OpenAI API key. Please double-check the key you entered."
        )
    except openai.RateLimitError:
        logger.error("OpenAI rate limit exceeded.")
        return _error_response(
            "OpenAI rate limit exceeded on your key. Try again in a moment."
        )
    except openai.APIConnectionError as exc:
        logger.error("OpenAI connection error: %s", exc)
        return _error_response(f"Could not connect to OpenAI: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected LLM error: %s", exc)
        return _fallback_response(symbolic_issues)


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
        "suggested_fix":    "Fix the reported symbolic issues. Add OPENAI_API_KEY for AI-powered suggestions.",
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
