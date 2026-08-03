"""Inventory Service for StockIT Architecture"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from ..models.inventory import Inventory, VALID_INVENTORY_STATUSES
from ..models.stock_entry import StockEntry
from ..models.stock_exit import StockExit
from ..models.product import Product, VALID_PRODUCT_NAMES, get_tracking_type
from ..models.purchase_order import PurchaseOrder
from ..models.ticket import Ticket

_PRODUCT_TYPE_NORMALIZE = {
    "LAPTOP": "Laptop",
    "MOUSE": "Mouse",
    "KEYBOARD": "Keyboard",
    "MONITOR": "Monitor",
    "HEADSET": "Headset",
    "EQUIPMENT": "Laptop",
    "LAPTOPS": "Laptop",
    "MICE": "Mouse",
    "MONITORS": "Monitor",
    "HEADPHONES": "Headset",
    "HEADPHONE": "Headset",
    "AUDIO": "Headset",
}

# Low-stock thresholds
PRODUCT_TYPE_LOW_STOCK_THRESHOLD = 5
INVENTORY_ITEM_LOW_STOCK_THRESHOLD = 2


class InventoryService:
    """Service for managing inventory, stock entries, stock exits, and dashboard KPIs"""

    def _resolve_product(self, db: Session, product_type_hint: Optional[str]) -> Product:
        """Resolve product category string -> Products row. Always returns a valid Product with tracking_type."""
        if not product_type_hint:
            raise ValueError("Product type/category is required to resolve product.")

        raw = str(product_type_hint).strip()
        if raw.upper() in _PRODUCT_TYPE_NORMALIZE:
            resolved = _PRODUCT_TYPE_NORMALIZE[raw.upper()]
        elif raw in VALID_PRODUCT_NAMES:
            resolved = raw
        else:
            lowered = {pt.upper(): pt for pt in VALID_PRODUCT_NAMES}
            if raw.upper() in lowered:
                resolved = lowered[raw.upper()]
            else:
                raise ValueError(
                    f"Unknown product category '{raw}'. Expected one of: {', '.join(VALID_PRODUCT_NAMES)}."
                )

        product = db.query(Product).filter(Product.product_name == resolved).first()
        if product is None:
            track_type = get_tracking_type(resolved)
            product = Product(product_name=resolved, tracking_type=track_type, stock_on_hand=0)
            db.add(product)
            db.flush()
        return product

    def _resolve_purchase_order_id(self, db: Session, po_id: Optional[str]) -> int:
        """Resolve database PurchaseOrder primary key from a PO id or PO number."""
        from ..models.document import Document

        if po_id is None or str(po_id).strip() == "":
            fallback_doc = db.query(Document).order_by(Document.id.desc()).first()
            if fallback_doc is None:
                fallback_doc = Document(
                    document_type="fallback",
                    document_number="DOC-FALLBACK-0001",
                    supplier="Unknown Supplier",
                    image_path="",
                    extracted_text="",
                )
                db.add(fallback_doc)
                db.flush()
            fallback_po = PurchaseOrder(
                document_id=fallback_doc.id,
                po_number="PO-FALLBACK-0001",
                description="Auto-created PO fallback",
                serial_numbers=None,
            )
            db.add(fallback_po)
            db.flush()
            return fallback_po.id

        po_value = str(po_id).strip()

        # 1. Search by exact po_number string match first (most common)
        po_record = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_value).first()
        if po_record:
            return po_record.id

        # 2. Try integer primary key id match if numeric and < 1000000
        try:
            numeric_id = int(po_value)
            if numeric_id < 1000000:
                po_record = db.query(PurchaseOrder).filter(PurchaseOrder.id == numeric_id).first()
                if po_record:
                    return po_record.id
        except ValueError:
            pass

        # 3. Fallback PO row creation if PO number not found in database
        fallback_doc = db.query(Document).order_by(Document.id.desc()).first()
        if fallback_doc is None:
            fallback_doc = Document(
                document_type="fallback",
                document_number="DOC-FALLBACK-0002",
                supplier="Unknown Supplier",
                image_path="",
                extracted_text="",
            )
            db.add(fallback_doc)
            db.flush()

        auto_po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_value).first()
        if auto_po:
            return auto_po.id

        auto_po = PurchaseOrder(
            document_id=fallback_doc.id,
            po_number=po_value,
            description=f"Auto-created PO for {po_value}",
            serial_numbers=None,
        )
        db.add(auto_po)
        db.flush()
        return auto_po.id

    def _normalize_serial_list(self, serial_numbers: Optional[List[str]]) -> List[str]:
        """Split legacy comma-separated strings, strip, dedupe preserving order, skip empty."""
        if not serial_numbers:
            return []
        out: List[str] = []
        seen = set()
        for item in serial_numbers:
            if item is None:
                continue
            for tok in str(item).split(","):
                tok_clean = tok.strip()
                if tok_clean and tok_clean not in seen:
                    seen.add(tok_clean)
                    out.append(tok_clean)
        return out

    def _sanitize_product_name(self, raw_name: Optional[str], default_name: str) -> str:
        """Ensure product_name is a clean human-readable product description, never an image filename like uuid.jpg or path."""
        if not raw_name:
            return default_name

        clean_str = str(raw_name).strip()

        # Reject image filenames, file extensions, paths, and UUIDs
        if (
            re.search(r'\.(?:jpg|jpeg|png|webp|gif|pdf|tiff|bmp)$', clean_str, re.IGNORECASE)
            or '/' in clean_str
            or '\\' in clean_str
            or re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', clean_str, re.IGNORECASE)
        ):
            return default_name

        return clean_str

    def receive_stock(
        self,
        db: Session,
        product_ref: str,
        quantity: int,
        technician: str,
        po_id: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        product_name: Optional[str] = None,
        article_number: Optional[str] = None,
        serial_numbers: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record stock receive operation.
        Strictly enforces SERIALIZED vs BULK behavior based on master product.tracking_type.
        """
        now = datetime.utcnow()
        if quantity is None or quantity <= 0:
            raise ValueError("Quantity received must be greater than 0.")

        product = self._resolve_product(db, category or product_ref)
        tracking_type = product.tracking_type  # Defined on products table
        po_db_id = self._resolve_purchase_order_id(db, po_id)

        cleaned_serials = self._normalize_serial_list(serial_numbers)
        resolved_article = article_number or product_ref
        clean_product_name = self._sanitize_product_name(product_name, default_name=product.product_name)

        try:
            if tracking_type == "SERIALIZED":
                # Validation: serial numbers required
                if not cleaned_serials:
                    raise ValueError(
                        f"Serial number is required for serialized product '{product.product_name}'."
                    )
                if len(cleaned_serials) != quantity:
                    raise ValueError(
                        f"Serial number count ({len(cleaned_serials)}) does not match quantity ({quantity}) "
                        f"for serialized product '{product.product_name}'."
                    )

                created_inventory_ids = []
                for serial in cleaned_serials:
                    # Duplicate serial check for active serialized items
                    existing = (
                        db.query(Inventory)
                        .filter(
                            Inventory.product_id == product.id,
                            Inventory.serial_number == serial,
                            Inventory.status.in_(["AVAILABLE", "ASSIGNED", "MAINTENANCE"])
                        )
                        .first()
                    )
                    if existing:
                        raise ValueError(
                            f"Serial number '{serial}' already exists for active asset in product '{product.product_name}'."
                        )

                    inv = Inventory(
                        purchase_order_id=po_db_id,
                        product_id=product.id,
                        brand=brand or "Generic",
                        product_name=clean_product_name,
                        article_number=resolved_article,
                        serial_number=serial,
                        quantity_available=1,
                        status="AVAILABLE",
                        received_by=technician,
                        received_at=now,
                    )
                    db.add(inv)
                    db.flush()

                    stock_entry = StockEntry(
                        inventory_id=inv.id,
                        purchase_order_id=po_db_id,
                        quantity_received=1,
                        created_by=technician,
                        created_at=now,
                    )
                    db.add(stock_entry)
                    created_inventory_ids.append(inv.id)

                # Increment aggregate stock
                product.stock_on_hand = (product.stock_on_hand or 0) + quantity
                db.commit()

                return {
                    "id": f"SE-{created_inventory_ids[0]}",
                    "product_id": product.id,
                    "action": "IN",
                    "quantity": quantity,
                    "user": technician,
                    "po_id": str(po_db_id),
                    "tracking_type": "SERIALIZED",
                    "inventory_ids": created_inventory_ids,
                    "timestamp": now.isoformat(),
                }

            else:  # BULK
                upc_value = cleaned_serials[0] if cleaned_serials else None

                # Check for existing matching bulk inventory row
                existing_bulk = (
                    db.query(Inventory)
                    .join(Product, Inventory.product_id == Product.id)
                    .filter(
                        Inventory.product_id == product.id,
                        Inventory.purchase_order_id == po_db_id,
                        Inventory.article_number == resolved_article,
                        Product.tracking_type == "BULK",
                        Inventory.status == "AVAILABLE"
                    )
                    .first()
                )

                if existing_bulk:
                    existing_bulk.quantity_available = (existing_bulk.quantity_available or 0) + quantity
                    if upc_value and not existing_bulk.serial_number:
                        existing_bulk.serial_number = upc_value
                    if clean_product_name and clean_product_name != product.product_name:
                        existing_bulk.product_name = clean_product_name
                    inv = existing_bulk
                else:
                    inv = Inventory(
                        purchase_order_id=po_db_id,
                        product_id=product.id,
                        brand=brand or "Generic",
                        product_name=clean_product_name,
                        article_number=resolved_article,
                        serial_number=upc_value,
                        quantity_available=quantity,
                        status="AVAILABLE",
                        received_by=technician,
                        received_at=now,
                    )
                    db.add(inv)
                    db.flush()

                stock_entry = StockEntry(
                    inventory_id=inv.id,
                    purchase_order_id=po_db_id,
                    quantity_received=quantity,
                    created_by=technician,
                    created_at=now,
                )
                db.add(stock_entry)

                product.stock_on_hand = (product.stock_on_hand or 0) + quantity
                db.commit()

                return {
                    "id": f"SE-{stock_entry.id}",
                    "product_id": product.id,
                    "action": "IN",
                    "quantity": quantity,
                    "user": technician,
                    "po_id": str(po_db_id),
                    "tracking_type": "BULK",
                    "inventory_id": inv.id,
                    "timestamp": now.isoformat(),
                }

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to receive stock: {str(e)}")

    def assign_stock(
        self,
        db: Session,
        product_id: str,
        quantity: int,
        ticket_id: str,
        technician: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record stock assignment (stock out).
        Enforces SERIALIZED vs BULK assignment rules based on product tracking_type.
        """
        now = datetime.utcnow()
        if quantity is None or quantity <= 0:
            raise ValueError("Assignment quantity must be greater than 0.")

        if not ticket_id:
            raise ValueError("Ticket ID is required for stock assignment.")

        # Check ticket exists (or format validation)
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            ticket = Ticket(
                id=ticket_id,
                title=f"Assignment to {ticket_id}",
                status="Open",
                requester=technician,
            )
            db.add(ticket)
            db.flush()

        # Resolve Inventory item
        target_inv: Optional[Inventory] = None
        try:
            int_id = int(str(product_id))
            target_inv = db.query(Inventory).filter(Inventory.id == int_id).first()
        except ValueError:
            target_inv = (
                db.query(Inventory)
                .filter(
                    (Inventory.article_number == str(product_id))
                    | (Inventory.serial_number == str(product_id))
                )
                .filter(Inventory.quantity_available > 0)
                .order_by(Inventory.id.asc())
                .first()
            )

        if not target_inv:
            raise ValueError(f"Could not locate available inventory record for '{product_id}'.")

        tracking_type = target_inv.tracking_type

        try:
            if tracking_type == "SERIALIZED":
                if quantity != 1:
                    raise ValueError("Serialized equipment assignment quantity must be exactly 1.")

                if target_inv.status != "AVAILABLE" or target_inv.quantity_available < 1:
                    raise ValueError(
                        f"Serialized asset ID {target_inv.id} (serial: '{target_inv.serial_number}') "
                        f"is not available (current status: {target_inv.status})."
                    )

                target_inv.status = "ASSIGNED"
                target_inv.quantity_available = 0

                stock_exit = StockExit(
                    inventory_id=target_inv.id,
                    ticket_id=ticket_id,
                    quantity=1,
                    created_by=technician,
                    created_at=now,
                )
                db.add(stock_exit)

                # Decrement aggregate stock
                if target_inv.product_id:
                    prod = db.query(Product).filter(Product.id == target_inv.product_id).first()
                    if prod:
                        prod.stock_on_hand = max(0, (prod.stock_on_hand or 0) - 1)

                db.commit()

                return {
                    "id": f"SX-{stock_exit.id}",
                    "product_id": target_inv.product_id,
                    "action": "OUT",
                    "quantity": 1,
                    "user": technician,
                    "ticket_id": ticket_id,
                    "timestamp": now.isoformat(),
                }

            else:  # BULK
                if target_inv.quantity_available < quantity:
                    raise ValueError(
                        f"Insufficient bulk stock for item ID {target_inv.id}: "
                        f"requested {quantity}, available {target_inv.quantity_available}."
                    )

                target_inv.quantity_available -= quantity

                stock_exit = StockExit(
                    inventory_id=target_inv.id,
                    ticket_id=ticket_id,
                    quantity=quantity,
                    created_by=technician,
                    created_at=now,
                )
                db.add(stock_exit)

                if target_inv.product_id:
                    prod = db.query(Product).filter(Product.id == target_inv.product_id).first()
                    if prod:
                        prod.stock_on_hand = max(0, (prod.stock_on_hand or 0) - quantity)

                db.commit()

                return {
                    "id": f"SX-{stock_exit.id}",
                    "product_id": target_inv.product_id,
                    "action": "OUT",
                    "quantity": quantity,
                    "user": technician,
                    "ticket_id": ticket_id,
                    "timestamp": now.isoformat(),
                }

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to assign stock: {str(e)}")

    def update_inventory_status(
        self,
        db: Session,
        inventory_id: int,
        new_status: str,
        technician: str
    ) -> Dict[str, Any]:
        """Update lifecycle status of an inventory item (AVAILABLE, ASSIGNED, MAINTENANCE, RETIRED, LOST)."""
        status_upper = new_status.upper()
        if status_upper not in VALID_INVENTORY_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. Expected one of: {', '.join(VALID_INVENTORY_STATUSES)}"
            )

        inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
        if not inv:
            raise ValueError(f"Inventory item ID {inventory_id} not found.")

        old_status = inv.status
        inv.status = status_upper
        db.commit()
        db.refresh(inv)

        return {
            "id": inv.id,
            "old_status": old_status,
            "new_status": inv.status,
            "technician": technician,
            "updated_at": datetime.utcnow().isoformat()
        }

    def get_stock_history(
        self,
        db: Session,
        *,
        limit: int = 100,
        action: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Unified stock activity timeline from stock_entries (IN) and stock_exits (OUT).
        """
        records: List[Dict[str, Any]] = []

        entry_rows = (
            db.query(StockEntry, Inventory, Product.product_name, PurchaseOrder.po_number)
            .outerjoin(Inventory, StockEntry.inventory_id == Inventory.id)
            .outerjoin(Product, Inventory.product_id == Product.id)
            .outerjoin(PurchaseOrder, StockEntry.purchase_order_id == PurchaseOrder.id)
            .order_by(StockEntry.created_at.desc())
            .limit(limit)
            .all()
        )
        for entry, inv, product_name, po_number in entry_rows:
            records.append(
                {
                    "id": f"SE-{entry.id}",
                    "source_table": "stock_entries",
                    "source_id": entry.id,
                    "action": "IN",
                    "inventory_id": entry.inventory_id,
                    "product_name": product_name or "Unknown",
                    "article_number": inv.article_number if inv else None,
                    "category": product_name,
                    "quantity": entry.quantity_received,
                    "po_number": po_number,
                    "ticket_id": None,
                    "technician": entry.created_by,
                    "timestamp": entry.created_at,
                    "reference": inv.article_number if inv else None,
                    "notes": f"Stock entry #{entry.id}",
                }
            )

        exit_rows = (
            db.query(StockExit, Inventory, Product.product_name, PurchaseOrder.po_number)
            .outerjoin(Inventory, StockExit.inventory_id == Inventory.id)
            .outerjoin(Product, Inventory.product_id == Product.id)
            .outerjoin(PurchaseOrder, Inventory.purchase_order_id == PurchaseOrder.id)
            .order_by(StockExit.created_at.desc())
            .limit(limit)
            .all()
        )
        for exit_row, inv, product_name, po_number in exit_rows:
            records.append(
                {
                    "id": f"SX-{exit_row.id}",
                    "source_table": "stock_exits",
                    "source_id": exit_row.id,
                    "action": "OUT",
                    "inventory_id": exit_row.inventory_id,
                    "product_name": product_name or "Unknown",
                    "article_number": inv.article_number if inv else None,
                    "category": product_name,
                    "quantity": exit_row.quantity,
                    "po_number": po_number,
                    "ticket_id": exit_row.ticket_id,
                    "technician": exit_row.created_by,
                    "timestamp": exit_row.created_at,
                    "reference": inv.article_number if inv else None,
                    "notes": f"Stock exit #{exit_row.id} to ticket {exit_row.ticket_id}",
                }
            )

        if action:
            action_upper = action.upper()
            records = [r for r in records if r["action"] == action_upper]

        records.sort(key=lambda r: r["timestamp"] or datetime.min, reverse=True)
        return records[:limit]

    def list_inventory_items(
        self,
        db: Session,
        *,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Return all inventory rows joined with product name and PO number."""
        query = (
            db.query(Inventory, Product.product_name, Product.tracking_type, PurchaseOrder.po_number)
            .join(Product, Inventory.product_id == Product.id)
            .outerjoin(PurchaseOrder, Inventory.purchase_order_id == PurchaseOrder.id)
            .order_by(Inventory.received_at.desc())
        )

        if category:
            query = query.filter(Product.product_name.ilike(f"%{category}%"))
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                (Inventory.article_number.ilike(term))
                | (Inventory.serial_number.ilike(term))
                | (Product.product_name.ilike(term))
            )

        rows = query.limit(limit).all()
        return [
            {
                "id": inv.id,
                "product_id": inv.product_id,
                "category": product_name,
                "article_number": inv.article_number,
                "serial_number": inv.serial_number,
                "quantity_available": inv.quantity_available,
                "tracking_type": tracking_type,
                "status": inv.status,
                "received_by": inv.received_by,
                "received_at": inv.received_at,
                "purchase_order_id": inv.purchase_order_id,
                "po_number": po_number,
            }
            for inv, product_name, tracking_type, po_number in rows
        ]

    def get_inventory_item(self, db: Session, inventory_id: int) -> Optional[Dict[str, Any]]:
        """Return a single inventory row with joins."""
        row = (
            db.query(Inventory, Product.product_name, Product.tracking_type, PurchaseOrder.po_number)
            .join(Product, Inventory.product_id == Product.id)
            .outerjoin(PurchaseOrder, Inventory.purchase_order_id == PurchaseOrder.id)
            .filter(Inventory.id == inventory_id)
            .first()
        )
        if not row:
            return None
        inv, product_name, tracking_type, po_number = row
        return {
            "id": inv.id,
            "product_id": inv.product_id,
            "category": product_name,
            "article_number": inv.article_number,
            "serial_number": inv.serial_number,
            "quantity_available": inv.quantity_available,
            "tracking_type": tracking_type,
            "status": inv.status,
            "received_by": inv.received_by,
            "received_at": inv.received_at,
            "purchase_order_id": inv.purchase_order_id,
            "po_number": po_number,
        }

    def get_dashboard_kpis(self, db: Session) -> Dict[str, Any]:
        """Compute dashboard KPIs strictly from stock_entries, stock_exits, products, and inventory."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        total_inventory_records = db.query(Inventory).count()
        total_inventory_quantity = int(
            db.query(sa_func.coalesce(sa_func.sum(Inventory.quantity_available), 0)).scalar() or 0
        )

        total_product_types = db.query(Product).count()
        active_product_types = (
            db.query(Product).filter(Product.stock_on_hand > 0).count()
        )

        total_tickets = db.query(Ticket).count()
        open_tickets = (
            db.query(Ticket)
            .filter(Ticket.status.notin_(["Assigned", "Closed"]))
            .count()
        )
        fulfilled_tickets = total_tickets - open_tickets
        ticket_fulfillment_rate = (
            round((fulfilled_tickets / total_tickets) * 100, 1) if total_tickets > 0 else 0.0
        )

        total_purchase_orders = db.query(PurchaseOrder).count()

        # Movement analytics computed from stock_entries & stock_exits
        stock_in_this_week = int(
            db.query(sa_func.coalesce(sa_func.sum(StockEntry.quantity_received), 0))
            .filter(StockEntry.created_at >= week_ago)
            .scalar()
            or 0
        )
        stock_out_this_week = int(
            db.query(sa_func.coalesce(sa_func.sum(StockExit.quantity), 0))
            .filter(StockExit.created_at >= week_ago)
            .scalar()
            or 0
        )
        movements_this_week = (
            db.query(StockEntry).filter(StockEntry.created_at >= week_ago).count()
            + db.query(StockExit).filter(StockExit.created_at >= week_ago).count()
        )

        status_distribution: Dict[str, int] = {}
        for (st,) in db.query(Inventory.status).distinct().all():
            status_distribution[st] = (
                db.query(Inventory).filter(Inventory.status == st).count()
            )

        product_rows = db.query(Product).all()
        type_order = {pt: idx for idx, pt in enumerate(VALID_PRODUCT_NAMES)}
        sorted_products = sorted(
            product_rows,
            key=lambda p: type_order.get(p.product_name, 999),
        )

        category_stock: List[Dict[str, Any]] = []
        for product in sorted_products:
            inventory_records = (
                db.query(Inventory).filter(Inventory.product_id == product.id).count()
            )
            share_percent = (
                round((product.stock_on_hand / total_inventory_quantity) * 100, 1)
                if total_inventory_quantity > 0
                else 0.0
            )
            category_stock.append(
                {
                    "product_type": product.product_name,
                    "tracking_type": product.tracking_type,
                    "stock_on_hand": product.stock_on_hand or 0,
                    "inventory_records": inventory_records,
                    "share_percent": share_percent,
                }
            )

        low_stock_alerts: List[Dict[str, Any]] = []
        for product in sorted_products:
            qty = product.stock_on_hand or 0
            if qty <= PRODUCT_TYPE_LOW_STOCK_THRESHOLD:
                low_stock_alerts.append(
                    {
                        "alert_type": "product_type",
                        "product_type": product.product_name,
                        "product_name": None,
                        "article_number": None,
                        "inventory_id": None,
                        "current_quantity": qty,
                        "threshold": PRODUCT_TYPE_LOW_STOCK_THRESHOLD,
                        "severity": "critical" if qty == 0 else "warning",
                    }
                )

        category_alert_count = sum(
            1 for a in low_stock_alerts if a["alert_type"] == "product_type"
        )

        return {
            "total_inventory_quantity": total_inventory_quantity,
            "total_inventory_records": total_inventory_records,
            "total_product_types": total_product_types,
            "active_product_types": active_product_types,
            "open_tickets": open_tickets,
            "total_tickets": total_tickets,
            "ticket_fulfillment_rate": ticket_fulfillment_rate,
            "movements_this_week": movements_this_week,
            "stock_in_this_week": stock_in_this_week,
            "stock_out_this_week": stock_out_this_week,
            "total_purchase_orders": total_purchase_orders,
            "low_stock_alert_count": category_alert_count,
            "low_stock_alerts": low_stock_alerts,
            "category_stock": category_stock,
            "status_distribution": status_distribution,
        }


# Global instance
inventory_service = InventoryService()
