"""Ticket model."""
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Ticket(Base):
    """Support ticket model."""

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

    stock_exits = relationship("StockExit", back_populates="ticket")

    def __repr__(self):
        return f"<Ticket(id='{self.id}', status='{self.status}', title='{self.title}')>"
