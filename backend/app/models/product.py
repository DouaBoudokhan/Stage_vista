"""Product model and inventory tracking source-of-truth."""
from sqlalchemy import CheckConstraint, Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from ..database import Base

VALID_PRODUCT_NAMES = ("Laptop", "Mouse", "Keyboard", "Monitor", "Headset")
SERIALIZED_PRODUCTS = {"Laptop", "Monitor"}
BULK_PRODUCTS = {"Headset", "Mouse", "Keyboard"}


def get_tracking_type(product_name: str) -> str:
    """Resolve the inventory tracking mode for a supported product name."""
    normalized = (product_name or "").strip()
    if normalized in SERIALIZED_PRODUCTS:
        return "SERIALIZED"
    if normalized in BULK_PRODUCTS:
        return "BULK"
    raise ValueError(
        f"Unknown product category '{product_name}'. Expected one of: "
        f"{', '.join(VALID_PRODUCT_NAMES)}."
    )


class Product(Base):
    """Master product catalog table (aggregate by product_name)."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column("category", String, nullable=False, index=True)
    tracking_type = Column(String, nullable=False, default="BULK")  # SERIALIZED | BULK
    stock_on_hand = Column(Integer, nullable=False, default=0)

    inventory_items = relationship("Inventory", back_populates="product")

    __table_args__ = (
        UniqueConstraint("category", name="uq_products_product_name"),
        CheckConstraint(
            f"category IN {VALID_PRODUCT_NAMES}",
            name="ck_products_product_name_enum",
        ),
        CheckConstraint(
            "tracking_type IN ('SERIALIZED', 'BULK')",
            name="ck_products_tracking_type",
        ),
    )

    def __repr__(self):
        return (
            f"<Product(id={self.id}, product_name='{self.product_name}', "
            f"tracking_type='{self.tracking_type}', stock_on_hand={self.stock_on_hand})>"
        )
