"""Test Script for Invoice Analysis Workflow"""
import requests
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def create_test_invoice_image():
    """Create a test invoice image for testing"""
    # Create invoice image
    img = Image.new('RGB', (800, 1000), color='white')
    draw = ImageDraw.Draw(img)
    
    # Invoice content
    lines = [
        "TECH SOLUTIONS LTD",
        "",
        "INVOICE: INV-2026-00012",
        "",
        "Bill To:",
        "StockIT Company",
        "123 Business Ave",
        "",
        "--------------------------------",
        "",
        "PO 2000234706",
        "",
        "MacBook Pro 16",
        "M5 Processor",
        "24GB RAM",
        "1TB SSD",
        "Space Gray",
        "",
        "Serial Number: C02ABC123456",
        "",
        "Qty: 1",
        "Price: $3,299.00",
        "",
        "--------------------------------",
        "",
        "PO 2000235001", 
        "",
        "Magic Keyboard",
        "USB-C Connection",
        "White Color",
        "Backlit Keys",
        "",
        "Serial Number: AAB123XYZ789",
        "",
        "Qty: 1", 
        "Price: $199.00",
        "",
        "--------------------------------",
        "",
        "Total: $3,498.00",
        "",
        "Thank you for your business!"
    ]
    
    y = 50
    for line in lines:
        draw.text((50, y), line, fill='black')
        y += 25
    
    # Save to bytes
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer


def get_test_ocr_text():
    """Get test OCR text that matches the invoice image"""
    return """TECH SOLUTIONS LTD

INVOICE: INV-2026-00012

Bill To:
StockIT Company
123 Business Ave

--------------------------------

PO 2000234706

MacBook Pro 16
M5 Processor
24GB RAM
1TB SSD
Space Gray

Serial Number: C02ABC123456

Qty: 1
Price: $3,299.00

--------------------------------

PO 2000235001

Magic Keyboard
USB-C Connection
White Color
Backlit Keys

Serial Number: AAB123XYZ789

Qty: 1
Price: $199.00

--------------------------------

Total: $3,498.00

Thank you for your business!"""


def test_ocr_parsing():
    """Test deterministic OCR parsing (Step 1)"""
    print("🔍 Testing OCR Parsing (Deterministic)")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1/documents"
    ocr_text = get_test_ocr_text()
    
    # Test OCR parsing endpoint
    response = requests.post(
        f"{base_url}/parse-ocr",
        data={"ocr_text": ocr_text}
    )
    
    if response.status_code != 200:
        print(f"❌ OCR parsing failed: {response.text}")
        return False
    
    result = response.json()
    
    print(f"✅ Supplier: {result['supplier']}")
    print(f"✅ Invoice Number: {result['invoice_number']}")
    print(f"✅ Purchase Orders Found: {len(result['purchase_orders'])}")
    
    for i, po in enumerate(result['purchase_orders'], 1):
        print(f"   {i}. PO {po['po_number']}")
        print(f"      Text: {po['text'][:50]}...")
        print(f"      Serial Numbers: {po['serial_numbers']}")
    
    print(f"✅ Validation: {'PASSED' if result['validation']['valid'] else 'FAILED'}")
    if result['validation']['warnings']:
        print(f"⚠️  Warnings: {result['validation']['warnings']}")
    
    return True


def test_llm_generation():
    """Test LLM description generation (Step 2)"""
    print("\n🤖 Testing LLM Description Generation")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1/documents"
    
    # Test LLM generation for MacBook
    test_data = {
        "po_number": "2000234706",
        "po_text": "MacBook Pro 16 M5 Processor 24GB RAM 1TB SSD Space Gray"
    }
    
    response = requests.post(
        f"{base_url}/generate-description",
        json=test_data
    )
    
    if response.status_code != 200:
        print(f"❌ LLM generation failed: {response.text}")
        return False
    
    result = response.json()
    
    if result['success']:
        print(f"✅ Generated Description: {result['description']}")
        print(f"✅ Word Count: {result.get('word_count', 'N/A')}")
        print(f"✅ Model Used: {result.get('model_used', 'N/A')}")
    else:
        print(f"❌ LLM Error: {result['error']}")
        return False
    
    return True


def test_complete_workflow():
    """Test complete invoice analysis workflow"""
    print("\n🚀 Testing Complete Invoice Analysis Workflow")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1/documents"
    
    # Create test data
    invoice_image = create_test_invoice_image()
    ocr_text = get_test_ocr_text()
    
    # Prepare multipart data
    files = {
        'image': ('test_invoice.png', invoice_image, 'image/png')
    }
    data = {
        'ocr_text': ocr_text,
        'document_type': 'invoice'
    }
    
    # Call complete analysis endpoint
    response = requests.post(
        f"{base_url}/analyze",
        files=files,
        data=data
    )
    
    if response.status_code != 200:
        print(f"❌ Complete analysis failed: {response.text}")
        return False
    
    result = response.json()
    
    print(f"✅ Analysis Success: {result['success']}")
    
    # Document info
    doc = result['document']
    print(f"✅ Document ID: {doc['id']}")
    print(f"✅ Supplier: {doc['supplier']}")
    print(f"✅ Invoice Number: {doc['invoice_number']}")
    print(f"✅ Image Saved: {doc['image_path']}")
    
    # Purchase Orders
    print(f"\n📋 Purchase Orders ({len(result['purchase_orders'])} found):")
    for po in result['purchase_orders']:
        print(f"   • PO {po['po_number']}")
        print(f"     Description: {po['description']}")
        print(f"     Serial Numbers: {po['serial_numbers']}")
        print(f"     Cached: {'YES' if po['cached'] else 'NO'}")
        print(f"     LLM Used: {'YES' if po['llm_used'] else 'NO'}")
        print()
    
    # Statistics
    stats = result['statistics']
    print(f"📊 Statistics:")
    print(f"   Total POs: {stats['total_pos']}")
    print(f"   Cached Descriptions: {stats['cached_descriptions']}")
    print(f"   New Descriptions: {stats['new_descriptions']}")
    print(f"   Serial Numbers: {stats['total_serial_numbers']}")
    
    return True


def test_cache_functionality():
    """Test LLM cache functionality by running analysis twice"""
    print("\n💾 Testing LLM Cache Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1/documents"
    
    # Run analysis twice with same data
    invoice_image1 = create_test_invoice_image()
    invoice_image2 = create_test_invoice_image()
    ocr_text = get_test_ocr_text()
    
    print("🔄 First Analysis (should generate descriptions)...")
    
    # First analysis
    files1 = {'image': ('test_invoice1.png', invoice_image1, 'image/png')}
    data1 = {'ocr_text': ocr_text, 'document_type': 'invoice'}
    
    response1 = requests.post(f"{base_url}/analyze", files=files1, data=data1)
    
    if response1.status_code != 200:
        print(f"❌ First analysis failed: {response1.text}")
        return False
    
    result1 = response1.json()
    cached_count1 = result1['statistics']['cached_descriptions']
    new_count1 = result1['statistics']['new_descriptions']
    
    print(f"✅ First run - Cached: {cached_count1}, New: {new_count1}")
    
    print("\n🔄 Second Analysis (should use cache)...")
    
    # Second analysis (should use cache)
    files2 = {'image': ('test_invoice2.png', invoice_image2, 'image/png')}
    data2 = {'ocr_text': ocr_text, 'document_type': 'invoice'}
    
    response2 = requests.post(f"{base_url}/analyze", files=files2, data=data2)
    
    if response2.status_code != 200:
        print(f"❌ Second analysis failed: {response2.text}")
        return False
    
    result2 = response2.json()
    cached_count2 = result2['statistics']['cached_descriptions']
    new_count2 = result2['statistics']['new_descriptions']
    
    print(f"✅ Second run - Cached: {cached_count2}, New: {new_count2}")
    
    # Verify cache was used
    if cached_count2 > cached_count1:
        print("✅ Cache functionality working - descriptions reused!")
        return True
    else:
        print("⚠️  Cache might not be working as expected")
        return False


def test_api_endpoints():
    """Test additional API endpoints"""
    print("\n🌐 Testing Additional API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1/documents"
    
    # Test document listing
    print("📋 Testing document listing...")
    response = requests.get(f"{base_url}/list")
    if response.status_code == 200:
        docs = response.json()
        print(f"✅ Found {len(docs)} documents")
    else:
        print(f"❌ Document listing failed: {response.text}")
    
    # Test PO listing
    print("📋 Testing Purchase Order listing...")
    response = requests.get(f"{base_url}/purchase-orders")
    if response.status_code == 200:
        pos = response.json()
        print(f"✅ Found {len(pos)} Purchase Orders")
        
        # Show cache status
        cached = sum(1 for po in pos if po['has_description'])
        print(f"✅ Cached descriptions: {cached}/{len(pos)}")
    else:
        print(f"❌ PO listing failed: {response.text}")
    
    # Test cache statistics
    print("📊 Testing cache statistics...")
    response = requests.get(f"{base_url}/cache-stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Cache Statistics:")
        print(f"   Total POs: {stats['total_purchase_orders']}")
        print(f"   Cached: {stats['cached_descriptions']}")
        print(f"   Hit Rate: {stats['cache_hit_rate']:.2%}")
    else:
        print(f"❌ Cache stats failed: {response.text}")


def main():
    """Run all tests"""
    print("🧪 StockIT Invoice Analysis Workflow Tests")
    print("=" * 60)
    
    try:
        # Test individual components
        if not test_ocr_parsing():
            return
        
        if not test_llm_generation():
            print("⚠️  LLM test failed - check Azure AI configuration")
        
        # Test complete workflow
        if not test_complete_workflow():
            return
        
        # Test caching
        test_cache_functionality()
        
        # Test API endpoints
        test_api_endpoints()
        
        print("\n🎉 All tests completed!")
        print("\n📋 Next Steps:")
        print("1. Configure Azure AI Foundry credentials in .env")
        print("2. Test with real invoice images")
        print("3. Monitor LLM cache performance")
        print("4. Integrate with mobile app")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the backend server is running")
        print("Start server with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()