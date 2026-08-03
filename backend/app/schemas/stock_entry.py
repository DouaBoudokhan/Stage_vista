"""Stock Entry Workflow Schemas"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ProductDetectionRequest(BaseModel):
    """Request for product detection (Step 1)"""
    image_data: str = Field(..., description="Base64 encoded image")
    
    
class ProductDetectionResponse(BaseModel):
    """Response from product detection"""
    category: str
    confidence: float
    success: bool
    message: Optional[str] = None


class DocumentOCRRequest(BaseModel):
    """Request for document OCR (Step 2)"""
    image_data: str = Field(..., description="Base64 encoded document image")
    
    
class PurchaseOrderInfo(BaseModel):
    """Purchase Order information extracted from document"""
    po_number: str
    description: str
    serial_numbers: List[str] = []


class DocumentOCRResponse(BaseModel):
    """Response from document OCR"""
    supplier: str
    document_number: str
    purchase_orders: List[PurchaseOrderInfo]
    extracted_text: str
    success: bool
    message: Optional[str] = None


class PurchaseOrderSelection(BaseModel):
    """Technician's selection of Purchase Order (Step 3)"""
    selected_po_number: str
    workflow_id: str = Field(..., description="Workflow session ID")


class PackageLabelRequest(BaseModel):
    """Request for package label OCR (Step 4)"""
    image_data: str = Field(..., description="Base64 encoded package label image")
    workflow_id: str = Field(..., description="Workflow session ID")


class PackageLabelResponse(BaseModel):
    """Response from package label OCR"""
    brand: str
    product_name: str
    article_number: str
    quantity: int
    po_on_package: Optional[str] = None
    upc: Optional[str] = None
    ean: Optional[str] = None
    success: bool
    message: Optional[str] = None
    warning: Optional[str] = None


class StockEntrySaveRequest(BaseModel):
    """Request to save stock entry (Step 5)"""
    workflow_id: str = Field(..., description="Workflow session ID")
    received_by: str = Field(..., description="Technician who received the items")
    confirm_warnings: bool = Field(default=False, description="Confirm despite warnings")


class WorkflowState(BaseModel):
    """Complete workflow state"""
    workflow_id: str
    step: int = Field(default=1, description="Current step (1-5)")
    category: Optional[str] = None
    confidence: Optional[float] = None
    supplier: Optional[str] = None
    document_number: Optional[str] = None
    purchase_orders: List[PurchaseOrderInfo] = []
    selected_po: Optional[PurchaseOrderInfo] = None
    brand: Optional[str] = None
    product_name: Optional[str] = None
    article_number: Optional[str] = None
    quantity: Optional[int] = None
    po_on_package: Optional[str] = None
    serial_numbers: List[str] = []
    extracted_texts: Dict[str, str] = {}  # Store OCR results for auditing
    warnings: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StockEntryCompleteResponse(BaseModel):
    """Final response after complete workflow"""
    category: str
    brand: str
    product_name: str
    article_number: str
    quantity: int
    supplier: str
    selected_po: str
    serial_numbers: List[str]
    status: str = "READY_TO_SAVE"
    inventory_id: Optional[int] = None
    stock_entry_id: Optional[int] = None
    warnings: List[str] = []


class WorkflowStatusResponse(BaseModel):
    """Workflow status response"""
    workflow_id: str
    current_step: int
    status: str  # "IN_PROGRESS", "COMPLETED", "FAILED"
    data: Dict[str, Any] = {}
    next_action: Optional[str] = None
    warnings: List[str] = []