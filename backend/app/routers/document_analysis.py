"""Document Analysis Router - Invoice Analysis API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.document_analysis import (
    InvoiceAnalysisResponse, ErrorResponse, DocumentListResponse,
    PurchaseOrderCacheResponse, CacheStatisticsResponse,
    ParsedInvoiceResponse, LLMGenerationRequest, LLMGenerationResponse
)
from ..services.document_service import document_service
from ..services.ocr_parser_service import ocr_parser_service
from ..services.llm_service import get_llm_service

router = APIRouter(prefix="/documents", tags=["Document Analysis"])


@router.post("/analyze")
async def analyze_invoice(
    file: UploadFile = File(...),
    ocr_text: str = Form(default=""),
    document_type: str = Form(default="invoice"),
    db: Session = Depends(get_db)
):
    """
    Analyze invoice/delivery document using complete AI workflow.
    
    This endpoint:
    1. Saves the uploaded image
    2. Parses OCR text deterministically (no AI)
    3. Checks database cache for existing PO descriptions
    4. Calls Azure AI Foundry LLM for missing descriptions
    5. Saves all data to database
    6. Returns structured analysis results
    """
    try:
        print(f"🔍 Received file: {file.filename if file else 'None'}")
        print(f"📝 OCR text length: {len(ocr_text)}")
        print(f"📄 Document type: {document_type}")
        
        # Validate inputs
        # Note: ocr_text should come from Google ML Kit on-device recognition
        # If empty, the document service will return an appropriate error
        
        if not file or not file.filename:
            print("❌ No file received!")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file is required"
            )
        
        print("📤 Calling document_service.analyze_invoice...")
        
        # Run complete analysis workflow
        result = await document_service.analyze_invoice(
            db=db,
            image_file=file,
            ocr_text=ocr_text,
            document_type=document_type
        )
        
        print(f"✅ Document service result: success={result.get('success')}")
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            error_step = result.get("step", "unknown")
            print(f"❌ Document service error at step '{error_step}': {error_msg}")
            
            # Return structured error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": error_msg,
                    "step": error_step,
                    "success": False
                }
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in analyze_invoice: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/parse-ocr", response_model=ParsedInvoiceResponse)
async def parse_ocr_text(
    ocr_text: str = Form(..., description="Raw OCR text to parse")
):
    """
    Parse OCR text deterministically (no AI/LLM involved).
    
    This endpoint demonstrates the deterministic parsing step
    without involving the LLM or database operations.
    """
    try:
        if not ocr_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OCR text cannot be empty"
            )
        
        # Parse using deterministic service
        parsed_invoice = ocr_parser_service.parse_invoice(ocr_text)
        
        # Validate extraction quality
        validation = ocr_parser_service.validate_extraction(parsed_invoice)
        
        # Build response
        return ParsedInvoiceResponse(
            supplier=parsed_invoice.supplier,
            invoice_number=parsed_invoice.invoice_number,
            purchase_orders=[
                {
                    "po_number": po.po_number,
                    "text": po.text,
                    "serial_numbers": po.serial_numbers
                }
                for po in parsed_invoice.purchase_orders
            ],
            validation=validation
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OCR parsing failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parsing error: {str(e)}"
        )


@router.post("/generate-description", response_model=LLMGenerationResponse)
async def generate_po_description(request: LLMGenerationRequest):
    """
    Generate description for Purchase Order using LLM.
    
    This endpoint demonstrates the LLM generation step
    without involving database operations.
    """
    try:
        if not request.po_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PO text cannot be empty"
            )
        
        # Generate description using LLM
        llm_service = get_llm_service()
        result = await llm_service.generate_description(
            po_number=request.po_number,
            po_text=request.po_text
        )
        
        return LLMGenerationResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation error: {str(e)}"
        )


@router.get("/list", response_model=List[DocumentListResponse])
async def list_documents(
    limit: int = 20,
    supplier: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List recent documents with optional supplier filter.
    """
    try:
        if supplier:
            documents = document_service.get_documents_by_supplier(db, supplier, limit)
        else:
            documents = document_service.get_recent_documents(db, limit)
        
        return [
            DocumentListResponse(
                id=doc.id,
                document_type=doc.document_type,
                document_number=doc.document_number,
                supplier=doc.supplier,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@router.get("/purchase-orders", response_model=List[PurchaseOrderCacheResponse])
async def list_purchase_orders(
    limit: int = 50,
    has_description: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List Purchase Orders with cache status.
    """
    try:
        from ..models.purchase_order import PurchaseOrder
        
        query = db.query(PurchaseOrder)
        
        if has_description is not None:
            if has_description:
                query = query.filter(PurchaseOrder.description.isnot(None))
            else:
                query = query.filter(PurchaseOrder.description.is_(None))
        
        pos = query.order_by(PurchaseOrder.created_at.desc()).limit(limit).all()
        
        return [
            PurchaseOrderCacheResponse(
                id=po.id,
                po_number=po.po_number,
                description=po.description,
                created_at=po.created_at,
                updated_at=po.updated_at,
                has_description=po.description is not None
            )
            for po in pos
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing Purchase Orders: {str(e)}"
        )


@router.get("/cache-stats", response_model=CacheStatisticsResponse)
async def get_cache_statistics(db: Session = Depends(get_db)):
    """
    Get LLM cache statistics.
    
    Shows how many PO descriptions are cached vs need generation.
    """
    try:
        stats = document_service.get_cache_statistics(db)
        return CacheStatisticsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cache statistics: {str(e)}"
        )


@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get specific document by ID with full details.
    """
    try:
        document = document_service.get_document_by_id(db, document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get associated Purchase Orders
        from ..models.purchase_order import PurchaseOrder
        pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.document_id == document_id
        ).all()
        
        return {
            "document": {
                "id": document.id,
                "document_type": document.document_type,
                "document_number": document.document_number,
                "supplier": document.supplier,
                "image_path": document.image_path,
                "created_at": document.created_at,
                "updated_at": document.updated_at
            },
            "purchase_orders": [
                {
                    "id": po.id,
                    "po_number": po.po_number,
                    "description": po.description,
                    "has_description": po.description is not None,
                    "created_at": po.created_at,
                    "updated_at": po.updated_at
                }
                for po in pos
            ],
            "extracted_text": document.extracted_text  # Full OCR text for reference
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )