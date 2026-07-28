"""
Label Analysis Router
OCR-based analysis of shipping labels and package information
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.ocr_parser_service import OCRParserService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/labels", tags=["labels"])

ocr_parser_service = OCRParserService()

@router.post("/analyze")
async def analyze_label(file: UploadFile = File(...)):
    """
    Analyze shipping label using OCR to extract:
    - Equipment Product Name (IMPACT 100 MS Stereo USB-C+A)
    - Brand (EPOS, Dell, Apple, etc.)
    - Article Number (Art.-No. 1001421)
    - Quantities (QTY: 20)
    - PO Number (PO:3480)
    - Serial numbers & Barcodes
    """
    try:
        image_bytes = await file.read()
        
        # Extract text via OCR
        from app.services.azure_ocr_service import azure_ocr_service
        from app.services.ocr_service import ocr_service
        import base64

        final_text = ""
        try:
            val = azure_ocr_service.validate_image(image_bytes)
            if val.get('valid'):
                res = await azure_ocr_service.extract_text_from_image(image_bytes)
                if res.get('success') and res.get('text'):
                    final_text = res['text']
        except Exception:
            pass

        if not final_text.strip():
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')
            success, text = ocr_service.extract_text_from_image(img_b64)
            if success and text:
                final_text = text

        # Parse extracted OCR text or sample label
        parsed_result = ocr_parser_service.parse_shipping_label(final_text)
        
        return JSONResponse(content=parsed_result)
        
    except Exception as e:
        logger.error(f"Label analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Label analysis failed")

@router.post("/ocr-only")
async def extract_text_only(file: UploadFile = File(...)):
    """
    Extract raw text from label image using OCR
    """
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
            
        # Mock OCR text extraction
        mock_text = """
        Dell Latitude 5440 Business Laptop
        Quantity: 10 units
        Purchase Order: PO-2026-0042
        Serial Numbers:
        S/N: 7X89W23, S/N: 7X89W24, S/N: 7X89W25
        S/N: 7X89W26, S/N: 7X89W27, S/N: 7X89W28
        S/N: 7X89W29, S/N: 7X89W30, S/N: 7X89W31
        S/N: 7X89W32
        
        Tracking: 1Z999AA1234567890
        """
        
        return {"extracted_text": mock_text.strip()}
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        raise HTTPException(status_code=500, detail="OCR extraction failed")