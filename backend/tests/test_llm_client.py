"""
Unit tests for the LLM client abstraction and Prompt Builder (backend/llm/).
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from openai import APIConnectionError, AuthenticationError, RateLimitError

from llm.client import GroqClient
from llm.prompt_builder import PromptBuilder
from models.errors import LLMError


class TestGroqClient:
    """Test suite for GroqClient LLM abstraction."""

    def test_init_without_key(self):
        """Test initialization without any API key."""
        with patch("utils.config.Config.GROQ_API_KEY", None):
            client = GroqClient(api_key=None)
            assert client.is_available() is False
            assert client.client is None

    def test_init_invalid_key_format(self):
        """Test initialization with key not starting with 'gsk_'."""
        with pytest.raises(LLMError) as exc_info:
            GroqClient(api_key="invalid_format_key_12345")
        assert exc_info.value.error_type == "invalid_key"

    def test_init_valid_key(self):
        """Test initialization with valid gsk_ key format."""
        client = GroqClient(api_key="gsk_valid_test_key_12345")
        assert client.is_available() is True
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_generate_patch_success(self):
        """Test successful patch generation with markdown fences stripped."""
        client = GroqClient(api_key="gsk_test_mock_key")
        
        mock_choice = MagicMock()
        mock_choice.message.content = "```python\nx = 42\nprint(x)\n```"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            issues = [{"rule_id": "R002", "severity": "error", "category": "UndefinedVariable", "message": "undefined"}]
            patch_code = await client.generate_patch("print(x)", issues)

            assert patch_code == "x = 42\nprint(x)"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_patch_auth_error(self):
        """Test authentication error handling."""
        client = GroqClient(api_key="gsk_test_mock_key")

        with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = AuthenticationError(
                message="Invalid API Key",
                response=MagicMock(status_code=401, headers={}),
                body={"error": "auth failed"},
            )

            with pytest.raises(LLMError) as exc_info:
                await client.generate_patch("code", [])
            assert exc_info.value.error_type == "auth_error"

    @pytest.mark.asyncio
    async def test_generate_patch_rate_limit_error(self):
        """Test rate limit error handling."""
        client = GroqClient(api_key="gsk_test_mock_key")

        with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429, headers={}),
                body={"error": "rate limit"},
            )

            with pytest.raises(LLMError) as exc_info:
                await client.generate_patch("code", [])
            assert exc_info.value.error_type == "rate_limit"

    @pytest.mark.asyncio
    async def test_generate_analysis_success(self):
        """Test successful JSON analysis generation."""
        client = GroqClient(api_key="gsk_test_mock_key")

        mock_choice = MagicMock()
        mock_choice.message.content = """```json
{
  "error_type": "UndefinedVariable",
  "explanation": "Variable x was used without initialization",
  "suggested_fix": "Initialize x = 0 before use",
  "confidence_score": 0.95
}
```"""
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            analysis = await client.generate_analysis("print(x)", [])
            assert analysis["error_type"] == "UndefinedVariable"
            assert analysis["confidence_score"] == 0.95
            assert "x" in analysis["explanation"]

    def test_parse_code_response_fences(self):
        """Test code response parser with various fence styles."""
        assert GroqClient._parse_code_response("```python\nx = 1\n```") == "x = 1"
        assert GroqClient._parse_code_response("```\nx = 2\n```") == "x = 2"
        assert GroqClient._parse_code_response("x = 3") == "x = 3"


class TestPromptBuilder:
    """Test suite for PromptBuilder."""

    def test_build_patch_prompt_contains_code_and_issues(self):
        """Test that patch prompt includes code and formatted symbolic findings."""
        code = "print(undefined_val)"
        issues = [
            {"rule_id": "R002", "severity": "error", "category": "UndefinedVariable", "message": "undefined_val not found", "line": 1}
        ]
        prompt = PromptBuilder.build_patch_prompt(code, issues)
        assert "print(undefined_val)" in prompt
        assert "R002" in prompt
        assert "UndefinedVariable" in prompt

    def test_build_analysis_prompt_contains_code_and_issues(self):
        """Test that analysis prompt includes code and issues."""
        code = "val = 10 / 0"
        issues = [
            {"rule_id": "R006", "severity": "error", "category": "DivisionByZero", "message": "Literal division by zero", "line": 1}
        ]
        prompt = PromptBuilder.build_analysis_prompt(code, issues)
        assert "val = 10 / 0" in prompt
        assert "DivisionByZero" in prompt
