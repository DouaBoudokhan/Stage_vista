"""Inventory Model"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from ..database import Base


class Inventory(Base):
    """Inventory items model"""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    brand = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    article_number = Column(String, nullable=False)
    serial_number = Column(String)
    quantity_available = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False)  # available, assigned, maintenance, etc.
    received_by = Column(String, nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", lazy="joined")

    @hybrid_property
    def category(self):
        """Backward-compatible read-only category via products FK."""
        if self.product is not None and getattr(self.product, "product_type", None):
            return self.product.product_type
        return None

    def __repr__(self):
        return f"<Inventory(product='{self.product_name}', qty={self.quantity_available})>"


class InventoryMovement(Base):
    """Inventory movement tracking model"""

    __tablename__ = "inventory_movements"

    id = Column(String, primary_key=True)  # MOV-XXXXXXXX format
    product_id = Column(String, nullable=False)
    product_name = Column(String)
    action = Column(String, nullable=False)  # IN or OUT
    quantity = Column(Integer, nullable=False)
    user = Column(String, nullable=False)
    po_id = Column(String)
    reference = Column(String)
    ticket_id = Column(String)
    assignee = Column(String)
    notes = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<InventoryMovement(id='{self.id}', action='{self.action}', qty={self.quantity})>"


class Ticket(Base):
    """Support ticket model"""

    __tablename__ = "tickets"

    id = Column(String, primary_key=True)  # T-XXXXXXXX format
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(String, nullable=False, default="Medium")
    category = Column(String)
    product_needed = Column(String)
    status = Column(String, nullable=False, default="Open")
    requester = Column(String)
    assignee = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Ticket(id='{self.id}', status='{self.status}', title='{self.title}')>"
