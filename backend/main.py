"""
NeuroDebug Backend - Main Application Entry Point

FastAPI server with clean architecture for neuro-symbolic code debugging.
Includes PostgreSQL integration, session management, and usage limiting.
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from database import close_db, init_db
from middleware.security import security_middleware
from routes import (
    analytics_router,
    auth_router,
    debug_router,
    history_router,
    profile_router,
    workspace_router,
)
from services.cache_service import cache_service
from utils.config import Config
from utils.logging import configure_logging, get_logger, set_request_id

# ──────────────────────────────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────────────────────────────
configure_logging(Config.LOG_LEVEL)
logger = get_logger("neurodebug.main")


# ──────────────────────────────────────────────────────────────────
# Lifecycle Management
# ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    logger.info("Starting NeuroDebug API...")
    await init_db()
    await cache_service.initialize()
    yield
    # Shutdown
    logger.info("Shutting down NeuroDebug API...")
    await close_db()
    await cache_service.close()
    logger.info("Database and cache connections closed")


# ──────────────────────────────────────────────────────────────────
# App Initialisation
# ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title=Config.APP_NAME,
    description="Neuro-Symbolic AI Code Debugger — combines AST analysis with LLM reasoning for candidate patch generation",
    version=Config.APP_VERSION,
    lifespan=lifespan,
)

# CORS — allow the React dev server, Vercel frontend, and production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://neuro-debug.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.middleware("http")(security_middleware)

# Include routes
app.include_router(debug_router, tags=["debug"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(workspace_router, prefix="/workspace", tags=["workspace"])
app.include_router(history_router, prefix="/history", tags=["history"])
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])


# ──────────────────────────────────────────────────────────────────
# Middleware — request timing and request ID
# ──────────────────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to add request ID and log request timing."""
    # Add request ID if not present
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id
    set_request_id(request_id)

    start = time.time()
    response = await call_next(request)
    duration = round(time.time() - start, 4)

    logger.info(
        "%s %s → %s (%.4fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
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
