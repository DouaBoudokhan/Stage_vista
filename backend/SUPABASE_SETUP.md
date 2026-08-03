# Supabase Setup Guide for StockIT

## Required Tables (8 Tables)

```sql
-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Products Table (Master Catalog)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category VARCHAR UNIQUE NOT NULL,
    tracking_type VARCHAR NOT NULL DEFAULT 'BULK', -- 'SERIALIZED' or 'BULK'
    stock_on_hand INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT ck_products_tracking_type CHECK (tracking_type IN ('SERIALIZED', 'BULK'))
);

-- 3. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(100) NOT NULL,
    document_number VARCHAR(255) NOT NULL,
    supplier VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    extracted_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_documents_type_number UNIQUE (document_type, document_number)
);

-- 4. Purchase Orders Table
CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    po_number VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    serial_numbers TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Inventory Table
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) NOT NULL,
    purchase_order_id INTEGER REFERENCES purchase_orders(id) NOT NULL,
    article_number VARCHAR NOT NULL,
    serial_number VARCHAR,
    quantity_available INTEGER NOT NULL DEFAULT 0,
    status VARCHAR NOT NULL DEFAULT 'AVAILABLE', -- 'AVAILABLE', 'ASSIGNED', 'MAINTENANCE', 'RETIRED', 'LOST'
    received_by VARCHAR NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_inventory_status CHECK (status IN ('AVAILABLE', 'ASSIGNED', 'MAINTENANCE', 'RETIRED', 'LOST'))
);

-- 6. Stock Entries Table
CREATE TABLE IF NOT EXISTS stock_entries (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES inventory(id) ON DELETE CASCADE NOT NULL,
    purchase_order_id INTEGER REFERENCES purchase_orders(id) ON DELETE CASCADE NOT NULL,
    quantity_received INTEGER NOT NULL,
    created_by VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Stock Exits Table
CREATE TABLE IF NOT EXISTS stock_exits (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES inventory(id) ON DELETE CASCADE NOT NULL,
    ticket_number VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    created_by VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT,
    priority VARCHAR NOT NULL DEFAULT 'Medium',
    category VARCHAR,
    product_needed VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'Open',
    requester VARCHAR,
    assignee VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE
);
```
