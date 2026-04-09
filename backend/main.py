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
from llm_engine import get_llm_analysis, generate_test_cases
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
    api_key: str | None = None   # user supplies their own Groq key


class DebugResponse(BaseModel):
    error_type: str
    explanation: str
    suggested_fix: str
    confidence_score: float
    symbolic_issues: list
    raw_errors: list


class TestGenerationRequest(BaseModel):
    code: str
    api_key: str | None = None   # user supplies their own Groq key


class TestCase(BaseModel):
    test_name: str
    test_code: str
    description: str


class TestGenerationResponse(BaseModel):
    test_cases: list[TestCase]
    imports: str
    setup_code: str
    success: bool
    error: str | None = None


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


# ──────────────────────────────────────────────────────────────────
# Test Generation Endpoint
# ──────────────────────────────────────────────────────────────────
@app.post("/generate-tests", response_model=TestGenerationResponse)
async def generate_tests(request: TestGenerationRequest):
    """
    Generate pytest test cases for the provided code.

    Uses LLM-powered analysis to create comprehensive test coverage.
    """
    code = request.code.strip()

    if not code:
        return JSONResponse(
            status_code=400,
            content={"detail": "Code input must not be empty."},
        )

    logger.info("=== New test generation request received (%d chars) ===", len(code))

    # Check for syntax errors via AST parsing
    ast_result = analyze_code_ast(code)
    if not ast_result.get("success"):
        return JSONResponse(
            status_code=400,
            content={"detail": f"Syntax error in code: {ast_result.get('syntax_error')}"},
        )

    logger.info("Code syntax validated. Generating test cases…")

    # Call LLM for test generation
    llm_result = await generate_test_cases(code, api_key=request.api_key)

    if not llm_result.get("success"):
        error_msg = llm_result.get("error", "Failed to generate test cases.")
        logger.error("Test generation failed: %s", error_msg)
        return JSONResponse(
            status_code=500,
            content={"detail": error_msg},
        )

    # Transform the LLM result into proper response format
    test_cases = []
    for tc in llm_result.get("test_cases", []):
        test_cases.append(
            TestCase(
                test_name=tc.get("test_name", "unnamed_test"),
                test_code=tc.get("test_code", ""),
                description=tc.get("description", ""),
            )
        )

    logger.info("Test generation complete. Generated %d test cases.", len(test_cases))

    return TestGenerationResponse(
        test_cases=test_cases,
        imports=llm_result.get("imports", "import pytest"),
        setup_code=llm_result.get("setup_code", ""),
        success=True,
        error=None,
    )
