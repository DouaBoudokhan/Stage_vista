"""Stock Exit Model"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class StockExit(Base):
    """Stock exits model - tracking items assigned/removed"""
    
    __tablename__ = "stock_exits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    ticket_number = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<StockExit(inventory_id={self.inventory_id}, qty={self.quantity})>"