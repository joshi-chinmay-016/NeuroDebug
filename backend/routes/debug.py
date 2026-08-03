"""
API routes for debug endpoints.

Contains route handlers that delegate business logic to services.
"""

from fastapi import APIRouter, HTTPException, Request

from models.errors import AnalysisError, NeuroDebugError
from models.requests import DebugRequest
from models.responses import DebugResponse, HealthResponse
from services.debug_service import DebugService
from utils.config import Config
from utils.logging import get_logger, set_request_id

logger = get_logger("neurodebug.routes")

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy", service=Config.APP_NAME, version=Config.APP_VERSION
    )


@router.post("/debug", response_model=DebugResponse)
async def debug_code(request: Request, debug_request: DebugRequest):
    """
    Main debugging endpoint.

    Orchestrates the complete debug pipeline:
    - AST Analysis
    - Rule Engine
    - LLM Analysis (if API key provided)
    - Patch Generation (if issues detected)
    - Patch Validation
    - Diff Generation

    Args:
        request: FastAPI request object.
        debug_request: DebugRequest containing code and optional API key.

    Returns:
        DebugResponse with analysis results and patch if available.
    """
    # Set request ID for logging
    request_id = request.headers.get("X-Request-ID", "")
    if request_id:
        set_request_id(request_id)

    code = debug_request.code.strip()

    # Validation
    if not code:
        raise HTTPException(status_code=400, detail="Code input must not be empty.")

    if len(code) > Config.MAX_CODE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Code exceeds maximum length of {Config.MAX_CODE_LENGTH} characters.",
        )

    logger.info("Debug request received: code_length=%d", len(code))

    try:
        # Initialize debug service
        debug_service = DebugService()

        # Execute debug pipeline
        result = await debug_service.debug_code(
            code=code, api_key=debug_request.api_key
        )

        return result

    except AnalysisError as exc:
        logger.error("Analysis error: %s", exc.message)
        raise HTTPException(
            status_code=422, detail={"error": "analysis_error", "message": exc.message}
        )

    except NeuroDebugError as exc:
        logger.error("NeuroDebug error: %s", exc.message)
        raise HTTPException(
            status_code=500, detail={"error": "service_error", "message": exc.message}
        )

    except Exception:
        logger.exception("Unexpected error in debug endpoint")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred",
            },
        )
