"""
Database Configuration
SQLAlchemy setup for PostgreSQL (Supabase)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    Automatically closes session after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import text


def init_db():
    """Initialize database - create all tables and ensure required columns exist"""
    # Import models package so Base.metadata contains all tables
    from . import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
    
    # Run auto-migration for PostgreSQL/Supabase missing columns and types
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE documents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                ALTER TABLE documents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                ALTER TABLE documents ALTER COLUMN supplier TYPE TEXT;
                ALTER TABLE documents ALTER COLUMN document_number TYPE TEXT;
                ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS description TEXT;
                ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS serial_numbers TEXT;
                ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            """))
            conn.commit()
            print("✅ Database schema synchronized with missing columns and expanded column types")
        except Exception as e:
            print(f"⚠️ Schema migration notice: {e}")
