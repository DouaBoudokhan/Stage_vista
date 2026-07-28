"""Inventory Service for Stock Entry Workflow"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.inventory import Inventory
from ..models.purchase_order import PurchaseOrder
from ..models.stock_entry import StockEntry
from ..schemas.stock_entry import WorkflowState


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
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record stock-in movement"""
        import uuid
        mov_id = f"MOV-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.utcnow()

        self._debug_print("start", f"product_ref={product_ref}, quantity={quantity}, technician={technician}, po_id={po_id}")
        
        try:
            inv = db.query(Inventory).filter(Inventory.article_number == product_ref).first()
            if inv:
                self._debug_print("inventory_lookup", f"Existing inventory found id={inv.id}, current_quantity={inv.quantity_available}")
                inv.quantity_available += quantity
                if category and inv.category in {"Equipment", "", None}:
                    inv.category = category
                if brand and inv.brand in {"Generic", "", None}:
                    inv.brand = brand
                if product_name and inv.product_name in {product_ref, "", None}:
                    inv.product_name = product_name
                if article_number and inv.article_number in {product_ref, "", None}:
                    inv.article_number = article_number
                if serial_numbers:
                    inv.serial_number = ",".join(serial_numbers)
                self._debug_print("inventory_update", f"New quantity will be {inv.quantity_available}")
            else:
                resolved_po_id = self._resolve_purchase_order_id(db, po_id)
                self._debug_print("po_resolve", f"Resolved purchase_order_id={resolved_po_id}")

                resolved_category = category or "Equipment"
                resolved_brand = brand or "Generic"
                resolved_product_name = product_name or product_ref
                resolved_article_number = article_number or product_ref
                resolved_serial_number = ",".join(serial_numbers) if serial_numbers else None

                inv = Inventory(
                    purchase_order_id=resolved_po_id,
                    category=resolved_category,
                    brand=resolved_brand,
                    product_name=resolved_product_name,
                    article_number=resolved_article_number,
                    quantity_available=quantity,
                    status="AVAILABLE",
                    received_by=technician,
                    received_at=now
                )
                inv.serial_number = resolved_serial_number
                db.add(inv)
                self._debug_print(
                    "inventory_create",
                    (
                        f"Prepared new inventory row category={inv.category}, brand={inv.brand}, "
                        f"product_name={inv.product_name}, article_number={inv.article_number}, "
                        f"serial_number={inv.serial_number}, quantity={inv.quantity_available}"
                    )
                )

            db.flush()
            self._debug_print("flush", f"Pending inventory id={getattr(inv, 'id', None)}")
            self._debug_print("before_commit", f"inventory_payload={self._inventory_snapshot(inv)}")
            db.commit()
            db.refresh(inv)
            self._debug_print(
                "commit",
                f"saved_inventory={self._inventory_snapshot(inv)}"
            )
        except Exception as e:
            db.rollback()
            self._debug_print("error", f"Transaction rolled back: {e}")
            raise ValueError(f"Failed to receive stock: {e}")

        persisted = db.query(Inventory).filter(Inventory.id == inv.id).first()
        if persisted:
            self._debug_print(
                "verify",
                f"verified_inventory={self._inventory_snapshot(persisted)}"
            )
        else:
            self._debug_print("verify", f"No row found after commit for inventory id={inv.id}")
            
        return {
            "id": mov_id,
            "product_id": product_ref,
            "action": "IN",
            "quantity": quantity,
            "user": technician,
            "product_name": product_ref,
            "po_id": po_id or "PO-2026-0042",
            "reference": product_ref,
            "notes": notes,
            "timestamp": now.isoformat()
        }

    def _resolve_purchase_order_id(self, db: Session, po_id: Optional[str]) -> int:
        """Resolve the database PurchaseOrder primary key from a PO id or PO number."""
        if po_id is None or str(po_id).strip() == "":
            raise ValueError("Purchase order is required to receive new stock")

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

        raise ValueError(f"Purchase order '{po_value}' not found")

    def assign_stock(
        self,
        db: Session,
        product_id: str,
        quantity: int,
        ticket_id: str,
        technician: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record stock-out assignment movement"""
        import uuid
        mov_id = f"MOV-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.utcnow()
        
        return {
            "id": mov_id,
            "product_id": product_id,
            "action": "OUT",
            "quantity": quantity,
            "user": technician,
            "ticket_id": ticket_id,
            "assignee": technician,
            "notes": notes,
            "timestamp": now.isoformat()
        }
    
    def create_inventory_and_stock_entry(
        self,
        db: Session,
        workflow_state: WorkflowState,
        received_by: str,
        po_id: int
    ) -> Dict[str, Any]:
        """
        Create inventory item and stock entry record (Step 5)
        
        Args:
            db: Database session
            workflow_state: Complete workflow state
            received_by: Technician who received the items
            po_id: Purchase Order ID
            
        Returns:
            Result dictionary with created record IDs
        """
        try:
            self._debug_print(
                "workflow_start",
                (
                    f"workflow_id={workflow_state.workflow_id}, category={workflow_state.category}, "
                    f"brand={workflow_state.brand}, product_name={workflow_state.product_name}, "
                    f"article_number={workflow_state.article_number}, quantity={workflow_state.quantity}, po_id={po_id}"
                )
            )

            # Create inventory record
            inventory = Inventory(
                purchase_order_id=po_id,
                category=workflow_state.category,
                brand=workflow_state.brand,
                product_name=workflow_state.product_name,
                article_number=workflow_state.article_number,
                serial_number=','.join(workflow_state.serial_numbers) if workflow_state.serial_numbers else None,
                quantity_available=workflow_state.quantity,
                status="AVAILABLE",
                received_by=received_by,
                received_at=datetime.utcnow()
            )
            
            db.add(inventory)
            db.flush()
            self._debug_print("workflow_inventory_flush", f"Pending inventory id={getattr(inventory, 'id', None)}")
            self._debug_print("workflow_inventory_before_commit", f"inventory_payload={self._inventory_snapshot(inventory)}")
            db.commit()
            db.refresh(inventory)
            self._debug_print(
                "workflow_inventory_commit",
                f"saved_inventory={self._inventory_snapshot(inventory)}"
            )
            
            # Create stock entry record
            stock_entry = StockEntry(
                inventory_id=inventory.id,
                quantity_received=workflow_state.quantity,
                created_by=received_by
            )
            
            db.add(stock_entry)
            db.flush()
            self._debug_print("workflow_stock_entry_flush", f"Pending stock_entry id={getattr(stock_entry, 'id', None)}")
            self._debug_print("workflow_stock_entry_before_commit", f"stock_entry_payload={self._stock_entry_snapshot(stock_entry)}")
            db.commit()
            db.refresh(stock_entry)
            self._debug_print(
                "workflow_stock_entry_commit",
                f"saved_stock_entry={self._stock_entry_snapshot(stock_entry)}"
            )

            verified_inventory = db.query(Inventory).filter(Inventory.id == inventory.id).first()
            verified_stock_entry = db.query(StockEntry).filter(StockEntry.id == stock_entry.id).first()
            self._debug_print(
                "workflow_verify",
                (
                    f"inventory_exists={bool(verified_inventory)}, stock_entry_exists={bool(verified_stock_entry)}"
                )
            )
            
            return {
                "success": True,
                "inventory_id": inventory.id,
                "stock_entry_id": stock_entry.id,
                "message": f"Successfully created inventory item and stock entry for {inventory.product_name}"
            }
            
        except Exception as e:
            db.rollback()
            self._debug_print("workflow_error", f"Transaction rolled back: {e}")
            return {
                "success": False,
                "message": f"Failed to create inventory and stock entry: {str(e)}"
            }
    
    def get_inventory_by_id(self, db: Session, inventory_id: int) -> Optional[Inventory]:
        """Get inventory item by ID"""
        return db.query(Inventory).filter(Inventory.id == inventory_id).first()
    
    def update_inventory_quantity(
        self, 
        db: Session, 
        inventory_id: int, 
        quantity_change: int
    ) -> Dict[str, Any]:
        """
        Update inventory quantity
        
        Args:
            db: Database session
            inventory_id: Inventory item ID
            quantity_change: Change in quantity (positive for additions, negative for subtractions)
            
        Returns:
            Update result
        """
        try:
            inventory = self.get_inventory_by_id(db, inventory_id)
            if not inventory:
                return {
                    "success": False,
                    "message": f"Inventory item {inventory_id} not found"
                }
            
            new_quantity = inventory.quantity_available + quantity_change
            
            if new_quantity < 0:
                return {
                    "success": False,
                    "message": f"Cannot reduce quantity below zero. Current: {inventory.quantity_available}, Requested change: {quantity_change}"
                }
            
            inventory.quantity_available = new_quantity
            db.commit()
            
            return {
                "success": True,
                "new_quantity": new_quantity,
                "message": f"Updated quantity to {new_quantity}"
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Failed to update inventory quantity: {str(e)}"
            }
    
    def search_inventory(
        self,
        db: Session,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Inventory]:
        """
        Search inventory items with filters
        
        Args:
            db: Database session
            category: Filter by category
            brand: Filter by brand
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of matching inventory items
        """
        query = db.query(Inventory)
        
        if category:
            query = query.filter(Inventory.category.ilike(f"%{category}%"))
        
        if brand:
            query = query.filter(Inventory.brand.ilike(f"%{brand}%"))
        
        if status:
            query = query.filter(Inventory.status == status)
        
        return query.limit(limit).all()
    
    def get_inventory_summary(self, db: Session) -> Dict[str, Any]:
        """
        Get inventory summary statistics
        
        Returns:
            Summary statistics
        """
        try:
            total_items = db.query(Inventory).count()
            
            # Count by status
            status_counts = {}
            statuses = db.query(Inventory.status).distinct().all()
            for (status,) in statuses:
                count = db.query(Inventory).filter(Inventory.status == status).count()
                status_counts[status] = count
            
            # Count by category
            category_counts = {}
            categories = db.query(Inventory.category).distinct().all()
            for (category,) in categories:
                count = db.query(Inventory).filter(Inventory.category == category).count()
                category_counts[category] = count
            
            # Total quantity
            total_quantity = db.query(db.func.sum(Inventory.quantity_available)).scalar() or 0
            
            return {
                "success": True,
                "total_items": total_items,
                "total_quantity": int(total_quantity),
                "status_distribution": status_counts,
                "category_distribution": category_counts
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get inventory summary: {str(e)}"
            }


# Global instance
inventory_service = InventoryService()