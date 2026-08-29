"""
Tests for Safe Logging, Credential Redaction, and Pipeline Observability.
"""

from utils.logging import (
    PipelineTelemetry,
    get_request_id,
    sanitize_log_message,
    set_request_id,
)


def test_sanitize_log_message_redaction():
    """Verify regex masking of secrets and API keys."""
    groq_secret = "User submitted key gsk_abcdef1234567890abcdef1234567890 to header"
    sanitized = sanitize_log_message(groq_secret)
    assert "gsk_***REDACTED***" in sanitized
    assert "1234567890" not in sanitized

    bearer_token = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
    sanitized_bearer = sanitize_log_message(bearer_token)
    assert "Bearer ***REDACTED_TOKEN***" in sanitized_bearer

    db_url = "Connecting to postgresql://admin:supersecretpass@localhost:5432/mydb"
    sanitized_db = sanitize_log_message(db_url)
    assert "***REDACTED***" in sanitized_db
    assert "supersecretpass" not in sanitized_db


def test_request_id_context_propagation():
    """Verify request ID is correctly set and retrieved in context."""
    custom_id = "req_test_abc123"
    set_request_id(custom_id)
    assert get_request_id() == custom_id

    # Auto-generate if None
    new_id = set_request_id(None)
    assert len(new_id) > 10
    assert get_request_id() == new_id


def test_pipeline_telemetry_structure():
    """Verify telemetry dataclass initialization and timing storage."""
    telemetry = PipelineTelemetry(request_id="req_999")
    telemetry.ast_duration_ms = 1.5
    telemetry.rule_duration_ms = 0.8
    telemetry.total_duration_ms = 2.3
    telemetry.stages_completed.extend(["ast_analysis", "rule_engine"])

    assert telemetry.request_id == "req_999"
    assert telemetry.ast_duration_ms == 1.5
    assert len(telemetry.stages_completed) == 2
