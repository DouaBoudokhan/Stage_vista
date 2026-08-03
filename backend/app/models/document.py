"""Document Model - Enhanced for Invoice Analysis"""
from sqlalchemy import Column, String, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Document(Base):
    """Document model for storing scanned invoices/delivery documents"""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_type = Column(String(100), nullable=False)  # 'invoice', 'delivery_note', etc.
    document_number = Column(String(255), nullable=False)  # Invoice number extracted from OCR
    supplier = Column(String(255), nullable=False)  # Supplier name extracted from OCR
    image_path = Column(String(500), nullable=False)  # Path to stored image file
    extracted_text = Column(Text)  # Full OCR text for auditing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    purchase_orders = relationship("PurchaseOrder", back_populates="document")

    __table_args__ = (
        UniqueConstraint("document_type", "document_number", name="uq_documents_type_number"),
    )
    
    def __repr__(self):
        return f"<Document(type='{self.document_type}', number='{self.document_number}', supplier='{self.supplier}')>"
