"""
Database Configuration
SQLAlchemy setup for PostgreSQL (Supabase) / SQLite
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
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


def _table_has_column(table_name: str, column_name: str) -> bool:
    """Return True if table exists and has the given column."""
    try:
        columns = {c["name"] for c in inspect(engine).get_columns(table_name)}
        return column_name in columns
    except Exception:
        return False


def init_db():
    """Initialize database - create all 8 required tables and run light migrations"""
    # Import models so Base.metadata contains all 8 required tables
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # 1. Sync legacy schema for documents / purchase_orders if needed
        try:
            conn.execute(text("""
                ALTER TABLE documents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                ALTER TABLE documents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS description TEXT;
                ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS serial_numbers TEXT;
                ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            """))
            conn.commit()
        except Exception as e:
            print(f"⚠️ Document/PO schema sync notice: {e}")

        # 2. Add tracking_type to products and backfill
        try:
            conn.execute(text("""
                ALTER TABLE products ADD COLUMN IF NOT EXISTS tracking_type VARCHAR DEFAULT 'BULK';
                UPDATE products SET tracking_type = 'SERIALIZED' WHERE category IN ('Laptop', 'Monitor');
                UPDATE products SET tracking_type = 'BULK' WHERE category IN ('Mouse', 'Keyboard', 'Headset');
            """))
            conn.commit()
            print("✅ products.tracking_type added and backfilled")
        except Exception as e:
            print(f"⚠️ Products tracking_type sync notice: {e}")

        # 3. Add product_id to inventory if missing, and drop legacy inventory.tracking_type
        try:
            conn.execute(text("""
                ALTER TABLE inventory ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES products(id);
                ALTER TABLE inventory DROP COLUMN IF EXISTS tracking_type;
            """))
            conn.commit()
            print("✅ inventory schema sync (dropped tracking_type from inventory)")
        except Exception as e:
            print(f"⚠️ Inventory schema sync notice: {e}")

        # 4. Add purchase_order_id to stock_entries
        try:
            conn.execute(text("""
                ALTER TABLE stock_entries ADD COLUMN IF NOT EXISTS purchase_order_id INTEGER REFERENCES purchase_orders(id);
            """))
            conn.commit()
        except Exception as e:
            print(f"⚠️ StockEntries schema sync notice: {e}")

        # 5. Seed products table with 5 core categories and tracking_type
        try:
            conn.execute(text("""
                INSERT INTO products (category, tracking_type, stock_on_hand)
                VALUES
                    ('Laptop', 'SERIALIZED', 0),
                    ('Mouse', 'BULK', 0),
                    ('Keyboard', 'BULK', 0),
                    ('Monitor', 'SERIALIZED', 0),
                    ('Headset', 'BULK', 0)
                ON CONFLICT (category) DO NOTHING;
            """))
            conn.commit()
            print("✅ Products table seeded with 5 core categories and tracking_types")
        except Exception as e:
            print(f"⚠️ Products seed notice: {e}")

        # 6. Drop legacy inventory.category column if present
        if _table_has_column("inventory", "category"):
            try:
                conn.execute(text("""
                    UPDATE inventory
                    SET product_id = products.id
                    FROM products
                    WHERE inventory.product_id IS NULL
                      AND COALESCE(inventory.category, '') = products.category;
                """))
                conn.execute(text("ALTER TABLE inventory DROP COLUMN IF EXISTS category;"))
                conn.commit()
                print("✅ Dropped legacy inventory.category column")
            except Exception as e:
                print(f"⚠️ Legacy category drop notice: {e}")

        # 7. Update products.stock_on_hand from active inventory
        try:
            conn.execute(text("""
                UPDATE products
                SET stock_on_hand = COALESCE(agg.total_qty, 0)
                FROM (
                    SELECT product_id, SUM(quantity_available) AS total_qty
                    FROM inventory
                    WHERE product_id IS NOT NULL
                    GROUP BY product_id
                ) AS agg
                WHERE products.id = agg.product_id;
            """))
            conn.commit()
            print("✅ products.stock_on_hand synchronized")
        except Exception as e:
            print(f"⚠️ stock_on_hand sync notice: {e}")
        
        # 8. Add Jira sync and AI analysis fields to tickets table
        try:
            conn.execute(text("""
                -- Add jira_key column (unique identifier from Jira)
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS jira_key VARCHAR UNIQUE;
                
                -- Add Jira sync fields
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS jira_last_updated TIMESTAMP WITH TIME ZONE;
                
                -- Add AI analysis cache fields
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ai_analyzed BOOLEAN DEFAULT FALSE NOT NULL;
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ai_analysis TEXT;
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ai_score FLOAT;
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ai_reason TEXT;
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ai_recommended_product VARCHAR;
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ai_recommended_quantity INTEGER;
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ai_confidence FLOAT;
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ai_model VARCHAR;
                ALTER TABLE tickets ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMP WITH TIME ZONE;
                
                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS idx_tickets_jira_key ON tickets(jira_key);
                CREATE INDEX IF NOT EXISTS idx_tickets_ai_analyzed ON tickets(ai_analyzed);
                CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
                
                -- Backfill jira_key from id for existing tickets
                UPDATE tickets SET jira_key = id WHERE jira_key IS NULL;
            """))
            conn.commit()
            print("✅ Tickets table extended with Jira sync and AI analysis fields")
        except Exception as e:
            print(f"⚠️ Tickets schema sync notice: {e}")
        
        # 9. Seed default admin user
        try:
            from ..utils.security import get_password_hash
            # Default password: admin123 (should be changed after first login)
            hashed_password = get_password_hash("admin123")
            
            conn.execute(text("""
                INSERT INTO users (id, email, name, role, hashed_password, is_active)
                VALUES ('admin-default-user', 'admin@stockit.local', 'Admin User', 'admin', :hashed_password, true)
                ON CONFLICT (email) DO NOTHING;
            """), {"hashed_password": hashed_password})
            conn.commit()
            print("✅ Default admin user seeded (email: admin@stockit.local, password: admin123)")
        except Exception as e:
            print(f"⚠️ User seed notice: {e}")
        
        # 10. Rename stock_exits.ticket_number to ticket_id
        try:
            # Check if old column exists
            if _table_has_column("stock_exits", "ticket_number"):
                conn.execute(text("""
                    ALTER TABLE stock_exits RENAME COLUMN ticket_number TO ticket_id;
                """))
                conn.commit()
                print("✅ Renamed stock_exits.ticket_number to ticket_id")
            else:
                print("✅ stock_exits.ticket_id already correct")
        except Exception as e:
            print(f"⚠️ StockExit column rename notice: {e}")


