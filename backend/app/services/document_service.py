"""Document Service - Orchestrates Invoice Analysis Workflow (Azure Computer Vision OCR)"""
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from ..models.document import Document
from ..models.purchase_order import PurchaseOrder
from .ocr_parser_service import ocr_parser_service
from .azure_ocr_service import azure_ocr_service
from .llm_service import get_llm_service
from .storage_service import storage_service


class DocumentService:
    """
    Service that orchestrates the complete Invoice Analysis workflow.
    Uses Azure Computer Vision Read API for dynamic server-side OCR on uploaded document images.
    """
    
    def _normalize_serial_numbers(self, serial_numbers: List[str]) -> List[str]:
        """Deduplicate serial numbers preserving original order."""
        normalized: List[str] = []
        for serial in serial_numbers:
            cleaned = str(serial).strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized
    
    async def analyze_invoice(
        self, 
        db: Session,
        image_file: UploadFile,
        ocr_text: str = "",
        document_type: str = "invoice"
    ) -> Dict[str, Any]:
        """
        Complete invoice analysis workflow.
        Performs dynamic Azure OCR on uploaded document image.
        """
        try:
            # 1. Save uploaded image
            save_result = await storage_service.save_document_image(image_file)
            if not save_result[0]:
                return {
                    "success": False,
                    "error": f"Image save failed: {save_result[1]}",
                    "step": "image_storage"
                }
            
            image_path = save_result[1]
            original_filename = save_result[2]
            full_path = storage_service.get_full_path(image_path)
            
            # Read image bytes
            image_bytes = b""
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    image_bytes = f.read()

            # 2. Dynamic Azure OCR on uploaded image
            final_ocr_text = (ocr_text or "").strip()
            ocr_source = "azure_computer_vision"

            if not final_ocr_text or len(final_ocr_text) < 15:
                print("🔍 Running dynamic Azure Computer Vision OCR on uploaded document image...")
                extracted = azure_ocr_service.extract_text_from_bytes(image_bytes)
                if extracted and len(extracted.strip()) > 5:
                    final_ocr_text = extracted.strip()
                else:
                    final_ocr_text = final_ocr_text or "No OCR text extracted"

            ocr_metadata = {'source': ocr_source}
            
            # 3. Parse OCR text deterministically
            try:
                parsed_invoice = ocr_parser_service.parse_invoice(final_ocr_text)
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"OCR succeeded but parsing failed: {str(e)}",
                    "step": "ocr_parsing",
                    "extracted_text": final_ocr_text[:500]
                }
            
            # 4. Create document record
            document = self._create_document(
                db=db,
                document_type=document_type,
                document_number=parsed_invoice.invoice_number,
                supplier=parsed_invoice.supplier,
                image_path=image_path,
                extracted_text=final_ocr_text
            )
            
            # 5. Process each Purchase Order (cache lookup + LLM if needed)
            processed_pos = []
            for parsed_po in parsed_invoice.purchase_orders:
                po_result = await self._process_purchase_order(
                    db=db,
                    document_id=document.id,
                    po_number=parsed_po.po_number,
                    po_text=parsed_po.text,
                    serial_numbers=parsed_po.serial_numbers,
                    full_ocr_text=final_ocr_text
                )
                processed_pos.append(po_result)
            
            return {
                "success": True,
                "document": {
                    "id": document.id,
                    "supplier": parsed_invoice.supplier,
                    "invoice_number": parsed_invoice.invoice_number,
                    "document_type": document_type,
                    "image_path": image_path,
                    "original_filename": original_filename
                },
                "purchase_orders": processed_pos,
                "extracted_text": final_ocr_text,
                "ocr_metadata": ocr_metadata,
                "statistics": {
                    "total_pos": len(processed_pos),
                    "cached_descriptions": sum(1 for po in processed_pos if po["cached"]),
                    "new_descriptions": sum(1 for po in processed_pos if not po["cached"]),
                    "total_serial_numbers": sum(len(po["serial_numbers"]) for po in processed_pos)
                }
            }
            
        except Exception as e:
            if 'image_path' in locals():
                await storage_service.delete_file(image_path)
            
            return {
                "success": False,
                "error": f"Invoice analysis failed: {str(e)}",
                "step": "workflow_orchestration"
            }
    
    def _create_document(
        self,
        db: Session,
        document_type: str,
        document_number: str,
        supplier: str,
        image_path: str,
        extracted_text: str
    ) -> Document:
        """Create document record in database"""
        safe_supplier = (supplier or "Unknown Supplier").strip().split('\n')[0][:250]
        safe_doc_num = (document_number or "INV-0000").strip().split('\n')[0][:250]

        existing_document = db.query(Document).filter(
            Document.document_type == document_type[:95],
            Document.document_number == safe_doc_num
        ).first()

        if existing_document:
            return existing_document

        document = Document(
            document_type=document_type[:95],
            document_number=safe_doc_num,
            supplier=safe_supplier,
            image_path=image_path[:490],
            extracted_text=extracted_text
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    
    async def _process_purchase_order(
        self,
        db: Session,
        document_id: int,
        po_number: str,
        po_text: str,
        serial_numbers: List[str],
        full_ocr_text: str = ""
    ) -> Dict[str, Any]:
        """Process single Purchase Order with cache lookup and LLM generation"""
        normalized_serials = self._normalize_serial_numbers(serial_numbers)

        existing_po = self._get_cached_po_description(db, po_number)
        
        if existing_po and existing_po.description and not existing_po.description.startswith("Equipment for PO "):
            description = existing_po.description
            cached = True
            llm_used = False
        else:
            context_text = po_text.strip()
            if full_ocr_text and len(full_ocr_text) > len(context_text):
                context_text = f"PO SECTION:\n{po_text}\n\nFULL INVOICE OCR TEXT:\n{full_ocr_text}"
                
            llm_service = get_llm_service()
            llm_result = await llm_service.generate_description(po_number, context_text)
            
            if llm_result["success"] and llm_result.get("description"):
                description = llm_result["description"]
                llm_used = True
            else:
                description = f"Equipment for PO {po_number}"
                llm_used = False
            
            cached = False
        
        po_record = self._create_or_update_po(
            db=db,
            document_id=document_id,
            po_number=po_number,
            description=description,
            serial_numbers=normalized_serials
        )
        
        return {
            "id": po_record.id,
            "po_number": po_number,
            "description": description,
            "serial_numbers": normalized_serials,
            "cached": cached,
            "llm_used": llm_used,
            "text_length": len(po_text)
        }
    
    def _get_cached_po_description(self, db: Session, po_number: str) -> Optional[PurchaseOrder]:
        """Look up existing PO description in cache"""
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == po_number,
            PurchaseOrder.description.isnot(None)
        ).first()
        
        if po and po.description and not po.description.startswith("Equipment for PO "):
            return po
        return None
    
    def _create_or_update_po(
        self,
        db: Session,
        document_id: int,
        po_number: str,
        description: str,
        serial_numbers: List[str]
    ) -> PurchaseOrder:
        """Create new PO record or update existing one in database"""
        serialized_serials = ",".join(self._normalize_serial_numbers(serial_numbers))
        existing_po = db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == po_number
        ).first()
        
        if existing_po:
            changed = False
            if not existing_po.description or existing_po.description.startswith("Equipment for PO ") or not description.startswith("Equipment for PO "):
                existing_po.description = description
                changed = True
            if serialized_serials:
                existing_po.serial_numbers = serialized_serials
                changed = True
            if changed:
                db.commit()
            db.refresh(existing_po)
            return existing_po
        else:
            new_po = PurchaseOrder(
                document_id=document_id,
                po_number=po_number,
                description=description,
                serial_numbers=serialized_serials
            )
            db.add(new_po)
            db.commit()
            db.refresh(new_po)
            return new_po
    
    def get_document_by_id(self, db: Session, document_id: int) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents_by_supplier(self, db: Session, supplier: str, limit: int = 50) -> List[Document]:
        return db.query(Document).filter(
            Document.supplier.ilike(f"%{supplier}%")
        ).order_by(Document.created_at.desc()).limit(limit).all()
    
    def get_po_by_number(self, db: Session, po_number: str) -> Optional[PurchaseOrder]:
        return db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == po_number
        ).first()
    
    def get_recent_documents(self, db: Session, limit: int = 20) -> List[Document]:
        return db.query(Document).order_by(
            Document.created_at.desc()
        ).limit(limit).all()
    
    def get_cache_statistics(self, db: Session) -> Dict[str, Any]:
        total_pos = db.query(PurchaseOrder).count()
        cached_pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.description.isnot(None)
        ).count()
        
        return {
            "total_purchase_orders": total_pos,
            "cached_descriptions": cached_pos,
            "cache_hit_rate": cached_pos / total_pos if total_pos > 0 else 0,
            "cache_miss_count": total_pos - cached_pos
        }


# Global instance
document_service = DocumentService()
