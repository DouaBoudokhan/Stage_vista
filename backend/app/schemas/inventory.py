"""Inventory and Ticket Schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class InventoryItem(BaseModel):
    """Single row from the inventory table (current on-hand stock)."""

    id: int
    product_id: int
    category: Optional[str] = None
    brand: str
    product_name: str
    article_number: str
    serial_number: Optional[str] = None
    quantity_available: int
    status: str
    received_by: str
    received_at: Optional[datetime] = None
    purchase_order_id: Optional[int] = None
    po_number: Optional[str] = None

    class Config:
        from_attributes = True


class StockHistoryRecord(BaseModel):
    """Unified stock-in / stock-out event from audit tables."""

    id: str
    source_table: str  # stock_entries | stock_exits | inventory_movements
    source_id: int
    action: str  # IN | OUT
    inventory_id: Optional[int] = None
    product_name: Optional[str] = None
    article_number: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    quantity: int
    technician: str
    timestamp: datetime
    po_number: Optional[str] = None
    ticket_id: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class InventoryMovementBase(BaseModel):
    """Base inventory movement schema"""
    product_id: str
    action: str
    quantity: int
    user: str
    notes: Optional[str] = None


class StockIn(BaseModel):
    """Schema for receiving stock"""
    ref: str  # Product reference/barcode
    quantity: int
    poId: Optional[str] = None
    technician: str
    category: Optional[str] = None
    brand: Optional[str] = None
    productName: Optional[str] = None
    articleNumber: Optional[str] = None
    serialNumbers: Optional[list[str]] = None
    notes: Optional[str] = None


class StockOut(BaseModel):
    """Schema for assigning stock"""
    productId: str
    quantity: int
    ticketId: str
    technician: str
    notes: Optional[str] = None


class InventoryMovement(InventoryMovementBase):
    """Schema for inventory movement response"""
    id: str
    product_name: Optional[str] = None
    po_id: Optional[str] = None
    reference: Optional[str] = None
    ticket_id: Optional[str] = None
    assignee: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    """Base ticket schema"""
    title: str
    description: Optional[str] = None
    priority: str = "Medium"
    category: Optional[str] = None
    product_needed: Optional[str] = None


class TicketCreate(TicketBase):
    """Schema for creating a ticket"""
    requester: str


class Ticket(TicketBase):
    """Schema for ticket response"""
    id: str
    status: str
    requester: Optional[str] = None
    assignee: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
