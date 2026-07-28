"""Debug database connection"""
import os
from sqlalchemy import create_engine, text
from app.config import settings

print("Testing database connection...")
print(f"DATABASE_URL: {settings.DATABASE_URL}")

try:
    # Test engine creation
    print("Creating engine...")
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )
    print("✅ Engine created")
    
    # Test connection
    print("Testing connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"✅ Connection successful: {result.scalar()}")
        
except Exception as e:
    print(f"❌ Database error: {e}")