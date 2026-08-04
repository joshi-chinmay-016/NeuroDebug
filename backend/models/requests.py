"""Request models for API endpoints."""

from typing import ClassVar

from pydantic import BaseModel, Field


class DebugRequest(BaseModel):
    """Request model for debug endpoint."""

    code: str = Field(..., min_length=1, description="Python code to analyze")
    api_key: str | None = Field(None, description="User's Groq API key")

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {"code": "x = undefined_var\nprint(x)", "api_key": "gsk_..."}
        }


class VerificationRequest(BaseModel):
    """Request model for verification endpoint."""

    original_code: str = Field(..., min_length=1, description="Original Python code")
    patched_code: str = Field(..., min_length=1, description="Patched Python code")
    test_code: str | None = Field(None, description="Optional pytest test code")

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "original_code": "x = undefined_var\nprint(x)",
                "patched_code": "x = 'some value'\nprint(x)",
                "test_code": "def test_x_defined():\n    assert x is not None",
            }
        }
