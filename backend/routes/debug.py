"""
API routes for debug endpoints.

Contains route handlers that delegate business logic to services.
"""

from fastapi import APIRouter, HTTPException, Request

from models.errors import AnalysisError, NeuroDebugError
from models.requests import DebugRequest, VerificationRequest
from models.responses import (
    DebugResponse,
    HealthResponse,
    VerificationReportResponse,
)
from services.debug_service import DebugService
from services.verification_engine import VerificationEngine
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
    - Verification (if patch generated)

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


@router.post("/verify", response_model=VerificationReportResponse)
async def verify_patch(request: Request, verification_request: VerificationRequest):
    """
    Verification endpoint for patch execution verification.

    Executes original and patched code, runs tests if provided,
    and returns a structured verification report.

    Args:
        request: FastAPI request object.
        verification_request: VerificationRequest containing original code,
            patched code, and optional test code.

    Returns:
        VerificationReportResponse with verification status and evidence.
    """
    # Set request ID for logging
    request_id = request.headers.get("X-Request-ID", "")
    if request_id:
        set_request_id(request_id)

    original_code = verification_request.original_code.strip()
    patched_code = verification_request.patched_code.strip()

    # Validation
    if not original_code:
        raise HTTPException(status_code=400, detail="Original code cannot be empty.")

    if not patched_code:
        raise HTTPException(status_code=400, detail="Patched code cannot be empty.")

    if len(original_code) > Config.MAX_CODE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Original code exceeds maximum length of {Config.MAX_CODE_LENGTH} characters.",
        )

    if len(patched_code) > Config.MAX_CODE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Patched code exceeds maximum length of {Config.MAX_CODE_LENGTH} characters.",
        )

    logger.info(
        "Verification request received: original_len=%d patched_len=%d",
        len(original_code),
        len(patched_code),
    )

    try:
        # Initialize verification engine
        verification_engine = VerificationEngine()

        # Execute verification
        report = verification_engine.verify_patch(
            original_code=original_code,
            patched_code=patched_code,
            test_code=verification_request.test_code,
        )

        # Convert to API response model
        return _convert_verification_report_to_response(report)

    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        logger.exception("Unexpected error in verification endpoint")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred during verification",
            },
        )


def _convert_verification_report_to_response(
    report,
) -> VerificationReportResponse:
    """
    Convert internal VerificationReport to API response model.

    Args:
        report: Internal VerificationReport from VerificationEngine.

    Returns:
        VerificationReportResponse for API response.
    """
    from models.responses import (
        ExecutionResultResponse,
        TestResultResponse,
        TestSuiteResultResponse,
        VerificationEvidenceResponse,
    )

    # Convert execution results
    original_exec = ExecutionResultResponse(
        success=report.evidence.original_code_execution.success,
        exit_code=report.evidence.original_code_execution.exit_code,
        stdout=report.evidence.original_code_execution.stdout,
        stderr=report.evidence.original_code_execution.stderr,
        execution_time=report.evidence.original_code_execution.execution_time,
        timeout_occurred=report.evidence.original_code_execution.timeout_occurred,
        traceback=report.evidence.original_code_execution.traceback,
    )

    patched_exec = ExecutionResultResponse(
        success=report.evidence.patched_code_execution.success,
        exit_code=report.evidence.patched_code_execution.exit_code,
        stdout=report.evidence.patched_code_execution.stdout,
        stderr=report.evidence.patched_code_execution.stderr,
        execution_time=report.evidence.patched_code_execution.execution_time,
        timeout_occurred=report.evidence.patched_code_execution.timeout_occurred,
        traceback=report.evidence.patched_code_execution.traceback,
    )

    # Convert test results if available
    test_results_response = None
    if report.evidence.test_results:
        test_result_responses = [
            TestResultResponse(
                test_name=t.test_name,
                passed=t.passed,
                failed=t.failed,
                skipped=t.skipped,
                duration=t.duration,
                error_message=t.error_message,
            )
            for t in report.evidence.test_results.test_results
        ]

        test_results_response = TestSuiteResultResponse(
            total_tests=report.evidence.test_results.total_tests,
            passed=report.evidence.test_results.passed,
            failed=report.evidence.test_results.failed,
            skipped=report.evidence.test_results.skipped,
            duration=report.evidence.test_results.duration,
            test_results=test_result_responses,
            output=report.evidence.test_results.output,
            error=report.evidence.test_results.error,
        )

    # Build evidence response
    evidence_response = VerificationEvidenceResponse(
        original_code_execution=original_exec,
        patched_code_execution=patched_exec,
        test_results=test_results_response,
        execution_comparison=report.evidence.execution_comparison,
    )

    return VerificationReportResponse(
        verification_status=report.verification_status.value,
        execution_summary=report.execution_summary,
        runtime=report.runtime,
        failure_reason=report.failure_reason,
        evidence=evidence_response,
    )
