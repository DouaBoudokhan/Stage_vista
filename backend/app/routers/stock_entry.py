"""Stock Entry Workflow Router"""
import base64
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.stock_entry import (
    ProductDetectionRequest, ProductDetectionResponse,
    DocumentOCRRequest, DocumentOCRResponse,
    PurchaseOrderSelection, PackageLabelRequest, PackageLabelResponse,
    StockEntrySaveRequest, StockEntryCompleteResponse,
    WorkflowStatusResponse, PurchaseOrderInfo
)
from ..services.yolo_service import YOLOService
from ..services.ocr_parser_service import ocr_parser_service
from ..services.azure_ocr_service import azure_ocr_service
from ..services.po_service import po_service
from ..services.inventory_service import inventory_service
from ..services.workflow_manager import workflow_manager

router = APIRouter(prefix="/stock-entry", tags=["Stock Entry Workflow"])


@router.post("/start", response_model=dict)
async def start_workflow():
    """
    Start a new Stock Entry workflow session
    """
    workflow_id = workflow_manager.create_workflow()
    
    return {
        "workflow_id": workflow_id,
        "step": 1,
        "next_action": "scan_product",
        "message": "Stock Entry workflow started. Please scan the product."
    }


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """
    Get current workflow status
    """
    status_info = workflow_manager.get_workflow_status(workflow_id)
    
    if not status_info["exists"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or expired"
        )
    
    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        current_step=status_info["current_step"],
        status=status_info["status"],
        next_action=status_info["next_action"],
        warnings=status_info["warnings"]
    )


@router.post("/step1/detect-product", response_model=ProductDetectionResponse)
async def detect_product(request: ProductDetectionRequest):
    """
    Step 1: Detect product using YOLO model
    """
    yolo_service = YOLOService()
    result = await yolo_service.detect_objects(request.image_data)
    
    return ProductDetectionResponse(
        category=result["category"],
        confidence=result["confidence"],
        success=True,
        message="Product detected successfully"
    )


@router.post("/step1/confirm/{workflow_id}")
async def confirm_product_detection(workflow_id: str, detection: ProductDetectionResponse):
    """
    Confirm Step 1 and update workflow state
    """
    workflow = workflow_manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    if workflow.step != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected step 1, currently at step {workflow.step}"
        )
    
    success = workflow_manager.update_workflow_step1(
        workflow_id, detection.category, detection.confidence
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update workflow"
        )
    
    return {
        "message": f"Product detection confirmed: {detection.category}",
        "next_step": 2,
        "next_action": "scan_document"
    }


@router.post("/step2/scan-document", response_model=DocumentOCRResponse)
async def scan_delivery_document(request: DocumentOCRRequest, db: Session = Depends(get_db)):
    """
    Step 2: Parse delivery document OCR text
    """
    ocr_text = (request.ocr_text or "").strip()
    
    # If client passed base64 image data instead of text, run Azure OCR dynamically
    if (not ocr_text or len(ocr_text) < 10) and request.image_data:
        try:
            raw_b64 = request.image_data
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(raw_b64)
            extracted = azure_ocr_service.extract_text_from_bytes(img_bytes)
            if extracted and len(extracted) > 10:
                ocr_text = extracted
        except Exception as e:
            print(f"⚠️ Step 2 base64 OCR extraction failed: {e}")

    ocr_text = ocr_text or "Delivery document scan"

    try:
        parsed = ocr_parser_service.parse_invoice(ocr_text)
        po_infos = [
            PurchaseOrderInfo(
                po_number=po.po_number,
                description=po.text[:100] if po.text else f"PO {po.po_number}",
                serial_numbers=po.serial_numbers
            )
            for po in parsed.purchase_orders
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse document OCR text: {str(e)}"
        )

    creation_result = po_service.create_document_and_pos(
        db=db,
        supplier=parsed.supplier,
        document_number=parsed.invoice_number,
        extracted_text=ocr_text,
        purchase_orders=po_infos
    )
    
    if not creation_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=creation_result["message"]
        )
    
    return DocumentOCRResponse(
        supplier=parsed.supplier,
        document_number=parsed.invoice_number,
        purchase_orders=po_infos,
        extracted_text=ocr_text,
        success=True,
        message=f"Found {len(po_infos)} Purchase Orders"
    )


@router.post("/step2/confirm/{workflow_id}")
async def confirm_document_scan(workflow_id: str, document_result: DocumentOCRResponse):
    """
    Confirm Step 2 and update workflow state
    """
    workflow = workflow_manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    if workflow.step != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected step 2, currently at step {workflow.step}"
        )
    
    success = workflow_manager.update_workflow_step2(
        workflow_id=workflow_id,
        supplier=document_result.supplier,
        document_number=document_result.document_number,
        purchase_orders=document_result.purchase_orders,
        extracted_text=document_result.extracted_text
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update workflow"
        )
    
    return {
        "message": f"Document scan confirmed. Found {len(document_result.purchase_orders)} Purchase Orders",
        "purchase_orders": [po.model_dump() for po in document_result.purchase_orders],
        "next_step": 3,
        "next_action": "select_purchase_order"
    }


@router.post("/step3/select-po")
async def select_purchase_order(selection: PurchaseOrderSelection, db: Session = Depends(get_db)):
    """
    Step 3: Technician selects correct Purchase Order
    """
    workflow = workflow_manager.get_workflow(selection.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    if workflow.step != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected step 3, currently at step {workflow.step}"
        )
    
    validation_result = po_service.validate_po_selection(
        db=db,
        selected_po_number=selection.selected_po_number,
        available_pos=workflow.purchase_orders
    )
    
    if not validation_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result["message"]
        )
    
    success = workflow_manager.update_workflow_step3(
        selection.workflow_id, selection.selected_po_number
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update workflow"
        )
    
    return {
        "message": f"Purchase Order {selection.selected_po_number} selected",
        "po_details": validation_result["po_info"].model_dump(),
        "next_step": 4,
        "next_action": "scan_package"
    }


@router.post("/step4/scan-package", response_model=PackageLabelResponse)
async def scan_package_label(request: PackageLabelRequest):
    """
    Step 4: Parse package label OCR text
    """
    workflow = workflow_manager.get_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    if workflow.step != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected step 4, currently at step {workflow.step}"
        )
    
    ocr_text = (request.ocr_text or "").strip()

    # If client passed base64 image data instead of OCR text, perform dynamic Azure OCR
    if (not ocr_text or len(ocr_text) < 5 or ocr_text.startswith("data:image")) and request.image_data:
        try:
            raw_b64 = request.image_data
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(raw_b64)
            extracted = azure_ocr_service.extract_text_from_bytes(img_bytes)
            if extracted and len(extracted) > 5:
                ocr_text = extracted
        except Exception as e:
            print(f"⚠️ Step 4 base64 OCR extraction failed: {e}")

    ocr_text = ocr_text or (workflow.category or "Equipment")

    parsed_label = ocr_parser_service.parse_shipping_label(ocr_text)
    
    # Fallback default values from workflow context if package label details missing
    brand = parsed_label.get("brand") or workflow.brand or "Generic"
    product_name = parsed_label.get("product_name") or workflow.product_name or workflow.category or "Equipment"
    article_number = parsed_label.get("article_number") or workflow.article_number or "N/A"
    quantity = parsed_label.get("quantity") or workflow.quantity or 1

    warning = None
    if parsed_label.get("po_number") and workflow.selected_po:
        if parsed_label["po_number"] != workflow.selected_po.po_number:
            warning = f"PO mismatch: Selected {workflow.selected_po.po_number}, Package shows {parsed_label['po_number']}"
    
    return PackageLabelResponse(
        brand=brand,
        product_name=product_name,
        article_number=article_number,
        quantity=quantity,
        po_on_package=parsed_label.get("po_number") or (workflow.selected_po.po_number if workflow.selected_po else None),
        upc=parsed_label.get("upc"),
        ean=parsed_label.get("ean"),
        success=True,
        message="Successfully processed package label scan",
        warning=warning
    )


@router.post("/step4/confirm/{workflow_id}")
async def confirm_package_scan(workflow_id: str, package_result: PackageLabelResponse):
    """
    Confirm Step 4 and update workflow state
    """
    workflow = workflow_manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    if workflow.step != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected step 4, currently at step {workflow.step}"
        )
    
    success = workflow_manager.update_workflow_step4(
        workflow_id=workflow_id,
        brand=package_result.brand,
        product_name=package_result.product_name,
        article_number=package_result.article_number,
        quantity=package_result.quantity,
        po_on_package=package_result.po_on_package,
        extracted_text=""
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update workflow"
        )
    
    return {
        "message": f"Package scan confirmed for {package_result.product_name}",
        "warning": package_result.warning,
        "next_step": 5,
        "next_action": "save_stock_entry"
    }


@router.post("/step5/save", response_model=StockEntryCompleteResponse)
async def save_stock_entry(request: StockEntrySaveRequest, db: Session = Depends(get_db)):
    """
    Step 5: Save complete stock entry to database
    """
    workflow = workflow_manager.get_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    if workflow.step != 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected step 5, currently at step {workflow.step}"
        )
    
    if workflow.warnings and not request.confirm_warnings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Workflow has warnings that require confirmation",
                "warnings": workflow.warnings,
                "confirm_required": True
            }
        )
    
    po_record = po_service.get_purchase_order_by_number(db, workflow.selected_po.po_number)
    if not po_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found in database"
        )
    
    creation_result = inventory_service.receive_stock(
        db=db,
        product_ref=workflow.article_number or workflow.product_name,
        quantity=workflow.quantity or 1,
        technician=request.received_by,
        po_id=str(po_record.id),
        category=workflow.category,
        brand=workflow.brand,
        product_name=workflow.product_name,
        article_number=workflow.article_number,
        serial_numbers=workflow.serial_numbers,
    )
    
    workflow_manager.complete_workflow(request.workflow_id)
    
    return StockEntryCompleteResponse(
        category=workflow.category or "Equipment",
        brand=workflow.brand or "Generic",
        product_name=workflow.product_name or "Equipment",
        article_number=workflow.article_number or "N/A",
        quantity=workflow.quantity or 1,
        supplier=workflow.supplier or "Unknown",
        selected_po=workflow.selected_po.po_number,
        serial_numbers=workflow.serial_numbers,
        status="COMPLETED",
        inventory_id=creation_result.get("inventory_id") or creation_result.get("inventory_ids", [None])[0],
        stock_entry_id=creation_result.get("id"),
        warnings=workflow.warnings
    )


@router.delete("/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """
    Cancel and delete workflow session
    """
    success = workflow_manager.delete_workflow(workflow_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    return {"message": "Workflow cancelled successfully"}


@router.get("/admin/workflows")
async def list_active_workflows():
    """
    Admin endpoint: List all active workflows
    """
    return workflow_manager.list_active_workflows()