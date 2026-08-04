#!/usr/bin/env python3
"""
Test the /tickets endpoint directly
"""

import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_endpoint():
    base_url = "http://172.18.221.31:8000"
    
    print("\n" + "="*80)
    print("Testing /tickets Endpoint")
    print("="*80 + "\n")
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")
    except Exception as e:
        print(f"   ERROR: {e}\n")
        return
    
    # Test 2: List all routes
    print("2. Testing OpenAPI docs...")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})
            print(f"   Available endpoints:")
            for path in sorted(paths.keys()):
                methods = list(paths[path].keys())
                print(f"     {path:40} {', '.join(methods)}")
            print()
    except Exception as e:
        print(f"   ERROR: {e}\n")
    
    # Test 3: Test /tickets
    print("3. Testing /tickets endpoint...")
    try:
        print(f"   GET {base_url}/tickets")
        response = requests.get(f"{base_url}/tickets", timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response type: {type(data)}")
            print(f"   Response length: {len(data) if isinstance(data, list) else 'N/A'}")
            if isinstance(data, list) and len(data) > 0:
                print(f"   First ticket: {data[0]}")
            else:
                print(f"   Response: {data}")
        else:
            print(f"   Error response: {response.text}")
        
        print()
        
    except requests.exceptions.Timeout:
        print("   ERROR: Request timed out after 30 seconds")
        print("   This suggests the endpoint is hanging or very slow\n")
    except Exception as e:
        print(f"   ERROR: {e}\n")
    
    # Test 4: Test with explicit base path
    print("4. Testing /api/v1/tickets (with prefix)...")
    try:
        response = requests.get(f"{base_url}/api/v1/tickets", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Tickets: {len(data) if isinstance(data, list) else data}")
        else:
            print(f"   Response: {response.text[:200]}")
        print()
    except Exception as e:
        print(f"   ERROR: {e}\n")
    
    print("="*80)
    print("Test Complete")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        test_endpoint()
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
