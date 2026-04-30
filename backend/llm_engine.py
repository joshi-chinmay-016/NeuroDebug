"""
NeuroDebug - Neural Layer (LLM Engine)

<<<<<<< HEAD
Sends the user's code plus symbolic findings to the Groq Chat API and returns
a structured explanation plus suggested fix.
=======
Sends the user's code plus symbolic findings to the Groq API
and returns a structured explanation + suggested fix.
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce
"""

import json
import logging
import os
from typing import Any

<<<<<<< HEAD
import openai
=======
import groq
from groq import AsyncGroq
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce
from dotenv import load_dotenv
from openai import AsyncOpenAI

<<<<<<< HEAD
load_dotenv()

logger = logging.getLogger("neurodebug.llm")

GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
_server_key = os.getenv("GROQ_API_KEY", "").strip()
=======
load_dotenv()  # load GROQ_API_KEY from .env

logger = logging.getLogger("neurodebug.llm")

# Server-level fallback client (used only if user doesn't supply a key)
_server_key = os.getenv("GROQ_API_KEY", "")
_server_client = AsyncGroq(api_key=_server_key) if _server_key else None

# ──────────────────────────────────────────────────────────────────
# Prompt templates
# ──────────────────────────────────────────────────────────────────
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce

_SYSTEM_PROMPT = """You are NeuroDebug, an expert Python code analyser and debugger.
You combine symbolic AST analysis with deep reasoning to help developers fix their code.

Your response MUST be valid JSON with exactly these keys:
{
<<<<<<< HEAD
  "error_type": "<concise category, e.g. 'SyntaxError', 'LogicError', 'Clean'>",
  "explanation": "<detailed explanation of what is wrong and why>",
  "suggested_fix": "<corrected code or description of fix>",
  "confidence_score": <float 0.0-1.0>
=======
  "error_type":        "<concise category, e.g. 'SyntaxError', 'LogicError', 'Clean'>",
  "explanation":       "<detailed explanation of what is wrong and why>",
  "suggested_fix":     "<the entire corrected Python code snippet, properly formatted line-by-line>",
  "confidence_score":  <float 0.0–1.0>
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce
}

Rules:
- If the code looks correct, set error_type to "Clean" and confidence_score to 0.95+.
- confidence_score reflects how certain you are that the issues you identified are real.
- suggested_fix MUST contain the exact, corrected Python code formatted cleanly. Do not write a prose description here; only output the actual fixed code.
- Be concise but thorough. Avoid hallucinating bugs that don't exist.
"""


async def get_llm_analysis(
    code: str,
    symbolic_issues: list[dict],
    api_key: str | None = None,
) -> dict[str, Any]:
    """
<<<<<<< HEAD
    Call Groq and return a parsed JSON response.
=======
    Call Groq and return parsed JSON response.
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce

    Key resolution order:
      1. User-supplied key from the request body.
      2. Server GROQ_API_KEY from backend/.env.
      3. Symbolic-only fallback if no key is available.
    """
    key_to_use = (api_key or "").strip() or _server_key

    if not key_to_use:
        logger.warning("No Groq API key provided; returning symbolic fallback.")
        return _fallback_response(symbolic_issues)

<<<<<<< HEAD
    if not key_to_use.startswith("gsk_"):
        return _error_response(
            "That doesn't look like a valid Groq key. Groq keys usually start with 'gsk_'."
        )

    client = AsyncOpenAI(api_key=key_to_use, base_url=GROQ_BASE_URL)
=======
    # Validate key looks plausible before hitting the API
    if not key_to_use.startswith("gsk_"):
        return _error_response(
            "That doesn't look like a valid Groq key (should start with 'gsk_'). "
            "Please check and try again."
        )

    # Build a request-scoped client so each user is billed to their own account
    client = AsyncGroq(api_key=key_to_use)
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce
    source = "user_key" if (api_key or "").strip() else "server_key"
    logger.info("Groq LLM call using %s with model %s", source, GROQ_MODEL)

    try:
        response = await client.chat.completions.create(
<<<<<<< HEAD
            model=GROQ_MODEL,
=======
            model="llama-3.1-8b-instant",
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce
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
<<<<<<< HEAD
    except openai.AuthenticationError:
        logger.error("Groq authentication failed.")
        return _error_response("Invalid Groq API key. Please double-check the key you entered.")
    except openai.RateLimitError:
        logger.error("Groq rate limit exceeded.")
        return _error_response("Groq rate limit exceeded on your key. Try again in a moment.")
    except openai.APIConnectionError as exc:
=======

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
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce
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
<<<<<<< HEAD
        "error_type": top["category"],
        "explanation": f"(LLM unavailable) Symbolic analysis: {top['message']}",
        "suggested_fix": "Fix the reported symbolic issues. Add GROQ_API_KEY for AI-powered suggestions.",
=======
        "error_type":       top["category"],
        "explanation":      f"(LLM unavailable) Symbolic analysis: {top['message']}",
        "suggested_fix":    "Fix the reported symbolic issues. Add GROQ_API_KEY for AI-powered suggestions.",
>>>>>>> e7698b0119407c2ead5d7fa76051f343e28ff1ce
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
