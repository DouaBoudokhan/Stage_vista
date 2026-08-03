"""Test dynamic delivery note & package label OCR parsing"""
import unittest
from app.services.ocr_parser_service import ocr_parser_service

class TestDeliveryNoteParsing(unittest.TestCase):
    def test_delivery_note_1_tech_plus(self):
        sample_text = """Tech plus
Bon de livraison N° : BLV26159
Date : 23/06/26
Fournisseur : TechDistributor Ltd
Lieu de livraison : Vista Print Immeuble Lac 8 Les Jardins du Lac

PO: 2000234706
MacBook Pro 16" M5 18 CPU and 20 GPU, 24GB 1TB SSD - Space Black
SN: C7R2RVDQVQ
APPLE USB-C 140 W pour MacBook Pro 16 pouces

PO: 2000237658
MacBook Pro 16" M5 18 CPU and 20 GPU, 24GB 1TB SSD - Space Black
SN: G2MPX05JWH - CTQJW36WOW - GVP2000TCP
APPLE USB-C 140 W pour MacBook Pro 16 pouces

PO: 2000243378
MacBook Pro 16" M5 18 CPU and 20 GPU, 24GB 1TB SSD - Space Black
SN: FLWWQ45LWG
APPLE USB-C 140 W pour MacBook Pro 16 pouces"""

        res = ocr_parser_service.parse_invoice(sample_text)
        self.assertIn(res.supplier, ["TechDistributor Ltd", "Tech plus"])
        self.assertEqual(res.invoice_number, "BLV26159")
        self.assertEqual(len(res.purchase_orders), 3)

        po1 = res.purchase_orders[0]
        self.assertEqual(po1.po_number, "2000234706")
        self.assertIn("C7R2RVDQVQ", po1.serial_numbers)

    def test_delivery_note_2_lactech_plus(self):
        sample_text = """Lactech plus
Centre Urbain Nord B 5-4 Immeuble Nour City 1082 Tunis
Matricule Fiscale : 1107543Y/A/M/000
Téléphone : 36 740 713

Bon de livraison
N° du BL : BLV26143
Date : 11/06/26

Lieu de livraison : Vista Print Immeuble Lac 8 Les Jardins du Lac

PO: 2000246645 Med Kountini
Dell Pro 14-16 Plus EcoLoop Slim - CP5724S

PO: 2000246286 Nizar Khemilek
DELL SOURIS OPTIQUE MS116 NOIR

PO: 2000246074 ghada soudani
EPOS IMPACT 460T USB-C AND USB-A UC

PO: 2000246070 Mootaz Salthi
EPOS IMPACT 100 MS stéréo USB-C+A

PO: 2000245842 Haifa EPJ
DELL SOURIS OPTIQUE MS116 NOIR

PO: 2000244012 imen Bouchaala
EPOS IMPACT 460T USB-C AND USB-A UC

PO: 2000246410 idriss jday
SERVICE FOURNISSEUR for laptop repair (idris jday) SN: DRDXJKVHK7

PO: 2000241920 Dhouha Hwiss
Dell Multimedia Keyboard-KB216 - French (AZERTY)"""

        res = ocr_parser_service.parse_invoice(sample_text)
        self.assertEqual(res.supplier, "Lactech plus")
        self.assertEqual(res.invoice_number, "BLV26143")
        self.assertEqual(len(res.purchase_orders), 8)

        po_numbers = [po.po_number for po in res.purchase_orders]
        self.assertIn("2000246645", po_numbers)
        self.assertIn("2000246286", po_numbers)
        self.assertIn("2000246074", po_numbers)
        self.assertIn("2000246070", po_numbers)
        self.assertIn("2000245842", po_numbers)
        self.assertIn("2000244012", po_numbers)
        self.assertIn("2000246410", po_numbers)
        self.assertIn("2000241920", po_numbers)

        po_service = [po for po in res.purchase_orders if po.po_number == "2000246410"][0]
        self.assertIn("DRDXJKVHK7", po_service.serial_numbers)

    def test_package_label_parsing_epos(self):
        """Test package label OCR parsing for EPOS headset real sample"""
        sample_label = """EPOS
0335
PO:3480
IMPACT 100 MS Stereo USB-C+A
Art .- No. 1001421
QTY: 20
EAN
5 716708 012429
UPC
8 40064 41222-"""

        parsed = ocr_parser_service.parse_shipping_label(sample_label)

        # 1. PO number
        self.assertEqual(parsed["po_number"], "3480")
        # 2. Article number
        self.assertEqual(parsed["article_number"], "1001421")
        # 3. UPC normalized
        self.assertEqual(parsed["upc"], "84006441222")
        # 4. EAN normalized
        self.assertEqual(parsed["ean"], "5716708012429")
        # 5. Quantity
        self.assertEqual(parsed["quantity"], 20)
        # 6. Full product description preserved
        self.assertEqual(parsed["product_name"], "IMPACT 100 MS Stereo USB-C+A")
        # Brand
        self.assertEqual(parsed["brand"], "EPOS")


if __name__ == "__main__":
    unittest.main()
