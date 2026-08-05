"""User Model"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    """User model for authentication and authorization"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, manager, technician
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
