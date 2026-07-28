"""Product Schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProductBase(BaseModel):
    """Base product schema"""
    name: str
    reference: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    quantity: int = 0
    min_quantity: int = 5
    price: float = 0.0
    location: Optional[str] = None
    supplier: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = None
    reference: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    quantity: Optional[int] = None
    min_quantity: Optional[int] = None
    price: Optional[float] = None
    location: Optional[str] = None
    supplier: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class Product(ProductBase):
    """Schema for product response"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_updated: Optional[str] = None
    
    class Config:
        from_attributes = True
