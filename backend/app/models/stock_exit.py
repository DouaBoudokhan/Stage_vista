"""Stock exit model."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class StockExit(Base):
    """Stock exits model - tracking items assigned/removed."""
    
    __tablename__ = "stock_exits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    ticket_id = Column("ticket_number", String, ForeignKey("tickets.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inventory = relationship("Inventory", back_populates="stock_exits")
    ticket = relationship("Ticket", back_populates="stock_exits")
    
    def __repr__(self):
        return f"<StockExit(inventory_id={self.inventory_id}, qty={self.quantity})>"
