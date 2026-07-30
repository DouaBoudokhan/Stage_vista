"""Product Model - Master Product Table (3 columns only)"""
from sqlalchemy import Column, String, Integer, UniqueConstraint, CheckConstraint
from ..database import Base

VALID_PRODUCT_TYPES = ("Laptop", "Mouse", "Keyboard", "Monitor", "Headset")


class Product(Base):
    """Master product catalog table (aggregate by product_type)"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Supabase legacy schema uses column name "category"; ORM exposes it as product_type.
    product_type = Column("category", String, nullable=False, index=True)
    stock_on_hand = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("category", name="uq_products_product_type"),
        CheckConstraint(
            f"category IN {VALID_PRODUCT_TYPES}",
            name="ck_products_product_type_enum",
        ),
    )

    def __repr__(self):
        return (
            f"<Product(id={self.id}, type='{self.product_type}', "
            f"stock_on_hand={self.stock_on_hand})>"
        )
