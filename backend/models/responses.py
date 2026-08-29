"""Response models for API endpoints."""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class SymbolicIssue(BaseModel):
    """Represents a symbolic analysis issue."""

    rule_id: str = Field(..., description="Rule identifier")
    severity: str = Field(..., description="Severity level: error, warning, info")
    category: str = Field(..., description="Issue category")
    message: str = Field(..., description="Issue description")
    line: int | None = Field(None, description="Line number if applicable")


class PatchResponse(BaseModel):
    """Model for patch generation response."""

    original_code: str = Field(..., description="Original code")
    patched_code: str = Field(..., description="Generated patch")
    unified_diff: str = Field(..., description="Unified diff format")
    validation_passed: bool = Field(
        ..., description="Whether patch passes syntax validation"
    )
    validation_error: str | None = Field(None, description="Validation error if any")


class ExecutionResultResponse(BaseModel):
    """Response model for execution result."""

    success: bool = Field(..., description="Whether execution succeeded")
    exit_code: int | None = Field(None, description="Process exit code")
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    execution_time: float = Field(..., description="Execution time in seconds")
    timeout_occurred: bool = Field(..., description="Whether execution timed out")
    traceback: str | None = Field(None, description="Traceback if error occurred")


class TestResultResponse(BaseModel):
    """Response model for a single test result."""

    test_name: str = Field(..., description="Test name")
    passed: bool = Field(..., description="Whether test passed")
    failed: bool = Field(..., description="Whether test failed")
    skipped: bool = Field(..., description="Whether test was skipped")
    duration: float = Field(..., description="Test duration in seconds")
    error_message: str | None = Field(None, description="Error message if failed")

    model_config = ConfigDict(extra="ignore")


class TestSuiteResultResponse(BaseModel):
    """Response model for test suite results."""

    total_tests: int = Field(..., description="Total number of tests")
    passed: int = Field(..., description="Number of passed tests")
    failed: int = Field(..., description="Number of failed tests")
    skipped: int = Field(..., description="Number of skipped tests")
    duration: float = Field(..., description="Total test duration in seconds")
    test_results: list[TestResultResponse] = Field(
        default_factory=list, description="Individual test results"
    )
    output: str = Field(..., description="Test output")
    error: str | None = Field(None, description="Error if test execution failed")

    model_config = ConfigDict(extra="ignore")


class VerificationEvidenceResponse(BaseModel):
    """Response model for verification evidence."""

    original_code_execution: ExecutionResultResponse = Field(
        ..., description="Original code execution result"
    )
    patched_code_execution: ExecutionResultResponse = Field(
        ..., description="Patched code execution result"
    )
    test_results: TestSuiteResultResponse | None = Field(
        None, description="Test suite results if available"
    )
    execution_comparison: dict = Field(
        default_factory=dict, description="Execution comparison metrics"
    )


class VerificationReportResponse(BaseModel):
    """Response model for verification report."""

    verification_status: str = Field(..., description="VERIFIED or UNVERIFIED")
    execution_summary: str = Field(..., description="Human-readable execution summary")
    runtime: float = Field(..., description="Total verification runtime in seconds")
    failure_reason: str | None = Field(
        None, description="Reason for verification failure"
    )
    evidence: VerificationEvidenceResponse = Field(
        ..., description="Verification evidence"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "verification_status": "VERIFIED",
                "execution_summary": "Verification Status: VERIFIED\nOriginal Code: FAILED\nPatched Code: SUCCESS\nTests: 3 passed, 0 failed, 0 skipped\nOriginal execution time: 0.001s\nPatched execution time: 0.002s",
                "runtime": 1.234,
                "failure_reason": None,
                "evidence": {
                    "original_code_execution": {
                        "success": False,
                        "exit_code": 1,
                        "stdout": "",
                        "stderr": "NameError: name 'undefined_var' is not defined",
                        "execution_time": 0.001,
                        "timeout_occurred": False,
                        "traceback": None,
                    },
                    "patched_code_execution": {
                        "success": True,
                        "exit_code": 0,
                        "stdout": "some value\n",
                        "stderr": "",
                        "execution_time": 0.002,
                        "timeout_occurred": False,
                        "traceback": None,
                    },
                    "test_results": {
                        "total_tests": 3,
                        "passed": 3,
                        "failed": 0,
                        "skipped": 0,
                        "duration": 0.5,
                        "test_results": [],
                        "output": "",
                        "error": None,
                    },
                    "execution_comparison": {
                        "original_success": False,
                        "patched_success": True,
                        "success_improved": True,
                        "success_regressed": False,
                    },
                },
            }
        }
    )


class AgreementSignalResponse(BaseModel):
    """Response model for AST / LLM agreement signal."""

    agreement_score: float = Field(..., ge=0.0, le=1.0, description="Agreement score between AST and LLM")
    consensus_status: str = Field(..., description="Consensus classification")
    matched_issues_count: int = Field(0, description="Number of matched issues")
    calibrated_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Calibrated confidence score")
    synthesis_summary: str = Field("", description="Summary of agreement/disagreement")


class CandidateEvaluationResponse(BaseModel):
    """Response model for candidate patch evaluations."""

    candidate_id: str = Field(..., description="Unique candidate ID")
    source: str = Field(..., description="Source of candidate: llm | deterministic | rule_engine")
    patched_code: str = Field(..., description="Patched code string")
    diff: str = Field(..., description="Unified diff")
    validation_passed: bool = Field(..., description="Whether syntax validation passed")
    verification_status: str = Field(..., description="Verification status")
    evidence_score: float = Field(0.0, description="Evidence score 0-100")
    rank: int = Field(0, description="Rank position")
    selection_reason: str = Field("", description="Why this candidate was chosen/ranked")


class DebugResponse(BaseModel):
    """Response model for debug endpoint."""

    detected_issues: list[SymbolicIssue] = Field(
        default_factory=list, description="Issues detected by analysis"
    )
    candidate_patch: PatchResponse | None = Field(
        None, description="Generated patch if available"
    )
    error_type: str = Field(..., description="Type of error detected")
    explanation: str = Field(..., description="Explanation of the issue")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the analysis"
    )
    patch_status: str = Field(..., description="Status of patch generation")
    validation_result: str = Field(..., description="Result of patch validation")
    verification_report: VerificationReportResponse | None = Field(
        None, description="Verification report if patch was verified"
    )
    agreement_signal: AgreementSignalResponse | None = Field(
        None, description="AST / LLM consensus agreement signal"
    )
    ranked_candidates: list[CandidateEvaluationResponse] = Field(
        default_factory=list, description="All evaluated and ranked candidate patches"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    usage_info: dict | None = Field(
        None, description="Usage information (remaining requests, tier, etc.)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detected_issues": [
                    {
                        "rule_id": "R002",
                        "severity": "error",
                        "category": "UndefinedVariable",
                        "message": "Name 'undefined_var' is used but never defined",
                        "line": None,
                    }
                ],
                "candidate_patch": {
                    "original_code": "x = undefined_var\nprint(x)",
                    "patched_code": "x = 'some value'\nprint(x)",
                    "unified_diff": "--- a/original.py\n+++ b/patched.py\n@@ -1,2 +1,2 @@\n-x = undefined_var\n+x = 'some value'\n print(x)",
                    "validation_passed": True,
                    "validation_error": None,
                },
                "error_type": "UndefinedVariable",
                "explanation": "The name 'undefined_var' is used on line 1 but was never defined",
                "confidence_score": 0.95,
                "patch_status": "generated",
                "validation_result": "valid",
                "metadata": {
                    "ast_duration_ms": 15,
                    "llm_duration_ms": 1250,
                    "validation_duration_ms": 5,
                },
            }
        }
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
