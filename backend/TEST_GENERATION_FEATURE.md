# Test Case Generation Feature

## Overview
NeuroDebug now includes an intelligent test case generation feature that automatically creates comprehensive pytest test cases based on your Python code. This feature uses the Groq LLM to analyze your code and generate diverse test cases covering:
- Happy path scenarios
- Edge cases and boundary values
- Error conditions
- Type variations

## How It Works

### Backend Implementation

#### 1. **LLM Engine Enhancement** (`backend/llm_engine.py`)
- Added `_TEST_GENERATION_SYSTEM_PROMPT`: Specialized prompt template for test generation
- Added `generate_test_cases()` async function: Main entry point for test generation
- Added helper functions:
  - `_build_test_generation_prompt()`: Constructs the user prompt
  - `_parse_test_generation_response()`: Parses LLM output
  - `_test_generation_error()`: Returns error responses

#### 2. **FastAPI Endpoint** (`backend/main.py`)
- **Endpoint**: `POST /generate-tests`
- **Request Model**: `TestGenerationRequest`
  - `code`: String containing Python code
  - `api_key`: Optional Groq API key
- **Response Model**: `TestGenerationResponse`
  - `test_cases`: List of generated test cases
  - `imports`: Required imports for tests
  - `setup_code`: Optional setup/fixture code
  - `success`: Boolean status
  - `error`: Error message if applicable

**Validation Pipeline**:
1. Validates code is not empty
2. Checks syntax via AST parsing
3. Calls LLM for test generation
4. Returns structured response

### Frontend Implementation

#### 1. **API Integration** (`frontend/src/App.jsx`)
- Added `runTestGeneration()` function for API calls
- New state variables:
  - `testResult`: Stores generated test cases
  - `testLoading`: Loading state during generation
  - `testError`: Error message if generation fails

#### 2. **UI Components**
- **TestResults Component**: Displays:
  - Generated test cases with descriptions
  - Required imports
  - Optional setup code
  - Copy buttons for easy code reuse

#### 3. **User Interface**
- Added "✓ Generate Tests" button in toolbar
- Button shows loading state during generation
- Results display in output panel
- Error banner for failed generations
- Integration with existing result display system

#### 4. **Styling** (`frontend/src/index.css`)
- Added `btn-secondary` style (green theme)
- Added styles for test results display:
  - `.tests-list`: Container for test cases
  - `.test-item`: Individual test case styling
  - `.test-header`: Test name and description
  - `.test-code-wrap`: Code block wrapper
  - `.test-code`: Monospace code formatting

## Usage

### Basic Flow
1. **Paste Code**: Enter your Python code in the editor
2. **Add API Key**: (Optional) Supply your Groq API key
3. **Click "Generate Tests"**: The button will show loading state
4. **View Results**: Test cases appear in the output panel
5. **Copy Tests**: Use copy buttons to get imports, setup code, and individual tests

### Example

**Input Code**:
```python
def add(a, b):
    """Add two numbers."""
    return a + b

def divide(x, y):
    """Divide x by y."""
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y
```

**Generated Output Includes**:
- Test for happy path: `test_add_positive_numbers()`
- Test for edge cases: `test_add_with_zero()`, `test_add_negative_numbers()`
- Test for error handling: `test_divide_by_zero()`
- Test for type variations: `test_divide_with_floats()`
- Required imports: `import pytest`
- Sample fixtures if needed

## API Details

### Request
```json
{
  "code": "def hello(name):\n    return f'Hello, {name}!'",
  "api_key": "gsk_..." 
}
```

### Success Response
```json
{
  "success": true,
  "test_cases": [
    {
      "test_name": "test_hello_with_name",
      "test_code": "def test_hello_with_name():\n    assert hello('Alice') == 'Hello, Alice!'",
      "description": "Test greeting with a name"
    }
  ],
  "imports": "import pytest",
  "setup_code": "",
  "error": null
}
```

### Error Response
```json
{
  "success": false,
  "test_cases": [],
  "imports": "",
  "setup_code": "",
  "error": "Syntax error in code: ..."
}
```

## Configuration

### Environment Variables
- `GROQ_API_KEY`: Server-side fallback key (optional)
- `VITE_API_URL`: Frontend API endpoint (defaults to current host)

### LLM Settings
- **Model**: `llama-3.1-8b-instant` (Groq)
- **Temperature**: 0.3 (more deterministic than debug analysis)
- **Max Tokens**: 2048 (allows longer test suites)
- **Timeout**: 30 seconds

## Performance Notes

- **First Request**: ~2-3 seconds (Groq API latency)
- **Subsequent Requests**: Similar latency (no caching)
- **Code Size**: Works with code up to ~2000 tokens
- **Test Count**: Usually generates 5-10 tests per request

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "No API key provided" | Missing Groq key | Set `GROQ_API_KEY` or supply in UI |
| "Invalid Groq key" | Key doesn't start with `gsk_` | Verify key format |
| "Syntax error" | Invalid Python code | Fix syntax errors first |
| "Rate limit exceeded" | Too many requests to Groq | Wait and retry |
| "Connection error" | Cannot reach Groq/Backend | Check network/API availability |

## Testing the Feature

### Manual Test
1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Paste sample code: Use "clean code" sample
4. Set Groq API key
5. Click "Generate Tests"
6. Verify test cases appear with proper formatting

### Sample Code for Testing
```python
def calculate_average(numbers):
    """Calculate average of a list of numbers."""
    if not numbers:
        raise ValueError("List cannot be empty")
    return sum(numbers) / len(numbers)
```

## Files Modified

1. **backend/llm_engine.py** (↑ ~120 lines)
   - Added test generation functions
   - New system prompt for test generation

2. **backend/main.py** (↑ ~60 lines)
   - New endpoint `/generate-tests`
   - New request/response models
   - Import `generate_test_cases`

3. **frontend/src/App.jsx** (↑ ~100 lines)
   - New `runTestGeneration()` function
   - New `TestResults` component
   - New state variables
   - Updated toolbar with test button
   - Updated output display logic

4. **frontend/src/index.css** (↑ ~50 lines)
   - `btn-secondary` style
   - Test results display styles

## Future Enhancements

- [ ] Test framework selection (pytest, unittest, nose)
- [ ] Mock/fixture auto-generation
- [ ] Coverage analysis integration
- [ ] Test execution in browser
- [ ] Parameterized test templates
- [ ] Performance test generation
- [ ] Integration test suggestions

## Notes

- Test generation requires a valid Groq API key
- Generated tests are suggestions and should be reviewed
- Consider the code's actual requirements when refining tests
- Tests follow pytest conventions for easy integration
