"""User Schemas"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    email: str  # Changed from EmailStr to allow .local domains
    name: str
    role: str = "technician"
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation that allows .local domains"""
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str


class UserLogin(BaseModel):
    """Schema for user login"""
    email: str  # Changed from EmailStr to allow .local domains
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation that allows .local domains"""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class User(UserBase):
    """Schema for user response"""
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token"""
    email: Optional[str] = None
