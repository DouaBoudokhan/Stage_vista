"""Purchase Order Model - Enhanced with LLM caching"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class PurchaseOrder(Base):
    """Purchase Order model with LLM-generated description caching"""
    
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    po_number = Column(String(255), nullable=False, unique=True, index=True)  # Unique for cache lookup
    description = Column(Text)  # LLM-generated description (cached)
    serial_numbers = Column(Text)  # Comma-separated serial numbers extracted from the document
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    document = relationship("Document", back_populates="purchase_orders")
    inventory_items = relationship("Inventory", back_populates="purchase_order")
    stock_entries = relationship("StockEntry", back_populates="purchase_order")
    
    def __repr__(self):
        return f"<PurchaseOrder(po_number='{self.po_number}', has_description={self.description is not None})>"
