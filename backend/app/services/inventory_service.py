"""Inventory Service for Stock Entry Workflow"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.inventory import Inventory, InventoryMovement, Ticket
from ..models.stock_entry import StockEntry
from ..models.stock_exit import StockExit
from ..models.product import Product, VALID_PRODUCT_TYPES
from ..models.purchase_order import PurchaseOrder
from ..schemas.stock_entry import WorkflowState


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


class InventoryService:
    """Service for managing inventory in Stock Entry workflow"""

    def __init__(self):
        pass

    def _debug_print(self, step: str, message: str) -> None:
        """Print a consistent debug line for step-by-step workflow tracing."""
        print(f"[stock-in:{step}] {message}")

    def _inventory_snapshot(self, inventory: Inventory) -> Dict[str, Any]:
        """Return a plain dictionary snapshot of an Inventory row for logging."""
        return {
            "id": inventory.id,
            "purchase_order_id": inventory.purchase_order_id,
            "product_id": inventory.product_id,
            "category": inventory.category,
            "brand": inventory.brand,
            "product_name": inventory.product_name,
            "article_number": inventory.article_number,
            "serial_number": inventory.serial_number,
            "quantity_available": inventory.quantity_available,
            "status": inventory.status,
            "received_by": inventory.received_by,
            "received_at": inventory.received_at.isoformat() if inventory.received_at else None,
        }

    def _stock_entry_snapshot(self, stock_entry: StockEntry) -> Dict[str, Any]:
        """Return a plain dictionary snapshot of a StockEntry row for logging."""
        return {
            "id": stock_entry.id,
            "inventory_id": stock_entry.inventory_id,
            "quantity_received": stock_entry.quantity_received,
            "created_by": stock_entry.created_by,
            "created_at": stock_entry.created_at.isoformat() if stock_entry.created_at else None,
        }

    # ------------------------------------------------------------------
    # Product resolution & stock_on_hand sync helpers
    # ------------------------------------------------------------------
    def _resolve_product(self, db: Session, product_type_hint: Optional[str]) -> Product:
        """Resolve YOLO `category` string → Products row. product_id is NEVER NULL after this call."""
        if not product_type_hint:
            raise ValueError("Product type (YOLO detection category) is required to resolve product_id")

        raw = str(product_type_hint).strip()
        if raw.upper() in _PRODUCT_TYPE_NORMALIZE:
            resolved = _PRODUCT_TYPE_NORMALIZE[raw.upper()]
        elif raw in VALID_PRODUCT_TYPES:
            resolved = raw
        else:
            # No direct match: try case-insensitive lookup against the 5 valid types
            lowered = {pt.upper(): pt for pt in VALID_PRODUCT_TYPES}
            if raw.upper() in lowered:
                resolved = lowered[raw.upper()]
            else:
                raise ValueError(
                    f"Unknown product type '{raw}'. Expected one of: {', '.join(VALID_PRODUCT_TYPES)}."
                )

        product = db.query(Product).filter(Product.product_type == resolved).first()
        if product is None:
            # Safety net: create on the fly if Products table exists but row is missing
            product = Product(product_type=resolved, stock_on_hand=0)
            db.add(product)
            db.flush()
            self._debug_print(
                "product_resolver",
                f"Products row missing for type={resolved}; created id={product.id}",
            )
        return product

    def _adjust_product_stock(self, db: Session, product_id: int, delta: int) -> None:
        """Delta Products.stock_on_hand; safe for +/-. Never goes below 0 on decrement (clamp)."""
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise ValueError(f"Product id={product_id} not found while adjusting stock_on_hand")
        new_val = (product.stock_on_hand or 0) + delta
        if new_val < 0:
            new_val = 0
        product.stock_on_hand = new_val
        db.flush()

    def _persist_movement(
        self,
        db: Session,
        *,
        mov_id: str,
        product_id_ref: str,
        action: str,
        quantity: int,
        user: str,
        product_name: Optional[str] = None,
        po_id: Optional[str] = None,
        reference: Optional[str] = None,
        ticket_id: Optional[str] = None,
        assignee: Optional[str] = None,
        notes: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> InventoryMovement:
        """Actually INSERT an InventoryMovement row (fixes prior known issue where history table stayed empty)."""
        ts = now or datetime.utcnow()
        row = InventoryMovement(
            id=mov_id,
            product_id=str(product_id_ref),
            product_name=product_name,
            action=action,
            quantity=quantity,
            user=user,
            po_id=po_id,
            reference=reference,
            ticket_id=ticket_id,
            assignee=assignee,
            notes=notes,
            timestamp=ts,
        )
        db.add(row)
        db.flush()
        return row

    def _persist_stock_entry(
        self, db: Session, inventory_id: int, quantity_received: int, created_by: str
    ) -> StockEntry:
        se = StockEntry(
            inventory_id=inventory_id,
            quantity_received=quantity_received,
            created_by=created_by,
        )
        db.add(se)
        db.flush()
        return se

    def _persist_stock_exit(
        self, db: Session, inventory_id: int, ticket_number: str, quantity: int, created_by: str
    ) -> StockExit:
        sx = StockExit(
            inventory_id=inventory_id,
            ticket_number=ticket_number,
            quantity=quantity,
            created_by=created_by,
        )
        db.add(sx)
        db.flush()
        return sx

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

    def _apply_meta(self, inv: Inventory, *, brand, product_name, article_number, serial_number, technician: Optional[str] = None, now: Optional[datetime] = None) -> None:
        """Idempotently enrich existing inventory row with incoming meta, without overwriting specific data."""
        if brand and (not inv.brand or inv.brand in ("Generic", "")):
            inv.brand = brand
        if product_name and (not inv.product_name or inv.product_name in ("Unknown", "")):
            inv.product_name = product_name
        if article_number and (not inv.article_number or inv.article_number == product_name):
            inv.article_number = article_number
        if serial_number:
            inv.serial_number = serial_number
        if technician:
            inv.received_by = technician
            if now is not None:
                inv.received_at = now

    # ------------------------------------------------------------------
    # Stock IN (Entry Workflow Workflow1)
    # ------------------------------------------------------------------
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
        serial_numbers: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record stock-in movement with Product FK synchronization and per-serial Laptop uniqueness."""
        import uuid

        now = datetime.utcnow()
        self._debug_print(
            "start",
            f"product_ref={product_ref}, quantity={quantity}, technician={technician}, po_id={po_id}, category={category}",
        )

        # 1) Resolve Product row — product_id will NEVER be NULL after this.
        try:
            product = self._resolve_product(db, category)
        except ValueError as ve:
            raise ve

        # 2) Resolve PurchaseOrder FK
        resolved_po_db_id = self._resolve_purchase_order_id(db, po_id)
        self._debug_print("po_resolve", f"Resolved purchase_order_id={resolved_po_db_id}")

        # 3) Normalize serials
        cleaned_serials = self._normalize_serial_list(serial_numbers)
        payload_qty = int(quantity) if quantity is not None and quantity > 0 else 1

        # 4) Decide strategy by product_type
        is_laptop = product.product_type == "Laptop"
        # Per-serial laptop rows when each unit has its own serial. A single batch/data-matrix
        # code on the shipping label (qty > 1, one serial) is stored as one bulk inventory row.
        use_laptop_per_serial = (
            is_laptop
            and cleaned_serials
            and (len(cleaned_serials) > 1 or payload_qty == 1)
        )
        movements_returned: List[Dict[str, Any]] = []
        total_quantity_delta = 0

        try:
            if use_laptop_per_serial:
                # --- Laptop rule: one Inventory row per serial_number. Merge ONLY by (product_id, serial_number).
                # --- Never merge by article_number, PO, supplier, or label.
                if not cleaned_serials:
                    raise ValueError(
                        "Laptops require at least one serial number to ensure uniqueness. "
                        "Please scan or re-enter serial numbers before receiving."
                    )

                for serial in cleaned_serials:
                    existing = (
                        db.query(Inventory)
                        .filter(
                            Inventory.product_id == product.id,
                            Inventory.serial_number == serial,
                        )
                        .first()
                    )
                    if existing is None:
                        inv = Inventory(
                            purchase_order_id=resolved_po_db_id,
                            product_id=product.id,
                            brand=brand or "Generic",
                            product_name=product_name or product_ref,
                            article_number=article_number or product_ref,
                            serial_number=serial,
                            quantity_available=1,
                            status="AVAILABLE",
                            received_by=technician,
                            received_at=now,
                        )
                        db.add(inv)
                        db.flush()
                        self._debug_print(
                            "laptop_create",
                            f"serial={serial} -> new inventory id={inv.id}",
                        )
                    else:
                        existing.quantity_available = existing.quantity_available or 0
                        self._apply_meta(
                            existing,
                            brand=brand,
                            product_name=product_name,
                            article_number=article_number,
                            serial_number=serial,
                            technician=technician,
                            now=now,
                        )
                        db.flush()
                        inv = existing
                        self._debug_print(
                            "laptop_update",
                            f"serial={serial} -> matched existing inventory id={inv.id}",
                        )

                    # Audit trails + stock counter per serial
                    self._adjust_product_stock(db, product.id, +1)
                    total_quantity_delta += 1
                    self._persist_stock_entry(db, inv.id, 1, technician)
                    mov_id_inner = f"MOV-{str(uuid.uuid4())[:8].upper()}"
                    self._persist_movement(
                        db,
                        mov_id=mov_id_inner,
                        product_id_ref=product_ref,
                        action="IN",
                        quantity=1,
                        user=technician,
                        product_name=product_name or product_ref,
                        po_id=po_id or f"PO-{resolved_po_db_id}",
                        reference=article_number or product_ref,
                        notes=(notes or "") + (f" [serial={serial}]" if serial else ""),
                        now=now,
                    )
                    movements_returned.append(
                        {
                            "id": mov_id_inner,
                            "inventory_id": inv.id,
                            "serial": serial,
                        }
                    )

                db.commit()

            else:
                # --- Bulk receive: non-laptop always; laptop when one batch serial covers many units.
                if is_laptop and not cleaned_serials:
                    raise ValueError(
                        "Laptops require at least one serial number to ensure uniqueness. "
                        "Please scan or re-enter serial numbers before receiving."
                    )

                resolved_article = article_number or product_ref
                resolved_brand = brand or "Generic"
                resolved_name = product_name or product_ref
                resolved_serial = (
                    ",".join(cleaned_serials) if cleaned_serials else None
                )

                inv = Inventory(
                    purchase_order_id=resolved_po_db_id,
                    product_id=product.id,
                    brand=resolved_brand,
                    product_name=resolved_name,
                    article_number=resolved_article,
                    serial_number=resolved_serial,
                    quantity_available=payload_qty,
                    status="AVAILABLE",
                    received_by=technician,
                    received_at=now,
                )
                db.add(inv)
                db.flush()
                self._debug_print(
                    "nonlaptop_create",
                    (
                        f"product_type={product.product_type}, qty={payload_qty}, "
                        f"article={resolved_article} -> inventory id={inv.id}"
                    ),
                )

                self._adjust_product_stock(db, product.id, +payload_qty)
                total_quantity_delta += payload_qty
                self._persist_stock_entry(db, inv.id, payload_qty, technician)
                mov_id_inner = f"MOV-{str(uuid.uuid4())[:8].upper()}"
                self._persist_movement(
                    db,
                    mov_id=mov_id_inner,
                    product_id_ref=product_ref,
                    action="IN",
                    quantity=payload_qty,
                    user=technician,
                    product_name=resolved_name,
                    po_id=po_id or f"PO-{resolved_po_db_id}",
                    reference=resolved_article,
                    notes=notes,
                    now=now,
                )
                movements_returned.append(
                    {"id": mov_id_inner, "inventory_id": inv.id, "serial": None}
                )

                db.commit()

            db.refresh(product)
            self._debug_print(
                "commit",
                (
                    f"product_type={product.product_type}, total_delta_qty={total_quantity_delta}, "
                    f"products.stock_on_hand now={product.stock_on_hand}, rows_inserted_or_updated={len(movements_returned)}"
                ),
            )

            # Return the *first* movement in the same response shape as before.
            # (Workflow1 mobile contract expects a single-movement response.)
            if movements_returned:
                mov_first_id = movements_returned[0]["id"]
            else:
                mov_first_id = f"MOV-{str(uuid.uuid4())[:8].upper()}"

            return {
                "id": mov_first_id,
                "product_id": product_ref,
                "action": "IN",
                "quantity": total_quantity_delta,
                "user": technician,
                "product_name": product_name or product_ref,
                "po_id": po_id or f"PO-{resolved_po_db_id}",
                "reference": article_number or product_ref,
                "notes": notes,
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            db.rollback()
            self._debug_print("error", f"Transaction rolled back: {e}")
            raise ValueError(f"Failed to receive stock: {e}")

    def _resolve_purchase_order_id(self, db: Session, po_id: Optional[str]) -> int:
        """Resolve the database PurchaseOrder primary key from a PO id or PO number.

        If po_id can't be found, create a dummy linked PO as last resort to keep Workflow1
        persistence running against the foreign-key constraint (never lose a stock-in because
        of missing PO cache row).
        """
        from ..models.document import Document

        if po_id is None or str(po_id).strip() == "":
            # Create fallback PO, linked to a synthetic document row (so FK constraints hold).
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
                description="Auto-created PO fallback (po_id missing at receive_stock)",
                serial_numbers=None,
            )
            db.add(fallback_po)
            db.flush()
            return fallback_po.id

        po_value = str(po_id).strip()

        try:
            numeric_id = int(po_value)
            po_record = db.query(PurchaseOrder).filter(PurchaseOrder.id == numeric_id).first()
            if po_record:
                return po_record.id
        except ValueError:
            pass

        po_record = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_value).first()
        if po_record:
            return po_record.id

        # Final last-resort: create a PO row so Inventory FK is never violated.
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
        auto_po = PurchaseOrder(
            document_id=fallback_doc.id,
            po_number=po_value,
            description=f"Auto-created PO for receive_stock import of {po_value}",
            serial_numbers=None,
        )
        db.add(auto_po)
        db.flush()
        self._debug_print(
            "po_resolve",
            f"PO lookup failed for po_value={po_value}; auto-created PO id={auto_po.id}",
        )
        return auto_po.id

    # ------------------------------------------------------------------
    # Stock OUT (Assign Equipment)
    # ------------------------------------------------------------------
    def assign_stock(
        self,
        db: Session,
        product_id: str,
        quantity: int,
        ticket_id: str,
        technician: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record stock-out assignment movement — decrements inventory, Products.stock_on_hand, writes StockExit + InventoryMovement."""
        import uuid

        mov_id = f"MOV-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.utcnow()

        try:
            # Resolve target Inventory row: accept either Inventory.id (int) or Inventory.article_number string.
            target_inv: Optional[Inventory] = None
            try:
                int_id = int(str(product_id))
                target_inv = db.query(Inventory).filter(Inventory.id == int_id).first()
            except ValueError:
                target_inv = (
                    db.query(Inventory)
                    .filter(
                        (Inventory.article_number == str(product_id))
                        | (Inventory.product_name == str(product_id))
                    )
                    .order_by(Inventory.id.asc())
                    .first()
                )

            if not target_inv:
                raise ValueError(
                    f"Could not locate inventory record matching product_id={product_id}"
                )

            # Decrement inventory quantity_available (never below 0)
            new_inv_qty = (target_inv.quantity_available or 0) - quantity
            if new_inv_qty < 0:
                raise ValueError(
                    f"Insufficient stock for inventory id={target_inv.id}: "
                    f"requested={quantity}, available={target_inv.quantity_available}"
                )
            target_inv.quantity_available = new_inv_qty
            if target_inv.status == "AVAILABLE" and new_inv_qty == 0:
                target_inv.status = "ASSIGNED"
            db.flush()

            # Decrement Products.stock_on_hand by same quantity
            if target_inv.product_id is not None:
                self._adjust_product_stock(db, target_inv.product_id, -quantity)
                product_type = (
                    db.query(Product.product_type)
                    .filter(Product.id == target_inv.product_id)
                    .scalar()
                )
            else:
                product_type = None

            # StockExit audit
            self._persist_stock_exit(
                db,
                inventory_id=target_inv.id,
                ticket_number=ticket_id,
                quantity=quantity,
                created_by=technician,
            )

            # InventoryMovement audit
            self._persist_movement(
                db,
                mov_id=mov_id,
                product_id_ref=str(product_id),
                action="OUT",
                quantity=quantity,
                user=technician,
                product_name=target_inv.product_name,
                reference=target_inv.article_number,
                ticket_id=ticket_id,
                assignee=technician,
                notes=notes,
                now=now,
            )

            db.commit()
            db.refresh(target_inv)

            self._debug_print(
                "stock_out",
                (
                    f"inventory_id={target_inv.id}, qty={quantity}, ticket={ticket_id}, "
                    f"technician={technician}, remaining_inv_qty={target_inv.quantity_available}, "
                    f"product_type={product_type}"
                ),
            )

            return {
                "id": mov_id,
                "product_id": product_id,
                "action": "OUT",
                "quantity": quantity,
                "user": technician,
                "ticket_id": ticket_id,
                "assignee": technician,
                "notes": notes,
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            db.rollback()
            self._debug_print("assign_error", f"Transaction rolled back: {e}")
            raise ValueError(f"Failed to assign stock: {e}")

    # ------------------------------------------------------------------
    # Legacy stock-entry router Step5 save path (disabled router)
    # ------------------------------------------------------------------
    def create_inventory_and_stock_entry(
        self,
        db: Session,
        workflow_state: WorkflowState,
        received_by: str,
        po_id: int,
    ) -> Dict[str, Any]:
        """
        Legacy 5-step workflow create path — refactored to use Product FK, respect Laptop serial uniqueness,
        never overwrite same-package-label non-Laptop rows with merges.
        """
        try:
            now = datetime.utcnow()
            self._debug_print(
                "workflow_start",
                (
                    f"workflow_id={workflow_state.workflow_id}, category={workflow_state.category}, "
                    f"brand={workflow_state.brand}, product_name={workflow_state.product_name}, "
                    f"article_number={workflow_state.article_number}, quantity={workflow_state.quantity}, po_id={po_id}"
                ),
            )

            product = self._resolve_product(db, workflow_state.category)
            cleaned_serials = self._normalize_serial_list(workflow_state.serial_numbers)
            payload_qty = (
                int(workflow_state.quantity)
                if workflow_state.quantity is not None and workflow_state.quantity > 0
                else 1
            )
            is_laptop = product.product_type == "Laptop"
            use_laptop_per_serial = (
                is_laptop
                and cleaned_serials
                and (len(cleaned_serials) > 1 or payload_qty == 1)
            )

            created_inventory_ids: List[int] = []
            created_stock_entry_ids: List[int] = []

            if use_laptop_per_serial:
                if not cleaned_serials:
                    raise ValueError(
                        "Laptop stock entry requires serial numbers; none were captured in workflow."
                    )
                for serial in cleaned_serials:
                    existing = (
                        db.query(Inventory)
                        .filter(
                            Inventory.product_id == product.id,
                            Inventory.serial_number == serial,
                        )
                        .first()
                    )
                    if existing is None:
                        inventory = Inventory(
                            purchase_order_id=po_id,
                            product_id=product.id,
                            brand=workflow_state.brand or "Generic",
                            product_name=workflow_state.product_name or workflow_state.article_number,
                            article_number=workflow_state.article_number,
                            serial_number=serial,
                            quantity_available=1,
                            status="AVAILABLE",
                            received_by=received_by,
                            received_at=now,
                        )
                        db.add(inventory)
                    else:
                        inventory = existing
                        inventory.quantity_available = (inventory.quantity_available or 0)
                        self._apply_meta(
                            inventory,
                            brand=workflow_state.brand,
                            product_name=workflow_state.product_name,
                            article_number=workflow_state.article_number,
                            serial_number=serial,
                            technician=received_by,
                            now=now,
                        )
                    db.flush()
                    self._adjust_product_stock(db, product.id, +1)
                    se = self._persist_stock_entry(db, inventory.id, 1, received_by)
                    created_inventory_ids.append(inventory.id)
                    created_stock_entry_ids.append(se.id)

                last_inv_id = created_inventory_ids[-1]
                last_se_id = created_stock_entry_ids[-1]
                last_inv = db.query(Inventory).filter(Inventory.id == last_inv_id).first()
                last_name = last_inv.product_name if last_inv else workflow_state.product_name

            else:
                if is_laptop and not cleaned_serials:
                    raise ValueError(
                        "Laptop stock entry requires serial numbers; none were captured in workflow."
                    )
                resolved_serial = (
                    ",".join(cleaned_serials) if cleaned_serials else None
                )
                inventory = Inventory(
                    purchase_order_id=po_id,
                    product_id=product.id,
                    brand=workflow_state.brand or "Generic",
                    product_name=workflow_state.product_name or workflow_state.article_number,
                    article_number=workflow_state.article_number,
                    serial_number=resolved_serial,
                    quantity_available=payload_qty,
                    status="AVAILABLE",
                    received_by=received_by,
                    received_at=now,
                )
                db.add(inventory)
                db.flush()
                self._adjust_product_stock(db, product.id, +payload_qty)
                se = self._persist_stock_entry(db, inventory.id, payload_qty, received_by)
                last_inv_id = inventory.id
                last_se_id = se.id
                last_name = inventory.product_name

            db.commit()

            verified_last = db.query(Inventory).filter(Inventory.id == last_inv_id).first()
            verified_se = db.query(StockEntry).filter(StockEntry.id == last_se_id).first()
            self._debug_print(
                "workflow_verify",
                (
                    f"inventory_exists={bool(verified_last)}, stock_entry_exists={bool(verified_se)}, "
                    f"rows_created={len(created_inventory_ids) if is_laptop else 1}"
                ),
            )

            return {
                "success": True,
                "inventory_id": last_inv_id,
                "stock_entry_id": last_se_id,
                "message": f"Successfully created inventory item and stock entry for {last_name}",
                "inventory_ids_created": created_inventory_ids,
                "stock_entry_ids_created": created_stock_entry_ids,
            }

        except Exception as e:
            db.rollback()
            self._debug_print("workflow_error", f"Transaction rolled back: {e}")
            return {
                "success": False,
                "message": f"Failed to create inventory and stock entry: {str(e)}",
            }

    # ------------------------------------------------------------------
    # Reads (unchanged contract)
    # ------------------------------------------------------------------
    def get_inventory_by_id(self, db: Session, inventory_id: int) -> Optional[Inventory]:
        """Get inventory item by ID"""
        return db.query(Inventory).filter(Inventory.id == inventory_id).first()

    def update_inventory_quantity(
        self,
        db: Session,
        inventory_id: int,
        quantity_change: int,
    ) -> Dict[str, Any]:
        """Update inventory quantity AND keep Products.stock_on_hand in sync."""
        try:
            inventory = self.get_inventory_by_id(db, inventory_id)
            if not inventory:
                return {
                    "success": False,
                    "message": f"Inventory item {inventory_id} not found",
                }

            new_quantity = inventory.quantity_available + quantity_change
            if new_quantity < 0:
                return {
                    "success": False,
                    "message": f"Cannot reduce quantity below zero. Current: {inventory.quantity_available}, Requested change: {quantity_change}",
                }

            inventory.quantity_available = new_quantity
            if inventory.product_id is not None:
                self._adjust_product_stock(db, inventory.product_id, quantity_change)
            db.commit()

            return {
                "success": True,
                "new_quantity": new_quantity,
                "message": f"Updated quantity to {new_quantity}",
            }

        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Failed to update inventory quantity: {str(e)}",
            }

    def search_inventory(
        self,
        db: Session,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Inventory]:
        """Search inventory (category reads via the hybrid_property → product.product_type transparently)."""
        query = db.query(Inventory)

        if category:
            filter_val = f"%{category}%"
            query = query.join(Product, Inventory.product_id == Product.id).filter(
                Product.product_type.ilike(filter_val)
            )

        if brand:
            query = query.filter(Inventory.brand.ilike(f"%{brand}%"))

        if status:
            query = query.filter(Inventory.status == status)

        return query.limit(limit).all()

    def get_inventory_summary(self, db: Session) -> Dict[str, Any]:
        """Inventory summary statistics (uses Products.product_type for category distribution when possible)."""
        try:
            total_items = db.query(Inventory).count()

            status_counts = {}
            statuses = db.query(Inventory.status).distinct().all()
            for (status,) in statuses:
                count = db.query(Inventory).filter(Inventory.status == status).count()
                status_counts[status] = count

            category_counts: Dict[str, int] = {}
            rows = (
                db.query(Product.product_type, Inventory.id)
                .join(Product, Inventory.product_id == Product.id)
                .all()
            )
            for product_type, _inv_id in rows:
                resolved = product_type or "Unknown"
                category_counts[resolved] = category_counts.get(resolved, 0) + 1

            from sqlalchemy import func as sa_func

            total_quantity = db.query(sa_func.sum(Inventory.quantity_available)).scalar() or 0

            return {
                "success": True,
                "total_items": total_items,
                "total_quantity": int(total_quantity),
                "status_distribution": status_counts,
                "category_distribution": category_counts,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get inventory summary: {str(e)}",
            }


# Global instance
inventory_service = InventoryService()
