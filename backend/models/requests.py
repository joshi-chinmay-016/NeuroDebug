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
