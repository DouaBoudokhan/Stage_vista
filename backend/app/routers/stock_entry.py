"""Stock Entry Workflow Router"""
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
from ..services.ocr_service import ocr_service
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
    # Run YOLO detection
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
    Step 2: Scan delivery document and extract Purchase Orders
    """
    # Run OCR on document
    success, result = ocr_service.process_delivery_document(request.image_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    # Create document and POs in database
    creation_result = po_service.create_document_and_pos(
        db=db,
        supplier=result["supplier"],
        document_number=result["document_number"],
        extracted_text=result["extracted_text"],
        purchase_orders=result["purchase_orders"]
    )
    
    if not creation_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=creation_result["message"]
        )
    
    return DocumentOCRResponse(
        supplier=result["supplier"],
        document_number=result["document_number"],
        purchase_orders=result["purchase_orders"],
        extracted_text=result["extracted_text"],
        success=True,
        message=result["message"]
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
        "purchase_orders": [po.dict() for po in document_result.purchase_orders],
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
    
    # Validate PO selection
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
    
    # Update workflow
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
        "po_details": validation_result["po_info"].dict(),
        "next_step": 4,
        "next_action": "scan_package"
    }


@router.post("/step4/scan-package", response_model=PackageLabelResponse)
async def scan_package_label(request: PackageLabelRequest):
    """
    Step 4: Scan package label and extract product details
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
    
    # Run OCR on package label
    success, result = ocr_service.process_package_label(request.image_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    # Check for PO mismatch
    warning = None
    if result.get("po_on_package") and workflow.selected_po:
        if result["po_on_package"] != workflow.selected_po.po_number:
            warning = f"PO mismatch: Selected {workflow.selected_po.po_number}, Package shows {result['po_on_package']}"
    
    return PackageLabelResponse(
        brand=result["brand"],
        product_name=result["product_name"],
        article_number=result["article_number"],
        quantity=result["quantity"],
        po_on_package=result.get("po_on_package"),
        success=True,
        message=result["message"],
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
        extracted_text=""  # Could be added to PackageLabelResponse
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
    
    # Check for warnings if not confirmed
    if workflow.warnings and not request.confirm_warnings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Workflow has warnings that require confirmation",
                "warnings": workflow.warnings,
                "confirm_required": True
            }
        )
    
    # Get PO ID from database
    po_record = po_service.get_purchase_order_by_number(db, workflow.selected_po.po_number)
    if not po_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found in database"
        )
    
    # Create inventory and stock entry
    creation_result = inventory_service.create_inventory_and_stock_entry(
        db=db,
        workflow_state=workflow,
        received_by=request.received_by,
        po_id=po_record.id
    )
    
    if not creation_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=creation_result["message"]
        )
    
    # Mark workflow as completed
    workflow_manager.complete_workflow(request.workflow_id)
    
    return StockEntryCompleteResponse(
        category=workflow.category,
        brand=workflow.brand,
        product_name=workflow.product_name,
        article_number=workflow.article_number,
        quantity=workflow.quantity,
        supplier=workflow.supplier,
        selected_po=workflow.selected_po.po_number,
        serial_numbers=workflow.serial_numbers,
        status="COMPLETED",
        inventory_id=creation_result["inventory_id"],
        stock_entry_id=creation_result["stock_entry_id"],
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