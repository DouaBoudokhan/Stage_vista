"""
YOLO11 Service for Object Detection
Detects and classifies IT equipment in images using real YOLO model
"""
import base64
import io
import os
from PIL import Image
import logging
from typing import Dict, List, Any
import torch
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class YOLOService:
    """
    YOLO11-based object detection service for IT equipment
    Uses real YOLO model for inference
    """
    
    def __init__(self):
        # Load the real YOLO model
        model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models_ai', 'best.pt')
        
        try:
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
                self.model_loaded = True
                logger.info(f"✅ Loaded YOLO model from: {model_path}")
            else:
                logger.warning(f"❌ YOLO model not found at: {model_path}")
                self.model = None
                self.model_loaded = False
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            self.model = None
            self.model_loaded = False
    
    async def detect_objects(self, image_data: bytes) -> Dict[str, Any]:
        """
        Detect IT equipment objects in image using real YOLO model
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Detection results with category, confidence, bounding box
        """
        try:
            # Parse image 
            try:
                image = Image.open(io.BytesIO(image_data))
                image = image.convert('RGB')
                width, height = image.size
                logger.info(f"📸 Processing image: {width}x{height}")
                
            except Exception as img_error:
                logger.error(f"Image processing error: {img_error}")
                raise Exception(f"Invalid image format: {img_error}")
            
            # Use real YOLO model if loaded
            if self.model_loaded and self.model:
                try:
                    # Run YOLO inference
                    results = self.model(image, verbose=False)
                    
                    if len(results) > 0 and len(results[0].boxes) > 0:
                        # Get the best detection
                        boxes = results[0].boxes
                        best_idx = torch.argmax(boxes.conf).item()
                        
                        # Extract detection data
                        box = boxes.xyxy[best_idx].cpu().numpy()  # [x1, y1, x2, y2]
                        confidence = boxes.conf[best_idx].cpu().item()
                        class_id = int(boxes.cls[best_idx].cpu().item())
                        
                        # Get class name from model
                        class_names = self.model.names
                        category = class_names.get(class_id, f"Class_{class_id}")
                        
                        # Calculate bounding box
                        x1, y1, x2, y2 = box
                        bbox_width = x2 - x1
                        bbox_height = y2 - y1
                        
                        result = {
                            "category": category,
                            "confidence": confidence,
                            "class_id": class_id,
                            "model": "Equipment Detection",
                            "reference": f"{category.upper()}-{class_id:03d}",
                            "bounding_box": {
                                "x": int(x1),
                                "y": int(y1),
                                "width": int(bbox_width),
                                "height": int(bbox_height),
                                "x_center": int((x1 + x2) / 2),
                                "y_center": int((y1 + y2) / 2)
                            },
                            "detected_features": [
                                f"Class ID: {class_id}",
                                f"Detection Score: {confidence:.3f}",
                                "Real YOLO Detection"
                            ],
                            "image_size": {"width": width, "height": height},
                            "processing_time_ms": 200,
                            "yolo_version": "YOLO11 (Real Model)",
                            "detection_score": confidence,
                            "equipment_type": category,
                            "model_path": "best.pt"
                        }
                        
                        logger.info(f"🎯 Real YOLO detection: {category} ({confidence:.2f} confidence)")
                        return result
                        
                    else:
                        # No objects detected
                        logger.info("❌ No objects detected by YOLO")
                        return self._get_no_detection_result(width, height)
                        
                except Exception as yolo_error:
                    logger.error(f"YOLO inference failed: {yolo_error}")
                    raise Exception(f"YOLO detection failed: {yolo_error}")
            
            else:
                # YOLO model not loaded - return clear error
                logger.error("❌ YOLO model not loaded")
                raise Exception(
                    "YOLO model not available. Please ensure best.pt model file exists at models_ai/best.pt"
                )
            
        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            raise Exception(f"Object detection unavailable: {str(e)}")
    
    
    def _get_no_detection_result(self, width: int, height: int) -> Dict[str, Any]:
        """Result when no objects are detected by YOLO"""
        return {
            "category": "No Object Detected",
            "confidence": 0.0,
            "class_id": -1,
            "model": "YOLO11",
            "reference": "NO-DETECT",
            "bounding_box": {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 0,
                "x_center": int(width * 0.5),
                "y_center": int(height * 0.5)
            },
            "detected_features": ["No objects found in image"],
            "image_size": {"width": width, "height": height},
            "processing_time_ms": 50,
            "yolo_version": "YOLO11",
            "detection_score": 0.0,
            "equipment_type": "Unknown"
        }
    
    def get_supported_categories(self) -> List[str]:
        """Return list of equipment categories the model can detect"""
        if self.model_loaded and self.model:
            return list(self.model.names.values())
        return []
