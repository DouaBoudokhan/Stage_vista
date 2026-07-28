"""Pydantic Schemas Package"""
from .user import User, UserCreate, UserLogin, Token
from .product import Product, ProductCreate, ProductUpdate
from .inventory import InventoryMovement, Ticket, TicketCreate, StockIn, StockOut
from .invoice import Invoice, InvoiceCreate
from .stock_entry import (
    ProductDetectionRequest, ProductDetectionResponse,
    DocumentOCRRequest, DocumentOCRResponse,
    PurchaseOrderSelection, PackageLabelRequest, PackageLabelResponse,
    StockEntrySaveRequest, StockEntryCompleteResponse,
    WorkflowStatusResponse, WorkflowState, PurchaseOrderInfo
)

__all__ = [
    "User", "UserCreate", "UserLogin", "Token",
    "Product", "ProductCreate", "ProductUpdate",
    "InventoryMovement", "Ticket", "TicketCreate", "StockIn", "StockOut",
    "Invoice", "InvoiceCreate",
    "ProductDetectionRequest", "ProductDetectionResponse",
    "DocumentOCRRequest", "DocumentOCRResponse",
    "PurchaseOrderSelection", "PackageLabelRequest", "PackageLabelResponse",
    "StockEntrySaveRequest", "StockEntryCompleteResponse",
    "WorkflowStatusResponse", "WorkflowState", "PurchaseOrderInfo",
]
