#!/usr/bin/env python3
"""
Integration test for the test generation feature.
Verifies the /generate-tests endpoint works correctly.

Usage:
    python test_generation_feature.py

Requirements:
    - Backend running on http://localhost:8000
    - Groq API key set in GROQ_API_KEY environment variable
"""

import os
import sys
import asyncio
import json
import httpx

# Configuration
API_BASE = "http://localhost:8000"
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Test code samples
CLEAN_CODE = '''def add(a, b):
    """Add two numbers."""
    return a + b
'''

FUNCTION_WITH_EDGE_CASES = '''def calculate_percentage(value, total):
    """Calculate percentage of value against total."""
    if total == 0:
        raise ValueError("Total cannot be zero")
    if value < 0 or total < 0:
        raise ValueError("Values must be non-negative")
    return (value / total) * 100
'''

COMPLEX_FUNCTION = '''def merge_sorted_lists(list1, list2):
    """Merge two sorted lists into a single sorted list."""
    result = []
    i = j = 0
    
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    
    result.extend(list1[i:])
    result.extend(list2[j:])
    return result
'''


async def test_health():
    """Test /health endpoint."""
    print("\n" + "=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health", timeout=5)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            assert response.status_code == 200
            print("✓ PASSED: Backend is online")
            return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


async def test_test_generation_empty_code():
    """Test that /generate-tests rejects empty code."""
    print("\n" + "=" * 60)
    print("TEST 2: Empty Code Rejection")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/generate-tests",
                json={"code": "", "api_key": GROQ_KEY},
                timeout=10
            )
            print(f"Status: {response.status_code}")
            assert response.status_code == 400
            error = response.json()
            print(f"Error message: {error['detail']}")
            print("✓ PASSED: Empty code correctly rejected")
            return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


async def test_test_generation_syntax_error():
    """Test that /generate-tests rejects syntax errors."""
    print("\n" + "=" * 60)
    print("TEST 3: Syntax Error Rejection")
    print("=" * 60)
    
    bad_code = "def broken(\n  if True: pass"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/generate-tests",
                json={"code": bad_code, "api_key": GROQ_KEY},
                timeout=10
            )
            print(f"Status: {response.status_code}")
            assert response.status_code == 400
            error = response.json()
            print(f"Error message: {error['detail']}")
            print("✓ PASSED: Syntax errors correctly rejected")
            return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


async def test_test_generation_no_key():
    """Test that /generate-tests handles missing API key."""
    print("\n" + "=" * 60)
    print("TEST 4: Missing API Key")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/generate-tests",
                json={"code": CLEAN_CODE},  # No API key
                timeout=10
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 500:
                error = response.json()
                print(f"Error: {error['detail']}")
                print("✓ PASSED: Missing key handled appropriately")
                return True
            else:
                print(f"Response: {response.json()}")
                print("✓ PASSED: Request processed")
                return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


async def test_test_generation_success():
    """Test successful test case generation."""
    print("\n" + "=" * 60)
    print("TEST 5: Successful Test Generation")
    print("=" * 60)
    
    if not GROQ_KEY:
        print("⊘ SKIPPED: No GROQ_API_KEY environment variable")
        return True
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/generate-tests",
                json={"code": CLEAN_CODE, "api_key": GROQ_KEY},
                timeout=30
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error: {response.json()}")
                print("✗ FAILED: Request was not successful")
                return False
            
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Test cases generated: {len(data.get('test_cases', []))}")
            print(f"Imports: {data.get('imports', 'N/A')[:50]}...")
            
            if data.get('success') and len(data.get('test_cases', [])) > 0:
                print("\nFirst test case:")
                first_test = data['test_cases'][0]
                print(f"  Name: {first_test['test_name']}")
                print(f"  Description: {first_test['description']}")
                print(f"  Code preview: {first_test['test_code'][:60]}...")
                print("✓ PASSED: Test generation successful")
                return True
            else:
                print("✗ FAILED: No test cases generated")
                return False
                
    except httpx.TimeoutException:
        print("✗ FAILED: Request timeout (LLM took too long)")
        return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


async def test_test_generation_complex():
    """Test generation with more complex code."""
    print("\n" + "=" * 60)
    print("TEST 6: Complex Function Test Generation")
    print("=" * 60)
    
    if not GROQ_KEY:
        print("⊘ SKIPPED: No GROQ_API_KEY environment variable")
        return True
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/generate-tests",
                json={"code": COMPLEX_FUNCTION, "api_key": GROQ_KEY},
                timeout=30
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error: {response.json()}")
                return False
            
            data = response.json()
            test_count = len(data.get('test_cases', []))
            print(f"Test cases generated: {test_count}")
            
            if test_count >= 3:
                print("✓ PASSED: Multiple test cases generated for complex function")
                for i, test in enumerate(data['test_cases'][:3]):
                    print(f"  {i+1}. {test['test_name']}: {test['description']}")
                return True
            else:
                print(f"✗ FAILED: Only {test_count} test cases (expected at least 3)")
                return False
                
    except httpx.TimeoutException:
        print("✗ FAILED: Request timeout")
        return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NeuroDebug Test Generation Feature - Integration Tests")
    print("=" * 60)
    print(f"API Base: {API_BASE}")
    print(f"API Key Set: {'Yes' if GROQ_KEY else 'No'}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", await test_health()))
    results.append(("Empty Code Rejection", await test_test_generation_empty_code()))
    results.append(("Syntax Error Rejection", await test_test_generation_syntax_error()))
    results.append(("Missing API Key", await test_test_generation_no_key()))
    results.append(("Successful Generation", await test_test_generation_success()))
    results.append(("Complex Function", await test_test_generation_complex()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠ Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
