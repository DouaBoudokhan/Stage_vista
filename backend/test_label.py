from app.services.ocr_parser_service import ocr_parser_service

label_ocr = """
EPOS
0335
PO:3480
IMPACT 100 MS Stereo USB-C+A
Art.-No. 1001421 QTY: 20
Product Set-serial numbers Data Matrix code
EAN 5 714708 012429
UPC 8 40064 41222 3
HS.FW.64
EPOS AUDIO UK Ltd 3800 Parkside, Birmingham B37 7YG, UK
DSEA A/S, Kongebakken 9, DK-2765 Smørum, Denmark
eposaudio.com
Made in China
"""

parsed = ocr_parser_service.parse_shipping_label(label_ocr)
print("--- PARSED SHIPPING LABEL DATA ---")
print("Brand:", parsed["brand"])
print("Product Name:", parsed["product_name"])
print("Article Number (Ref):", parsed["article_number"])
print("Quantity (QTY):", parsed["quantity"])
print("PO Number:", parsed["po_number"])
print("Matched PO:", parsed["matched_po"])
print("EAN:", parsed["ean"])
print("UPC:", parsed["upc"])
print("Serial Numbers:", parsed["serial_numbers"])
