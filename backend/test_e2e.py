import requests

url = "http://127.0.0.1:8000/api/v1/documents/analyze"
ocr_sample = """INVOICE
Supplier: Lactech plus
Centre Urbain Nord B 5-4 Immeuble Nour City 1082 Tunis
Facture N°: INV-2026-8942

Purchase Orders & Delivery Items:
PO: 2000234706
Item: MacBook Pro 16" M5 18 CPU and 20 GPU, Quantity: 1

PO: 2000237658
Item: Dell Latitude 5440 Core i7 16GB RAM 512GB SSD, Quantity: 10

PO: 2000243378
Item: EPOS Impact 100 MS Stereo USB-C Headset, Quantity: 15
"""

# Create a small dummy image file
dummy_img = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xFF\xC0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xFF\xDA\x00\x08\x01\x01\x00\x00?\x00\x7F\x00\xFF\xD9'

print("--- SCAN 1 (FIRST SCAN: GENERATING & CACHING WITH LLAMA 3.3) ---")
files = {'file': ('invoice.jpg', dummy_img, 'image/jpeg')}
data = {'ocr_text': ocr_sample, 'document_type': 'invoice'}

res1 = requests.post(url, files=files, data=data)
print("Status:", res1.status_code)
res1_json = res1.json()
print("Response statistics:", res1_json.get("statistics"))
for po in res1_json.get("purchase_orders", []):
    print(f"  PO {po['po_number']}: '{po['description']}' | Cached: {po['cached']} | LLM Used: {po['llm_used']}")

print("\n--- SCAN 2 (SECOND SCAN: READING CACHED DESCRIPTIONS FROM DB) ---")
files2 = {'file': ('invoice.jpg', dummy_img, 'image/jpeg')}
res2 = requests.post(url, files=files2, data=data)
print("Status:", res2.status_code)
res2_json = res2.json()
print("Response statistics:", res2_json.get("statistics"))
for po in res2_json.get("purchase_orders", []):
    print(f"  PO {po['po_number']}: '{po['description']}' | Cached: {po['cached']} | LLM Used: {po['llm_used']}")
