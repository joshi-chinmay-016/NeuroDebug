"""Custom exceptions for NeuroDebug."""

from typing import Optional


class NeuroDebugError(Exception):
    """Base exception for NeuroDebug errors."""

    def __init__(self, message: str, detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class LLMError(NeuroDebugError):
    """Exception raised when LLM operations fail."""

    def __init__(self, message: str, error_type: str = "llm_error", detail: Optional[str] = None):
        self.error_type = error_type
        super().__init__(message, detail)


class ValidationError(NeuroDebugError):
    """Exception raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


class AnalysisError(NeuroDebugError):
    """Exception raised during code analysis."""

    pass


class PatchGenerationError(NeuroDebugError):
    """Exception raised during patch generation."""

    pass
