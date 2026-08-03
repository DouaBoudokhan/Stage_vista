"""
Label Analysis Router
Accepts a shipping label image and runs Azure Computer Vision OCR server-side,
then parses the extracted text for product details.
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from app.services.ocr_parser_service import ocr_parser_service
from app.services.azure_ocr_service import azure_ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/labels", tags=["labels"])


@router.post("/analyze")
async def analyze_label(file: UploadFile = File(...)):
    """
    Analyze shipping label image.
    
    1. Receives the raw image file from the mobile client
    2. Sends it to Azure Computer Vision Read API for dynamic OCR
    3. Parses the extracted text for brand, product, article number, PO, serials, quantity, upc
    """
    try:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="Image file is required.")

        image_bytes = await file.read()
        if not image_bytes or len(image_bytes) < 100:
            raise HTTPException(status_code=400, detail="Image file is empty or too small.")

        print(f"\n==================== PACKAGE LABEL SCAN: {file.filename} ({len(image_bytes)} bytes) ====================")

        # Run Azure Computer Vision OCR on the image
        extracted_text = azure_ocr_service.extract_text_from_bytes(image_bytes)

        print("\n--- [AZURE OCR EXTRACTED TEXT FROM PACKAGE LABEL] ---")
        print(extracted_text or "[NO TEXT EXTRACTED BY AZURE OCR]")
        print("----------------------------------------------------\n")

        if not extracted_text or len(extracted_text.strip()) < 5:
            raise HTTPException(
                status_code=422,
                detail="Azure OCR could not extract text from the label image. Please retake with better lighting."
            )

        # Parse extracted text for shipping label fields
        parsed_result = ocr_parser_service.parse_shipping_label(extracted_text)

        print("--- [PARSED LABEL RESULT] ---")
        print(parsed_result)
        print("====================================================================================\n")

        parsed_result["confidence"] = 85
        parsed_result["extracted_text"] = extracted_text[:500]

        return JSONResponse(content=parsed_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Label analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Label analysis failed: {str(e)}")