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


from sqlalchemy import inspect, text


def _inventory_has_column(column_name: str) -> bool:
    """Return True if inventory table exists and has the given column."""
    try:
        inv_columns = {c["name"] for c in inspect(engine).get_columns("inventory")}
        return column_name in inv_columns
    except Exception:
        return False


def init_db():
    """Initialize database - create all tables and ensure required columns exist"""
    # Import all models so Base.metadata contains all tables (including new Products)
    from . import models  # noqa: F401
    from .models.product import Product  # ensure Products is registered explicitly

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
            print("✅ Legacy schema synchronization for documents/purchase_orders complete")
        except Exception as e:
            print(f"⚠️ Schema migration notice (legacy tables): {e}")

    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE inventory ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES products(id);
            """))
            conn.commit()
            print("✅ inventory.product_id FK column added (if missing)")
        except Exception as e:
            print(f"⚠️ Schema migration notice (inventory.product_id FK): {e}")

    with engine.connect() as conn:
        try:
            # Legacy Supabase schema uses products.category; greenfield installs get the same via ORM mapping.
            conn.execute(text("""
                INSERT INTO products (category, stock_on_hand)
                VALUES
                    ('Laptop', 0),
                    ('Mouse', 0),
                    ('Keyboard', 0),
                    ('Monitor', 0),
                    ('Headset', 0)
                ON CONFLICT (category) DO NOTHING;
            """))
            conn.commit()
            print("✅ Products table seeded with 5 core product_types (upsert)")
        except Exception as e:
            print(f"⚠️ Products seed notice: {e}")

    if _inventory_has_column("category"):
        with engine.connect() as conn:
            try:
                conn.execute(text("""
                    UPDATE inventory
                    SET product_id = products.id
                    FROM products
                    WHERE inventory.product_id IS NULL
                      AND COALESCE(inventory.category, '') = products.category;
                """))
                conn.commit()
                print("✅ Back-filled inventory.product_id FK from legacy category mapping")
            except Exception as e:
                print(f"⚠️ Product FK back-fill notice: {e}")

        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE inventory DROP COLUMN IF EXISTS category"))
                conn.commit()
                print("✅ Dropped legacy inventory.category column (product_id is source of truth)")
            except Exception as e:
                print(f"⚠️ inventory.category drop notice: {e}")
    else:
        print("ℹ️ inventory.category already removed; skipping legacy back-fill/drop")

    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE inventory ALTER COLUMN product_id SET NOT NULL;
            """))
            conn.commit()
            print("✅ inventory.product_id set NOT NULL")
        except Exception as e:
            print(f"⚠️ inventory.product_id NOT NULL notice: {e}")

    with engine.connect() as conn:
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
            print("✅ Products.stock_on_hand recomputed as SUM(inventory.quantity_available) per product_type")
        except Exception as e:
            print(f"⚠️ stock_on_hand recomputation notice: {e}")

        try:
            conn.execute(text("""
                UPDATE products
                SET stock_on_hand = 0
                WHERE id NOT IN (SELECT DISTINCT product_id FROM inventory WHERE product_id IS NOT NULL);
            """))
            conn.commit()
        except Exception as e:
            print(f"⚠️ stock_on_hand zero-fill notice: {e}")
