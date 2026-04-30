"""
NeuroDebug - Neural Layer (LLM Engine)

Sends the user's code plus symbolic findings to the Groq Chat API and returns
a structured explanation plus suggested fix.
"""

import json
import logging
import os
from typing import Any

import openai
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

logger = logging.getLogger("neurodebug.llm")

GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
_server_key = os.getenv("GROQ_API_KEY", "").strip()

_SYSTEM_PROMPT = """You are NeuroDebug, an expert Python code analyser and debugger.
You combine symbolic AST analysis with deep reasoning to help developers fix their code.

Your response MUST be valid JSON with exactly these keys:
{
  "error_type": "<concise category, e.g. 'SyntaxError', 'LogicError', 'Clean'>",
  "explanation": "<detailed explanation of what is wrong and why>",
  "suggested_fix": "<corrected code or description of fix>",
  "confidence_score": <float 0.0-1.0>
}

Rules:
- If the code looks correct, set error_type to "Clean" and confidence_score to 0.95+.
- confidence_score reflects how certain you are that the issues you identified are real.
- suggested_fix should contain the corrected Python code when possible.
- Be concise but thorough. Avoid hallucinating bugs that don't exist.
"""


async def get_llm_analysis(
    code: str,
    symbolic_issues: list[dict],
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Call Groq and return a parsed JSON response.

    Key resolution order:
      1. User-supplied key from the request body.
      2. Server GROQ_API_KEY from backend/.env.
      3. Symbolic-only fallback if no key is available.
    """
    key_to_use = (api_key or "").strip() or _server_key

    if not key_to_use:
        logger.warning("No Groq API key provided; returning symbolic fallback.")
        return _fallback_response(symbolic_issues)

    if not key_to_use.startswith("gsk_"):
        return _error_response(
            "That doesn't look like a valid Groq key. Groq keys usually start with 'gsk_'."
        )

    client = AsyncOpenAI(api_key=key_to_use, base_url=GROQ_BASE_URL)
    source = "user_key" if (api_key or "").strip() else "server_key"
    logger.info("Groq LLM call using %s with model %s", source, GROQ_MODEL)

    try:
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(code, symbolic_issues)},
            ],
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        logger.debug("Raw Groq response: %s", raw[:200])
        return _parse_llm_response(raw)
    except openai.AuthenticationError:
        logger.error("Groq authentication failed.")
        return _error_response("Invalid Groq API key. Please double-check the key you entered.")
    except openai.RateLimitError:
        logger.error("Groq rate limit exceeded.")
        return _error_response("Groq rate limit exceeded on your key. Try again in a moment.")
    except openai.APIConnectionError as exc:
        logger.error("Groq connection error: %s", exc)
        return _error_response(f"Could not connect to Groq: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected Groq LLM error: %s", exc)
        return _fallback_response(symbolic_issues)


def _build_user_prompt(code: str, symbolic_issues: list[dict]) -> str:
    if symbolic_issues:
        issues_text = "\n\nSymbolic analysis found these issues:\n"
        for issue in symbolic_issues:
            severity = issue.get("severity", "info").upper()
            rule_id = issue.get("rule_id", "?")
            message = issue.get("message", "")
            issues_text += f"  [{severity}] ({rule_id}) {message}\n"
    else:
        issues_text = "\n\nSymbolic analysis found no issues."

    return f"""Please analyse the following Python code:{issues_text}

```python
{code}
```

Return only valid JSON."""


def _parse_llm_response(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
        return {
            "error_type": str(data.get("error_type", "Unknown")),
            "explanation": str(data.get("explanation", "")),
            "suggested_fix": str(data.get("suggested_fix", "")),
            "confidence_score": float(data.get("confidence_score", 0.5)),
            "source": "llm",
        }
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse Groq JSON: %s", exc)
        return _error_response("Groq returned malformed JSON.")


def _fallback_response(symbolic_issues: list[dict]) -> dict[str, Any]:
    """Synthesize a response from symbolic data when the LLM is unavailable."""
    if not symbolic_issues:
        return {
            "error_type": "Clean",
            "explanation": "No issues detected by the symbolic analyser.",
            "suggested_fix": "Code appears correct.",
            "confidence_score": 0.75,
            "source": "symbolic_fallback",
        }

    error_issues = [issue for issue in symbolic_issues if issue["severity"] == "error"]
    top = error_issues[0] if error_issues else symbolic_issues[0]

    return {
        "error_type": top["category"],
        "explanation": f"(LLM unavailable) Symbolic analysis: {top['message']}",
        "suggested_fix": "Fix the reported symbolic issues. Add GROQ_API_KEY for AI-powered suggestions.",
        "confidence_score": 0.6,
        "source": "symbolic_fallback",
    }


def _error_response(msg: str) -> dict[str, Any]:
    return {
        "error_type": "LLMError",
        "explanation": msg,
        "suggested_fix": "Please check your Groq API key, model, and network connection.",
        "confidence_score": 0.0,
        "source": "error",
    }
