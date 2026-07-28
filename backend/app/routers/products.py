"""
Product Detection Router
YOLO11-based object detection for IT equipment
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.yolo_service import YOLOService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])

yolo_service = YOLOService()

@router.post("/detect")
async def detect_product(file: UploadFile = File(...)):
    """
    Detect IT equipment in uploaded image using YOLO11
    """
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Analyze with YOLO11
        result = await yolo_service.detect_objects(image_data)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Product detection failed: {e}")
        raise HTTPException(status_code=500, detail="Product detection failed")

@router.get("/debug/model-status")
async def get_model_status():
    """
    Debug endpoint to check YOLO model loading status
    """
    yolo_service = YOLOService()
    
    return {
        "model_loaded": yolo_service.model_loaded,
        "model_available": yolo_service.model is not None,
        "supported_categories": yolo_service.get_supported_categories(),
        "model_path": os.path.join(os.path.dirname(__file__), '..', '..', 'models_ai', 'best.pt')
    }

@router.get("/categories")
async def get_categories():
    """
    Get available equipment categories
    """
    return {
        "categories": [
            "Laptop",
            "Monitor", 
            "Mouse",
            "Keyboard",
            "Headset",
            "Networking",
            "Server",
            "Tablet",
            "Phone",
            "Accessories"
        ]
    }