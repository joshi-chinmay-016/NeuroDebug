"""
Debug Service - Orchestration Layer.

Orchestrates the entire debug pipeline using the new DebugPipeline orchestration layer.
"""

from llm.client import GroqClient
from models.responses import DebugResponse
from services.debug_pipeline import DebugPipeline
from utils.logging import get_logger

logger = get_logger("neurodebug.debug_service")


class DebugService:
    """Orchestrates the complete debug pipeline."""

    def __init__(self, llm_client: GroqClient | None = None):
        """
        Initialize the debug service.

        Args:
            llm_client: Optional GroqClient instance. If not provided, creates one per request.
        """
        self.llm_client = llm_client
        self.pipeline = DebugPipeline(llm_client=llm_client)

    async def debug_code(
        self,
        code: str,
        api_key: str | None = None,
        test_code: str | None = None,
    ) -> DebugResponse:
        """
        Execute the complete debug pipeline.

        Delegates to DebugPipeline for orchestration.

        Args:
            code: The Python code to debug.
            api_key: Optional user-provided Groq API key.
            test_code: Optional pytest verification suite.

        Returns:
            DebugResponse with analysis results and patch if available.
        """
        return await self.pipeline.execute(
            code=code,
            api_key=api_key,
            test_code=test_code,
        )
