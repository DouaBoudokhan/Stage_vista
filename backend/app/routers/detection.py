"""AI Detection Router - YOLO and OCR"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from ..dependencies import get_current_user
from ..models.user import User
from ..services.yolo_service import yolo_service
from ..services.ocr_service import ocr_service

router = APIRouter(prefix="", tags=["ai-detection"])


class DetectionRequest(BaseModel):
    """Request schema for object detection"""
    image: str  # Base64 encoded image
    mode: str = "product"  # product, invoice, etc.


class OCRRequest(BaseModel):
    """Request schema for OCR"""
    image: str  # Base64 encoded image
    mode: str = "invoice"


@router.post("/detect")
async def detect_object(
    request: DetectionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Detect objects in image using YOLO
    
    Modes:
    - product: Detect IT equipment products
    """
    
    try:
        if request.mode == "product":
            result = yolo_service.detect_product(request.image)
        else:
            result = yolo_service.detect_from_base64(request.image)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection failed: {str(e)}"
        )


@router.post("/ocr")
async def ocr_image(
    request: OCRRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Extract text from image using OCR
    
    Modes:
    - invoice: Extract invoice data
    - general: Extract all text
    """
    
    try:
        if request.mode == "invoice":
            result = ocr_service.analyze_invoice(request.image)
        else:
            text = ocr_service.extract_text_from_base64(request.image)
            result = {
                "success": True,
                "text": text
            }
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR failed: {str(e)}"
        )


@router.post("/invoice-analysis")
async def analyze_invoice(
    request: OCRRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze invoice image and extract structured data
    """
    
    try:
        result = ocr_service.analyze_invoice(request.image)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invoice analysis failed: {str(e)}"
        )


@router.post("/recommend-ticket")
async def recommend_ticket(
    product_ref: str,
    category: str,
    brand: str,
    current_user: User = Depends(get_current_user)
):
    """
    AI recommendation for which ticket to assign product to
    (Placeholder for future LLM integration)
    """
    
    # Placeholder - can be enhanced with LLM later
    return {
        "success": True,
        "recommendation": {
            "ticket_id": None,
            "confidence": 0.0,
            "reasoning": "LLM integration pending"
        }
    }
