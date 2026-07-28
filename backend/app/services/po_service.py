"""Purchase Order Service for Stock Entry Workflow"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.purchase_order import PurchaseOrder
from ..models.document import Document
from ..schemas.stock_entry import PurchaseOrderInfo


class PurchaseOrderService:
    """Service for managing Purchase Orders in Stock Entry workflow"""
    
    def __init__(self):
        pass

    def _serialize_serial_numbers(self, serial_numbers: List[str]) -> str:
        """Store PO serial numbers as a comma-separated string."""
        unique_serials: List[str] = []
        for serial in serial_numbers:
            cleaned = serial.strip()
            if cleaned and cleaned not in unique_serials:
                unique_serials.append(cleaned)
        return ",".join(unique_serials)
    
    def create_document_and_pos(
        self, 
        db: Session,
        supplier: str,
        document_number: str,
        extracted_text: str,
        purchase_orders: List[PurchaseOrderInfo]
    ) -> Dict[str, Any]:
        """
        Create document and associated Purchase Orders
        
        Args:
            db: Database session
            supplier: Supplier name
            document_number: Document identifier
            extracted_text: Full OCR text for auditing
            purchase_orders: List of extracted PO information
            
        Returns:
            Dictionary with created document and PO IDs
        """
        try:
            # Create document record
            document = Document(
                document_type="delivery_document",
                document_number=document_number,
                supplier=supplier,
                image_path="",  # Will be set when image is stored
                extracted_text=extracted_text
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Create Purchase Order records
            created_pos = []
            for po_info in purchase_orders:
                po = PurchaseOrder(
                    document_id=document.id,
                    po_number=po_info.po_number,
                    description=po_info.description,
                    serial_numbers=self._serialize_serial_numbers(po_info.serial_numbers)
                )
                
                db.add(po)
                created_pos.append(po)
            
            db.commit()
            
            # Refresh all POs to get their IDs
            for po in created_pos:
                db.refresh(po)
            
            return {
                "success": True,
                "document_id": document.id,
                "purchase_order_ids": [po.id for po in created_pos],
                "message": f"Created document and {len(created_pos)} Purchase Orders"
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Failed to create document and Purchase Orders: {str(e)}"
            }
    
    def get_purchase_order_by_number(self, db: Session, po_number: str) -> Optional[PurchaseOrder]:
        """Get Purchase Order by number"""
        return db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == po_number
        ).first()
    
    def validate_po_selection(
        self, 
        db: Session,
        selected_po_number: str,
        available_pos: List[PurchaseOrderInfo]
    ) -> Dict[str, Any]:
        """
        Validate technician's PO selection
        
        Args:
            db: Database session
            selected_po_number: PO number selected by technician
            available_pos: List of available PO options
            
        Returns:
            Validation result
        """
        # Check if selected PO is in the available list
        selected_po_info = None
        for po_info in available_pos:
            if po_info.po_number == selected_po_number:
                selected_po_info = po_info
                break
        
        if not selected_po_info:
            return {
                "success": False,
                "message": f"Selected PO {selected_po_number} not found in available options"
            }
        
        # Check if PO exists in database
        po_record = self.get_purchase_order_by_number(db, selected_po_number)
        if not po_record:
            return {
                "success": False,
                "message": f"Purchase Order {selected_po_number} not found in database"
            }
        
        return {
            "success": True,
            "po_id": po_record.id,
            "po_info": selected_po_info,
            "message": f"Purchase Order {selected_po_number} validated successfully"
        }
    
    def check_po_mismatch(
        self, 
        selected_po_number: str, 
        package_po_number: Optional[str]
    ) -> Optional[str]:
        """
        Check for PO mismatch between selected and package
        
        Returns:
            Warning message if mismatch detected, None otherwise
        """
        if not package_po_number:
            return None
        
        if selected_po_number != package_po_number:
            return (
                f"PO mismatch detected: Selected PO {selected_po_number} "
                f"differs from package PO {package_po_number}"
            )
        
        return None


# Global instance
po_service = PurchaseOrderService()
