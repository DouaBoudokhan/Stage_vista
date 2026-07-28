from app.services.ocr_parser_service import ocr_parser_service

sample_ocr = """
Lactech plus
Centre Urbain Nord
B 5-4 Immeuble Nour City
1082 Tunis
Matricule Fiscale :1107543Y/A/M/000

Cimpress Tunisie SARL
Immeuble Lac 8 Les Jardins du Lac

Bon de livraison
N° du BL: BLV26159
Date: 23/06/26

Désignation | Qté | P.U. H.T. | Montant HT
PO: 2000234706
MacBook Pro 16" M5 18 CPU and 20 GPU, 24GB 1TB SSD - Space Black
SN: C7R2RVDQVQ
APPLE USB-C 140 W pour MacBook Pro 16 pouces

PO: 2000237658
MacBook Pro 16" M5 18 CPU and 20 GPU, 24GB 1TB SSD - Space Black
SN: - G2MPX05JWH - CTQJW36WQW - GVP2D00TCP

PO: 2000243378
MacBook Pro 16" M5 18 CPU and 20 GPU, 24GB 1TB SSD - Space Black
SN: FLWWQ45LWG

Total Bon de livraison N° BLV26159
"""

parsed = ocr_parser_service.parse_invoice(sample_ocr)
print(f"Supplier: '{parsed.supplier}'")
print(f"Invoice/BL Number: '{parsed.invoice_number}'")
print(f"Total POs found: {len(parsed.purchase_orders)}")

for po in parsed.purchase_orders:
    print(f"  PO Number: {po.po_number}")
    print(f"  Serial Numbers: {po.serial_numbers}")
    print(f"  Section Text: {po.text[:100]}...\n")
