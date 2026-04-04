"""
NeuroDebug Backend - Main Application Entry Point
FastAPI server combining symbolic AST analysis with LLM-based neural reasoning
"""

import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from parser import analyze_code_ast
from rules import apply_rules
from llm_engine import get_llm_analysis
from utils import merge_results, format_response

# ──────────────────────────────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("neurodebug")

# ──────────────────────────────────────────────────────────────────
# App Initialisation
# ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NeuroDebug API",
    description="Neuro-Symbolic AI Code Debugger — combines AST analysis with LLM reasoning",
    version="1.0.0",
)

# CORS — allow the React dev server and any production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────────────────────────
class DebugRequest(BaseModel):
    code: str
    api_key: str | None = None   # user supplies their own OpenAI key


class DebugResponse(BaseModel):
    error_type: str
    explanation: str
    suggested_fix: str
    confidence_score: float
    symbolic_issues: list
    raw_errors: list


# ──────────────────────────────────────────────────────────────────
# Middleware — request timing
# ──────────────────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round(time.time() - start, 4)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}s)")
    return response


# ──────────────────────────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "NeuroDebug API", "version": "1.0.0"}


# ──────────────────────────────────────────────────────────────────
# Core Debug Endpoint
# ──────────────────────────────────────────────────────────────────
@app.post("/debug", response_model=DebugResponse)
async def debug_code(request: DebugRequest):
    """
    Main debugging endpoint.

    Pipeline:
      1. Symbolic layer  — AST parsing + rule-based checks
      2. Neural layer    — LLM explanation & suggested fix
      3. Merge           — combine both outputs into a unified response
    """
    code = request.code.strip()

    if not code:
        return JSONResponse(
            status_code=400,
            content={"detail": "Code input must not be empty."},
        )

    logger.info("=== New debug request received (%d chars) ===", len(code))

    # Step 1 — Symbolic analysis (AST + rules)
    logger.info("Running symbolic analysis…")
    ast_result = analyze_code_ast(code)
    rule_issues = apply_rules(code, ast_result)
    logger.info("Symbolic issues found: %d", len(rule_issues))

    # Step 2 — Neural analysis (LLM)
    logger.info("Querying LLM engine…")
    llm_result = await get_llm_analysis(code, rule_issues, api_key=request.api_key)

    # Step 3 — Merge
    final = merge_results(ast_result, rule_issues, llm_result)
    logger.info("Debug complete. error_type=%s confidence=%.2f", final["error_type"], final["confidence_score"])

    return format_response(final)
