"""Quick test of Invoice Analysis endpoints"""
import requests
import json

def test_basic_endpoints():
    """Test basic endpoints to verify API is working"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Invoice Analysis API")
    print("=" * 40)
    
    try:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test cache stats
        print("2. Testing cache stats...")
        response = requests.get(f"{base_url}/api/v1/documents/cache-stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Cache stats: {stats}")
        else:
            print(f"❌ Cache stats failed: {response.status_code}")
            print(f"Error: {response.text}")
        
        # Test OCR parsing
        print("3. Testing OCR parsing...")
        test_ocr_text = """TECH SOLUTIONS LTD

INVOICE: INV-2026-00012

PO 2000234706
MacBook Pro 16
M5 Processor  
24GB RAM
1TB SSD

Serial Number: C02ABC123456"""
        
        response = requests.post(
            f"{base_url}/api/v1/documents/parse-ocr",
            data={"ocr_text": test_ocr_text},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ OCR parsing successful")
            print(f"   Supplier: {result['supplier']}")
            print(f"   Invoice: {result['invoice_number']}")
            print(f"   POs found: {len(result['purchase_orders'])}")
            
            for po in result['purchase_orders']:
                print(f"   - PO {po['po_number']}: {po['text']}")
        else:
            print(f"❌ OCR parsing failed: {response.status_code}")
            print(f"Error: {response.text}")
        
        # Test document listing
        print("4. Testing document listing...")
        response = requests.get(f"{base_url}/api/v1/documents/list", timeout=10)
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Document listing: {len(docs)} documents found")
        else:
            print(f"❌ Document listing failed: {response.status_code}")
        
        print("\n🎉 Basic API tests completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - server not running?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server may be overloaded")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_basic_endpoints()