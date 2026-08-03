"""AI Detection Router - YOLO Product Detection"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from ..dependencies import get_current_user
from ..models.user import User
from ..services.yolo_service import yolo_service

router = APIRouter(prefix="", tags=["ai-detection"])


class DetectionRequest(BaseModel):
    """Request schema for object detection"""
    image: str  # Base64 encoded image
    mode: str = "product"  # product, invoice, etc.


@router.post("/detect")
async def detect_object(
    request: DetectionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Detect IT equipment products in image using YOLO
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
