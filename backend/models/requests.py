"""Request models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional


class DebugRequest(BaseModel):
    """Request model for debug endpoint."""

    code: str = Field(..., min_length=1, description="Python code to analyze")
    api_key: Optional[str] = Field(None, description="User's Groq API key")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "x = undefined_var\nprint(x)",
                "api_key": "gsk_..."
            }
        }
