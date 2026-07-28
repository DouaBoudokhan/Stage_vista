"""Simple direct test"""
import requests
import time

def simple_test():
    try:
        print("Testing direct connection...")
        response = requests.get("http://localhost:8000/docs", timeout=15)
        print(f"Docs endpoint status: {response.status_code}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/documents/parse-ocr",
            data={"ocr_text": "INVOICE INV-123 PO 2000234706 MacBook Pro"},
            timeout=10
        )
        print(f"OCR endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simple_test()