"""
NeuroDebug Backend - Main Application Entry Point

FastAPI server with clean architecture for neuro-symbolic code debugging.
"""

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from routes import debug_router
from utils.config import Config
from utils.logging import configure_logging, get_logger

# ──────────────────────────────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────────────────────────────
configure_logging(Config.LOG_LEVEL)
logger = get_logger("neurodebug.main")

# ──────────────────────────────────────────────────────────────────
# App Initialisation
# ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title=Config.APP_NAME,
    description="Neuro-Symbolic AI Code Debugger — combines AST analysis with LLM reasoning for candidate patch generation",
    version=Config.APP_VERSION,
)

# CORS — allow the React dev server and any production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(debug_router, tags=["debug"])


# ──────────────────────────────────────────────────────────────────
# Middleware — request timing and request ID
# ──────────────────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to add request ID and log request timing."""
    # Add request ID if not present
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id

    start = time.time()
    response = await call_next(request)
    duration = round(time.time() - start, 4)

    logger.info(
        "%s %s → %s (%.4fs) [request_id=%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration,
        request_id,
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    return response


# ──────────────────────────────────────────────────────────────────
# Root endpoint
# ──────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }
