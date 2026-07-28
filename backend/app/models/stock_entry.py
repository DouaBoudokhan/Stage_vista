"""Stock Entry Model"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class StockEntry(Base):
    """Stock entries model - tracking items received"""
    
    __tablename__ = "stock_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    quantity_received = Column(Integer, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<StockEntry(inventory_id={self.inventory_id}, qty={self.quantity_received})>"