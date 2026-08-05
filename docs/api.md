# API Documentation

## Overview

NeuroDebug provides a RESTful API built with FastAPI. All endpoints return JSON responses and include comprehensive error handling.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.neurodebug.com`

## Authentication

### Guest Access

No authentication required for basic debugging with rate limits.

### Authenticated Access

Session-based authentication for registered users.

```http
Cookie: neurodebug_session=<session_id>
```

## Common Headers

```http
Content-Type: application/json
X-Request-ID: <request_id>
```

## Response Format

All responses follow this structure:

```json
{
  "data": { ... },
  "usage_info": {
    "remaining_requests": 3,
    "daily_limit": 5,
    "tier": "free",
    "session_id": "abc123"
  }
}
```

## Endpoints

### Health Check

Check API health status.

```http
GET /health
```

**Response**:

```json
{
  "status": "healthy",
  "service": "NeuroDebug API",
  "version": "1.0.0"
}
```

### Debug Code

Main debugging endpoint with session management and usage limiting.

```http
POST /debug
```

**Request Body**:

```json
{
  "code": "def example():\n    return undefined_var",
  "api_key": "gsk_..."
}
```

**Parameters**:

- `code` (string, required): Python code to debug
- `api_key` (string, optional): Groq API key for LLM features

**Response**:

```json
{
  "detected_issues": [
    {
      "rule_id": "R002",
      "severity": "error",
      "category": "UndefinedVariable",
      "message": "Name 'undefined_var' is used but never defined",
      "line": 2
    }
  ],
  "candidate_patch": {
    "original_code": "def example():\n    return undefined_var",
    "patched_code": "def example():\n    return None",
    "unified_diff": "--- a/original.py\n+++ b/patched.py\n@@ -1,2 +1,2 @@\n-def example():\n-    return undefined_var\n+    return None",
    "validation_passed": true,
    "validation_error": null
  },
  "error_type": "UndefinedVariable",
  "explanation": "The name 'undefined_var' is used on line 2 but was never defined",
  "confidence_score": 0.95,
  "patch_status": "generated",
  "validation_result": "valid",
  "verification_report": {
    "verification_status": "VERIFIED",
    "execution_summary": "Verification Status: VERIFIED\nOriginal Code: FAILED\nPatched Code: SUCCESS",
    "runtime": 1.234,
    "failure_reason": null,
    "evidence": {
      "original_code_execution": {
        "success": false,
        "exit_code": 1,
        "stdout": "",
        "stderr": "NameError: name 'undefined_var' is not defined",
        "execution_time": 0.001,
        "timeout_occurred": false,
        "traceback": null
      },
      "patched_code_execution": {
        "success": true,
        "exit_code": 0,
        "stdout": "None\n",
        "stderr": "",
        "execution_time": 0.001,
        "timeout_occurred": false,
        "traceback": null
      },
      "test_results": null,
      "execution_comparison": {
        "original_success": false,
        "patched_success": true,
        "success_improved": true,
        "success_regressed": false
      }
    }
  },
  "metadata": {
    "ast_duration_ms": 15.23,
    "rule_duration_ms": 8.45,
    "llm_duration_ms": 1250.67,
    "patch_generation_duration_ms": 450.12,
    "verification_duration_ms": 1234.56,
    "pipeline_duration_ms": 2958.03
  },
  "usage_info": {
    "remaining_requests": 2,
    "daily_limit": 5,
    "tier": "free",
    "session_id": "abc123def456"
  }
}
```

**Error Responses**:

**422 Unprocessable Entity** (Analysis Error):

```json
{
  "error": "analysis_error",
  "message": "AST analysis failed: invalid syntax"
}
```

**429 Too Many Requests** (Usage Limit Exceeded):

```json
{
  "error": "usage_limit_exceeded",
  "message": "Daily usage limit exceeded: 5/5 requests",
  "tier": "free",
  "limit": 5,
  "current_usage": 5
}
```

**500 Internal Server Error**:

```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred"
}
```

### Verify Patch

Standalone verification endpoint for patch execution.

```http
POST /verify
```

**Request Body**:

```json
{
  "original_code": "def example():\n    return undefined_var",
  "patched_code": "def example():\n    return None",
  "test_code": "def test_example():\n    assert example() is None"
}
```

**Parameters**:

- `original_code` (string, required): Original Python code
- `patched_code` (string, required): Patched Python code
- `test_code` (string, optional): Test code for verification

**Response**:

```json
{
  "verification_status": "VERIFIED",
  "execution_summary": "Verification Status: VERIFIED\nOriginal Code: FAILED\nPatched Code: SUCCESS\nTests: 1 passed, 0 failed",
  "runtime": 1.234,
  "failure_reason": null,
  "evidence": {
    "original_code_execution": {
      "success": false,
      "exit_code": 1,
      "stdout": "",
      "stderr": "NameError: name 'undefined_var' is not defined",
      "execution_time": 0.001,
      "timeout_occurred": false,
      "traceback": null
    },
    "patched_code_execution": {
      "success": true,
      "exit_code": 0,
      "stdout": "None\n",
      "stderr": "",
      "execution_time": 0.001,
      "timeout_occurred": false,
      "traceback": null
    },
    "test_results": {
      "total_tests": 1,
      "passed": 1,
      "failed": 0,
      "skipped": 0,
      "duration": 0.5,
      "test_results": [
        {
          "test_name": "test_example",
          "passed": true,
          "failed": false,
          "skipped": false,
          "duration": 0.1,
          "error_message": null
        }
      ],
      "output": "",
      "error": null
    },
    "execution_comparison": {
      "original_success": false,
      "patched_success": true,
      "success_improved": true,
      "success_regressed": false
    }
  }
}
```

## Rate Limiting

### Tier-Based Limits

- **Guest**: 3 requests/day
- **Free**: 5 requests/day
- **Pro**: 20+ requests/day
- **Enterprise**: Unlimited

### Rate Limit Headers

```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1640995200
```

## Error Codes

| Status Code | Error Type | Description |
|------------|-----------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 422 | Analysis Error | Code analysis failed |
| 429 | Usage Limit Exceeded | Daily limit exceeded |
| 500 | Internal Error | Server error |

## Webhooks (Future)

### Verification Complete

```json
{
  "event": "verification.complete",
  "data": {
    "session_id": "abc123",
    "verification_status": "VERIFIED",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Usage Limit Reached

```json
{
  "event": "usage.limit_reached",
  "data": {
    "session_id": "abc123",
    "tier": "free",
    "limit": 5,
    "current_usage": 5,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## SDK Examples

### Python

```python
import requests

API_URL = "https://api.neurodebug.com"

def debug_code(code, api_key=None):
    response = requests.post(
        f"{API_URL}/debug",
        json={"code": code, "api_key": api_key}
    )
    return response.json()

result = debug_code("def example():\n    return undefined_var")
print(result["explanation"])
```

### JavaScript

```javascript
const API_URL = "https://api.neurodebug.com";

async function debugCode(code, apiKey) {
  const response = await fetch(`${API_URL}/debug`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ code, api_key: apiKey }),
  });
  return response.json();
}

const result = await debugCode("def example():\n    return undefined_var");
console.log(result.explanation);
```

### cURL

```bash
curl -X POST https://api.neurodebug.com/debug \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def example():\n    return undefined_var",
    "api_key": "gsk_..."
  }'
```

## Interactive Documentation

Interactive API documentation is available at:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

## Versioning

API versioning follows semantic versioning:

- Current version: `1.0.0`
- Version header: `X-API-Version: 1.0.0`

## Changelog

### v1.0.0 (Current)

- Initial release
- Debug endpoint with session management
- Usage limiting with tier-based limits
- Verification endpoint
- Comprehensive error handling
