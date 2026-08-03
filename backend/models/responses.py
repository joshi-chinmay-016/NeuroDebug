"""Response models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List


class SymbolicIssue(BaseModel):
    """Model for a symbolic analysis issue."""

    rule_id: str = Field(..., description="Rule identifier")
    severity: str = Field(..., description="Severity level: error, warning, info")
    category: str = Field(..., description="Issue category")
    message: str = Field(..., description="Issue description")
    line: Optional[int] = Field(None, description="Line number if applicable")


class PatchResponse(BaseModel):
    """Model for patch generation response."""

    original_code: str = Field(..., description="Original code")
    patched_code: str = Field(..., description="Generated patch")
    unified_diff: str = Field(..., description="Unified diff format")
    validation_passed: bool = Field(..., description="Whether patch passes syntax validation")
    validation_error: Optional[str] = Field(None, description="Validation error if any")


class DebugResponse(BaseModel):
    """Response model for debug endpoint."""

    detected_issues: List[SymbolicIssue] = Field(default_factory=list, description="Issues detected by analysis")
    candidate_patch: Optional[PatchResponse] = Field(None, description="Generated patch if available")
    error_type: str = Field(..., description="Type of error detected")
    explanation: str = Field(..., description="Explanation of the issue")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the analysis")
    patch_status: str = Field(..., description="Status of patch generation")
    validation_result: str = Field(..., description="Result of patch validation")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "detected_issues": [
                    {
                        "rule_id": "R002",
                        "severity": "error",
                        "category": "UndefinedVariable",
                        "message": "Name 'undefined_var' is used but never defined",
                        "line": None
                    }
                ],
                "candidate_patch": {
                    "original_code": "x = undefined_var\nprint(x)",
                    "patched_code": "x = 'some value'\nprint(x)",
                    "unified_diff": "--- a/original.py\n+++ b/patched.py\n@@ -1,2 +1,2 @@\n-x = undefined_var\n+x = 'some value'\n print(x)",
                    "validation_passed": True,
                    "validation_error": None
                },
                "error_type": "UndefinedVariable",
                "explanation": "The name 'undefined_var' is used on line 1 but was never defined",
                "confidence_score": 0.95,
                "patch_status": "generated",
                "validation_result": "valid",
                "metadata": {
                    "ast_duration_ms": 15,
                    "llm_duration_ms": 1250,
                    "validation_duration_ms": 5
                }
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
