from app.database import SessionLocal
from app.models.purchase_order import PurchaseOrder
from app.models.document import Document

db = SessionLocal()
print("--- DB PURCHASE ORDERS ---")
pos = db.query(PurchaseOrder).all()
for po in pos:
    print(f"ID: {po.id} | PO: {po.po_number} | Desc: {po.description}")

print("\n--- DB DOCUMENTS ---")
docs = db.query(Document).all()
for doc in docs:
    print(f"ID: {doc.id} | Doc#: {doc.document_number} | Supplier: {doc.supplier}")
