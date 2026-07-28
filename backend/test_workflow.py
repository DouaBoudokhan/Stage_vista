"""Test Script for Stock Entry Workflow"""
import requests
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def create_test_images():
    """Create test images for demonstration"""
    
    # Create product image (simulated laptop)
    product_img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(product_img)
    
    # Draw a simple laptop shape
    draw.rectangle([50, 80, 350, 220], fill='gray', outline='black', width=3)
    draw.rectangle([60, 90, 340, 180], fill='black')
    draw.text((160, 240), "LAPTOP", fill='black')
    
    # Save as base64
    buffer = BytesIO()
    product_img.save(buffer, format='PNG')
    product_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Create document image (simulated invoice)
    doc_img = Image.new('RGB', (600, 800), color='white')
    draw = ImageDraw.Draw(doc_img)
    
    # Document content
    lines = [
        "DELIVERY NOTE",
        "",
        "Supplier: TECH SOLUTIONS LTD",
        "Document: INV-2024-001234",
        "",
        "PO 2000234706",
        "MacBook Pro 16 M5 24GB 1TB SSD",
        "SN: C7R2RVDQVQ",
        "",
        "PO 2000237658", 
        "MacBook Pro 16 M5 32GB 2TB SSD",
        "SN: G2MPX05JVHV",
        "",
        "Total: 2 items"
    ]
    
    y = 50
    for line in lines:
        draw.text((50, y), line, fill='black')
        y += 40
    
    # Save as base64
    buffer = BytesIO()
    doc_img.save(buffer, format='PNG')
    document_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Create package label image
    package_img = Image.new('RGB', (500, 400), color='white')
    draw = ImageDraw.Draw(package_img)
    
    # Package label content
    package_lines = [
        "APPLE",
        "",
        "MacBook Pro 16 M5 24GB 1TB SSD",
        "",
        "Article: MBP16-001421",
        "",
        "Qty: 1",
        "",
        "PO: 2000234706"
    ]
    
    y = 50
    for line in package_lines:
        draw.text((50, y), line, fill='black')
        y += 35
    
    # Save as base64
    buffer = BytesIO()
    package_img.save(buffer, format='PNG')
    package_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return product_base64, document_base64, package_base64


def test_stock_entry_workflow():
    """Test the complete 5-step workflow"""
    base_url = "http://localhost:8000/api/v1/stock-entry"
    
    print("🚀 Testing Stock Entry Workflow")
    print("=" * 50)
    
    # Create test images
    product_img, document_img, package_img = create_test_images()
    
    # Step 0: Start workflow
    print("\n📋 Starting Workflow...")
    response = requests.post(f"{base_url}/start")
    if response.status_code != 200:
        print(f"❌ Failed to start workflow: {response.text}")
        return
    
    workflow_data = response.json()
    workflow_id = workflow_data["workflow_id"]
    print(f"✅ Workflow started: {workflow_id}")
    
    # Step 1: Product Detection
    print("\n🔍 Step 1: Product Detection...")
    detection_response = requests.post(
        f"{base_url}/step1/detect-product",
        json={"image_data": product_img}
    )
    
    if detection_response.status_code != 200:
        print(f"❌ Product detection failed: {detection_response.text}")
        return
    
    detection_data = detection_response.json()
    print(f"✅ Product detected: {detection_data['category']} (confidence: {detection_data['confidence']:.2f})")
    
    # Confirm Step 1
    confirm_response = requests.post(
        f"{base_url}/step1/confirm/{workflow_id}",
        json=detection_data
    )
    
    if confirm_response.status_code != 200:
        print(f"❌ Step 1 confirmation failed: {confirm_response.text}")
        return
    
    print("✅ Step 1 confirmed")
    
    # Step 2: Document OCR
    print("\n📄 Step 2: Document Scanning...")
    doc_response = requests.post(
        f"{base_url}/step2/scan-document",
        json={"image_data": document_img}
    )
    
    if doc_response.status_code != 200:
        print(f"❌ Document scanning failed: {doc_response.text}")
        return
    
    doc_data = doc_response.json()
    print(f"✅ Document scanned: {doc_data['supplier']}")
    print(f"📋 Found {len(doc_data['purchase_orders'])} Purchase Orders:")
    for po in doc_data['purchase_orders']:
        print(f"   • PO {po['po_number']}: {po['description']}")
    
    # Confirm Step 2
    confirm_response = requests.post(
        f"{base_url}/step2/confirm/{workflow_id}",
        json=doc_data
    )
    
    if confirm_response.status_code != 200:
        print(f"❌ Step 2 confirmation failed: {confirm_response.text}")
        return
    
    print("✅ Step 2 confirmed")
    
    # Step 3: PO Selection
    print("\n✅ Step 3: Purchase Order Selection...")
    selected_po = doc_data['purchase_orders'][0]['po_number']  # Select first PO
    
    selection_response = requests.post(
        f"{base_url}/step3/select-po",
        json={
            "selected_po_number": selected_po,
            "workflow_id": workflow_id
        }
    )
    
    if selection_response.status_code != 200:
        print(f"❌ PO selection failed: {selection_response.text}")
        return
    
    print(f"✅ Selected PO: {selected_po}")
    
    # Step 4: Package Label
    print("\n📦 Step 4: Package Label Scanning...")
    package_response = requests.post(
        f"{base_url}/step4/scan-package",
        json={
            "image_data": package_img,
            "workflow_id": workflow_id
        }
    )
    
    if package_response.status_code != 200:
        print(f"❌ Package scanning failed: {package_response.text}")
        return
    
    package_data = package_response.json()
    print(f"✅ Package scanned: {package_data['brand']} {package_data['product_name']}")
    print(f"📊 Quantity: {package_data['quantity']}")
    if package_data.get('warning'):
        print(f"⚠️  Warning: {package_data['warning']}")
    
    # Confirm Step 4
    confirm_response = requests.post(
        f"{base_url}/step4/confirm/{workflow_id}",
        json=package_data
    )
    
    if confirm_response.status_code != 200:
        print(f"❌ Step 4 confirmation failed: {confirm_response.text}")
        return
    
    print("✅ Step 4 confirmed")
    
    # Step 5: Save Stock Entry
    print("\n💾 Step 5: Saving Stock Entry...")
    save_response = requests.post(
        f"{base_url}/step5/save",
        json={
            "workflow_id": workflow_id,
            "received_by": "test_technician",
            "confirm_warnings": True
        }
    )
    
    if save_response.status_code != 200:
        print(f"❌ Save failed: {save_response.text}")
        return
    
    save_data = save_response.json()
    print(f"✅ Stock entry saved successfully!")
    print(f"🆔 Inventory ID: {save_data['inventory_id']}")
    print(f"🆔 Stock Entry ID: {save_data['stock_entry_id']}")
    
    # Final status
    print("\n📊 Final Summary:")
    print(f"   • Category: {save_data['category']}")
    print(f"   • Brand: {save_data['brand']}")
    print(f"   • Product: {save_data['product_name']}")
    print(f"   • Article #: {save_data['article_number']}")
    print(f"   • Quantity: {save_data['quantity']}")
    print(f"   • Supplier: {save_data['supplier']}")
    print(f"   • PO: {save_data['selected_po']}")
    
    print("\n🎉 Workflow completed successfully!")


if __name__ == "__main__":
    try:
        test_stock_entry_workflow()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()