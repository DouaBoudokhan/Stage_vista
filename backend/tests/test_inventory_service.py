"""
Automated unit test suite for StockIT InventoryService (unittest based)
Covers all 7 required test scenarios + history without inventory_movements + product.tracking_type + status transitions.
"""
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Product, Inventory, StockEntry, StockExit, PurchaseOrder, Document, Ticket, get_tracking_type
from app.services.inventory_service import InventoryService


class TestInventoryServiceScenarios(unittest.TestCase):

    def setUp(self):
        """In-memory SQLite database session for unit tests."""
        self.engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        
        self.db = TestingSessionLocal()
        self.service = InventoryService()

        # Seed 5 core product categories with tracking_type on products table
        categories = ["Laptop", "Mouse", "Keyboard", "Monitor", "Headset"]
        for cat in categories:
            track_type = get_tracking_type(cat)
            self.db.add(Product(product_name=cat, tracking_type=track_type, stock_on_hand=0))
        self.db.commit()

        # Seed dummy document & POs
        doc = Document(document_type="invoice", document_number="INV-2000234706", supplier="Tech Supplier", image_path="")
        self.db.add(doc)
        self.db.flush()
        po = PurchaseOrder(id=42, document_id=doc.id, po_number="2000234706", description="PO 2000234706")
        po_bulk = PurchaseOrder(id=51, document_id=doc.id, po_number="51", description="PO 51")
        self.db.add(po)
        self.db.add(po_bulk)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_scenario_1_serialized_laptop_receive(self):
        """TEST 1 — Serialized Laptop Receive"""
        result = self.service.receive_stock(
            db=self.db,
            product_ref="Laptop",
            quantity=1,
            technician="Tech1",
            po_id="42",
            category="Laptop",
            brand="Apple",
            product_name="MacBook Pro",
            article_number="MGEA4FN/A",
            serial_numbers=["C7R2RVDQVQ"]
        )

        self.assertEqual(result["tracking_type"], "SERIALIZED")
        self.assertEqual(result["quantity"], 1)

        # Verify inventory row
        inv = self.db.query(Inventory).filter(Inventory.serial_number == "C7R2RVDQVQ").first()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.product.product_name, "Laptop")
        self.assertEqual(inv.product.tracking_type, "SERIALIZED")
        self.assertEqual(inv.tracking_type, "SERIALIZED")
        self.assertEqual(inv.article_number, "MGEA4FN/A")
        self.assertEqual(inv.quantity_available, 1)
        self.assertEqual(inv.status, "AVAILABLE")

        # Verify stock_entries row
        se = self.db.query(StockEntry).filter(StockEntry.inventory_id == inv.id).first()
        self.assertIsNotNone(se)
        self.assertEqual(se.quantity_received, 1)
        self.assertEqual(se.purchase_order_id, 42)

        # Verify product stock_on_hand
        product = self.db.query(Product).filter(Product.product_name == "Laptop").first()
        self.assertEqual(product.stock_on_hand, 1)

    def test_scenario_2_multiple_serialized_laptops(self):
        """TEST 2 — Multiple Serialized Laptops"""
        serials = ["S1", "S2", "S3"]
        result = self.service.receive_stock(
            db=self.db,
            product_ref="Laptop",
            quantity=3,
            technician="Tech1",
            po_id="42",
            category="Laptop",
            brand="Dell",
            product_name="Latitude 5440",
            article_number="DELL-5440",
            serial_numbers=serials
        )

        self.assertEqual(len(result["inventory_ids"]), 3)

        inv_rows = self.db.query(Inventory).filter(Inventory.serial_number.in_(serials)).all()
        self.assertEqual(len(inv_rows), 3)
        for inv in inv_rows:
            self.assertEqual(inv.quantity_available, 1)
            self.assertEqual(inv.tracking_type, "SERIALIZED")
            self.assertEqual(inv.status, "AVAILABLE")

        entries = self.db.query(StockEntry).filter(StockEntry.inventory_id.in_([i.id for i in inv_rows])).all()
        self.assertEqual(len(entries), 3)

        product = self.db.query(Product).filter(Product.product_name == "Laptop").first()
        self.assertEqual(product.stock_on_hand, 3)

    def test_scenario_3_bulk_headset_receive(self):
        """TEST 3 — Bulk Headset Receive"""
        result = self.service.receive_stock(
            db=self.db,
            product_ref="Headset",
            quantity=20,
            technician="Tech1",
            po_id="51",
            category="Headset",
            brand="EPOS",
            product_name="IMPACT 100",
            article_number="1001421",
            serial_numbers=None
        )

        self.assertEqual(result["tracking_type"], "BULK")

        inv = self.db.query(Inventory).filter(Inventory.article_number == "1001421").first()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.tracking_type, "BULK")
        self.assertEqual(inv.quantity_available, 20)
        self.assertIsNone(inv.serial_number)
        self.assertEqual(inv.status, "AVAILABLE")

        se = self.db.query(StockEntry).filter(StockEntry.inventory_id == inv.id).first()
        self.assertIsNotNone(se)
        self.assertEqual(se.quantity_received, 20)

        product = self.db.query(Product).filter(Product.product_name == "Headset").first()
        self.assertEqual(product.stock_on_hand, 20)

    def test_scenario_4_serialized_laptop_assignment(self):
        """TEST 4 — Serialized Laptop Assignment"""
        self.service.receive_stock(
            db=self.db,
            product_ref="Laptop",
            quantity=1,
            technician="Tech1",
            po_id="42",
            category="Laptop",
            brand="Dell",
            product_name="Latitude 5440",
            article_number="DELL-5440",
            serial_numbers=["LAP-ASSIGN-1"]
        )

        inv = self.db.query(Inventory).filter(Inventory.serial_number == "LAP-ASSIGN-1").first()
        
        out_res = self.service.assign_stock(
            db=self.db,
            product_id=str(inv.id),
            quantity=1,
            ticket_id="T-123",
            technician="Tech1"
        )

        self.assertEqual(out_res["quantity"], 1)
        self.assertEqual(out_res["ticket_id"], "T-123")

        self.db.refresh(inv)
        self.assertEqual(inv.status, "ASSIGNED")
        self.assertEqual(inv.quantity_available, 0)

        sx = self.db.query(StockExit).filter(StockExit.inventory_id == inv.id).first()
        self.assertIsNotNone(sx)
        self.assertEqual(sx.quantity, 1)
        self.assertEqual(sx.ticket_id, "T-123")

        product = self.db.query(Product).filter(Product.product_name == "Laptop").first()
        self.assertEqual(product.stock_on_hand, 0)

    def test_scenario_5_bulk_headset_assignment(self):
        """TEST 5 — Bulk Headset Assignment"""
        self.service.receive_stock(
            db=self.db,
            product_ref="Headset",
            quantity=20,
            technician="Tech1",
            po_id="51",
            category="Headset",
            brand="EPOS",
            product_name="IMPACT 100",
            article_number="1001421"
        )

        inv = self.db.query(Inventory).filter(Inventory.article_number == "1001421").first()
        self.assertEqual(inv.quantity_available, 20)

        out_res = self.service.assign_stock(
            db=self.db,
            product_id=str(inv.id),
            quantity=1,
            ticket_id="T-456",
            technician="Tech1"
        )

        self.db.refresh(inv)
        self.assertEqual(inv.quantity_available, 19)
        self.assertEqual(inv.status, "AVAILABLE")

        product = self.db.query(Product).filter(Product.product_name == "Headset").first()
        self.assertEqual(product.stock_on_hand, 19)

    def test_scenario_6_invalid_serialized_receive(self):
        """TEST 6 — Invalid Serialized Receive (missing serial number)"""
        with self.assertRaises(ValueError):
            self.service.receive_stock(
                db=self.db,
                product_ref="Laptop",
                quantity=1,
                technician="Tech1",
                po_id="42",
                category="Laptop",
                serial_numbers=None
            )

        self.assertEqual(self.db.query(Inventory).count(), 0)
        product = self.db.query(Product).filter(Product.product_name == "Laptop").first()
        self.assertEqual(product.stock_on_hand, 0)

    def test_scenario_7_invalid_bulk_exit(self):
        """TEST 7 — Invalid Bulk Exit (assigning more bulk units than available)"""
        self.service.receive_stock(
            db=self.db,
            product_ref="Headset",
            quantity=2,
            technician="Tech1",
            po_id="51",
            category="Headset",
            article_number="1001421"
        )

        inv = self.db.query(Inventory).filter(Inventory.article_number == "1001421").first()

        with self.assertRaises(ValueError):
            self.service.assign_stock(
                db=self.db,
                product_id=str(inv.id),
                quantity=3,
                ticket_id="T-789",
                technician="Tech1"
            )

        self.db.refresh(inv)
        self.assertEqual(inv.quantity_available, 2)
        product = self.db.query(Product).filter(Product.product_name == "Headset").first()
        self.assertEqual(product.stock_on_hand, 2)

    def test_status_lifecycle_transitions(self):
        """Test extended asset status transitions (MAINTENANCE, RETIRED, LOST)."""
        self.service.receive_stock(
            db=self.db,
            product_ref="Laptop",
            quantity=1,
            technician="Tech1",
            po_id="42",
            category="Laptop",
            serial_numbers=["STATUS-TEST-1"]
        )
        inv = self.db.query(Inventory).filter(Inventory.serial_number == "STATUS-TEST-1").first()
        self.assertEqual(inv.status, "AVAILABLE")

        # Update status to MAINTENANCE
        res = self.service.update_inventory_status(self.db, inv.id, "MAINTENANCE", "Tech1")
        self.assertEqual(res["new_status"], "MAINTENANCE")
        self.assertEqual(inv.status, "MAINTENANCE")

        # Cannot assign item in MAINTENANCE
        with self.assertRaises(ValueError):
            self.service.assign_stock(self.db, str(inv.id), 1, "T-999", "Tech1")

        # Update status to RETIRED
        res2 = self.service.update_inventory_status(self.db, inv.id, "RETIRED", "Tech1")
        self.assertEqual(res2["new_status"], "RETIRED")

        # Invalid status raises ValueError
        with self.assertRaises(ValueError):
            self.service.update_inventory_status(self.db, inv.id, "UNKNOWN_STATUS", "Tech1")

    def test_history_unified_audit(self):
        """Verify history returns IN and OUT records built from stock_entries & stock_exits."""
        self.service.receive_stock(
            db=self.db,
            product_ref="Headset",
            quantity=10,
            technician="Tech1",
            po_id="51",
            category="Headset",
            article_number="1001421"
        )
        inv = self.db.query(Inventory).filter(Inventory.article_number == "1001421").first()

        self.service.assign_stock(
            db=self.db,
            product_id=str(inv.id),
            quantity=2,
            ticket_id="T-999",
            technician="Tech1"
        )

        history = self.service.get_stock_history(self.db)
        self.assertEqual(len(history), 2)
        actions = [h["action"] for h in history]
        self.assertIn("IN", actions)
        self.assertIn("OUT", actions)
        for h in history:
            self.assertIn(h["source_table"], ["stock_entries", "stock_exits"])

    def test_bulk_upc_propagation_and_serialized_workflow(self):
        """Verify UPC propagated as inventory identifier for bulk products & serialized laptop workflow preserved."""
        # 1. Bulk Headset receive with extracted UPC
        upc_result = self.service.receive_stock(
            db=self.db,
            product_ref="Headset",
            quantity=20,
            technician="Tech1",
            po_id="3480",
            category="Headset",
            brand="EPOS",
            product_name="IMPACT 100 MS Stereo USB-C+A",
            article_number="1001421",
            serial_numbers=["84006441222"]
        )

        bulk_inv = self.db.query(Inventory).filter(Inventory.article_number == "1001421").first()
        self.assertIsNotNone(bulk_inv)
        self.assertEqual(bulk_inv.serial_number, "84006441222")  # Stored as UPC identifier
        self.assertEqual(bulk_inv.quantity_available, 20)
        self.assertEqual(upc_result["tracking_type"], "BULK")

        # 2. Serialized Laptop receive with extracted serial number (workflow unchanged)
        laptop_result = self.service.receive_stock(
            db=self.db,
            product_ref="Laptop",
            quantity=1,
            technician="Tech1",
            po_id="2000234706",
            category="Laptop",
            brand="Apple",
            product_name="MacBook Pro 16",
            article_number="MGEA4FN/A",
            serial_numbers=["C7R2RVDQVQ"]
        )

        laptop_inv = self.db.query(Inventory).filter(Inventory.serial_number == "C7R2RVDQVQ").first()
        self.assertIsNotNone(laptop_inv)
        self.assertEqual(laptop_inv.serial_number, "C7R2RVDQVQ")
        self.assertEqual(laptop_inv.quantity_available, 1)
        self.assertEqual(laptop_result["tracking_type"], "SERIALIZED")

    def test_product_name_sanitizes_image_filename(self):
        """Verify image filenames like uuid.jpg are never stored as product_name in inventory."""
        self.service.receive_stock(
            db=self.db,
            product_ref="Headset",
            quantity=5,
            technician="Tech1",
            po_id="3480",
            category="Headset",
            brand="EPOS",
            product_name="dd10586d-bbfb-47e9-9c4c-e41db368ed0f.jpg",
            article_number="1001421",
            serial_numbers=["84006441222"]
        )

        inv = self.db.query(Inventory).filter(Inventory.article_number == "1001421").first()
        self.assertIsNotNone(inv)
        self.assertNotEqual(inv.product_name, "dd10586d-bbfb-47e9-9c4c-e41db368ed0f.jpg")
        self.assertEqual(inv.product_name, "Headset")


if __name__ == "__main__":
    unittest.main()
