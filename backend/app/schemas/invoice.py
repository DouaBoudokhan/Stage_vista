"""Invoice Schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class InvoiceBase(BaseModel):
    """Base invoice schema"""
    invoice_number: str
    supplier: Optional[str] = None
    total_amount: Optional[float] = None
    currency: str = "EUR"
    notes: Optional[str] = None


class InvoiceCreate(BaseModel):
    """Schema for creating invoice from OCR"""
    image_base64: str
    processed_by: str


class Invoice(InvoiceBase):
    """Schema for invoice response"""
    id: str
    extracted_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    image_path: Optional[str] = None
    status: str
    processed_by: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
