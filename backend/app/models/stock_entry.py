"""Stock entry model."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class StockEntry(Base):
    """Stock entries model - tracking items received."""
    
    __tablename__ = "stock_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    quantity_received = Column(Integer, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inventory = relationship("Inventory", back_populates="stock_entries")
    purchase_order = relationship("PurchaseOrder", back_populates="stock_entries")
    
    def __repr__(self):
        return f"<StockEntry(inventory_id={self.inventory_id}, qty={self.quantity_received})>"
