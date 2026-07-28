"""Minimal test to isolate the issue"""
import requests
import time

def test_minimal():
    print("Testing minimal endpoints...")
    
    try:
        # Test root endpoint (no database)
        print("1. Testing root endpoint...")
        response = requests.get("http://localhost:8000/", timeout=30)
        print(f"Root endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test health endpoint (no database)
        print("2. Testing health endpoint...")  
        response = requests.get("http://localhost:8000/health", timeout=30)
        print(f"Health endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
        
        print("✅ Basic endpoints working!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_minimal()