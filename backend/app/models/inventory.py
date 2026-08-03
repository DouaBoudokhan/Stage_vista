"""Inventory model."""
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base

VALID_INVENTORY_STATUSES = ("AVAILABLE", "ASSIGNED", "MAINTENANCE", "RETIRED", "LOST")


class Inventory(Base):
    """Inventory rows representing physical assets or bulk stock batches."""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    brand = Column(String, nullable=True, default="Generic")
    product_name = Column(String, nullable=True, default="Equipment")
    article_number = Column(String, nullable=False)
    serial_number = Column(String, nullable=True)
    quantity_available = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="AVAILABLE")
    received_by = Column(String, nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="inventory_items", lazy="joined")
    purchase_order = relationship("PurchaseOrder", back_populates="inventory_items")
    stock_entries = relationship("StockEntry", back_populates="inventory")
    stock_exits = relationship("StockExit", back_populates="inventory")

    __table_args__ = (
        CheckConstraint(
            f"status IN {VALID_INVENTORY_STATUSES}",
            name="ck_inventory_status",
        ),
    )

    @hybrid_property
    def tracking_type(self):
        """Read-only property delegating tracking_type resolution to the master product."""
        if self.product is not None and getattr(self.product, "tracking_type", None):
            return self.product.tracking_type
        return "BULK"

    @hybrid_property
    def category(self):
        """Backward-compatible read-only category via products FK."""
        if self.product is not None and getattr(self.product, "product_name", None):
            return self.product.product_name
        return None

    def __repr__(self):
        return (
            f"<Inventory(id={self.id}, product_id={self.product_id}, "
            f"status='{self.status}', qty={self.quantity_available})>"
        )
