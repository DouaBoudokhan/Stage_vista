"""Ticket model with Jira sync and AI analysis caching."""
from sqlalchemy import Column, DateTime, String, Text, Boolean, Float, Integer, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Ticket(Base):
    """
    Support ticket model - Jira is the single source of truth.
    Local database is used as cache for AI analysis and metadata.
    """

    __tablename__ = "tickets"

    id = Column(String, primary_key=True)  # T-XXXXXXXX format or Jira issue key
    
    # Jira fields (synced from Jira API)
    jira_key = Column(String, unique=True, nullable=False, index=True)  # Unique Jira issue key (e.g., IT-123)
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
    jira_last_updated = Column(DateTime(timezone=True))  # Last updated timestamp from Jira
    
    # AI analysis cache (local only, not from Jira)
    ai_analyzed = Column(Boolean, default=False, nullable=False)  # Whether AI analysis has been performed
    ai_analysis = Column(Text)  # Full AI analysis result (JSON)
    ai_score = Column(Float)  # AI recommendation score (0-100)
    ai_reason = Column(Text)  # Human-readable reason for recommendation
    ai_recommended_product = Column(String)  # Recommended product category
    ai_recommended_quantity = Column(Integer)  # Recommended quantity
    ai_confidence = Column(Float)  # AI confidence score (0-100)
    ai_model = Column(String)  # AI model used (e.g., "llama-3.3-70b")
    analyzed_at = Column(DateTime(timezone=True))  # When AI analysis was performed

    stock_exits = relationship("StockExit", back_populates="ticket")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tickets_jira_key', 'jira_key'),
        Index('idx_tickets_ai_analyzed', 'ai_analyzed'),
        Index('idx_tickets_status', 'status'),
    )

    def __repr__(self):
        return f"<Ticket(jira_key='{self.jira_key}', status='{self.status}', title='{self.title}')>"
    
    def needs_ai_analysis(self) -> bool:
        """
        Determine if this ticket needs AI analysis.
        Returns True if:
        - Never analyzed before, OR
        - Jira ticket was updated after last analysis
        """
        if not self.ai_analyzed:
            return True
        if not self.analyzed_at or not self.jira_last_updated:
            return True
        return self.jira_last_updated > self.analyzed_at
