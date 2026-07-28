-- StockIT Database Schema - Updated with improved PurchaseOrders and Documents tables
-- This script creates the exact 6 tables with enhanced schema

-- =====================================================
-- STEP 1: DROP ALL EXISTING TABLES (CLEAN SLATE)
-- =====================================================

DROP TABLE IF EXISTS stock_exits CASCADE;
DROP TABLE IF EXISTS stock_entries CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS purchase_orders CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop any extra unwanted tables
DROP TABLE IF EXISTS inventory_movements CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;

-- =====================================================
-- STEP 2: CREATE TABLES WITH IMPROVED SCHEMA
-- =====================================================

-- Users table (unchanged)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents table (added updated_at)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(100) NOT NULL,
    document_number VARCHAR(255) NOT NULL,
    supplier VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    extracted_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PurchaseOrders table (added description and updated_at)
CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    po_number VARCHAR(255) NOT NULL,
    description TEXT,  -- LLM-generated description for caching
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Inventory table (unchanged)
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER REFERENCES purchase_orders(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    article_number VARCHAR(100) NOT NULL,
    serial_number VARCHAR(255),
    quantity_available INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    received_by VARCHAR(255) NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- StockEntries table (unchanged)
CREATE TABLE stock_entries (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES inventory(id) ON DELETE CASCADE,
    quantity_received INTEGER NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- StockExits table (unchanged)
CREATE TABLE stock_exits (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES inventory(id) ON DELETE CASCADE,
    ticket_number VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- STEP 3: CREATE INDEXES FOR PERFORMANCE
-- =====================================================

-- Users indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Documents indexes
CREATE INDEX idx_documents_supplier ON documents(supplier);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_number ON documents(document_number);

-- Purchase Orders indexes (enhanced for LLM cache lookup)
CREATE UNIQUE INDEX idx_purchase_orders_po_number ON purchase_orders(po_number);
CREATE INDEX idx_purchase_orders_document ON purchase_orders(document_id);
CREATE INDEX idx_purchase_orders_description_null ON purchase_orders(po_number) WHERE description IS NULL;

-- Inventory indexes
CREATE INDEX idx_inventory_category ON inventory(category);
CREATE INDEX idx_inventory_brand ON inventory(brand);
CREATE INDEX idx_inventory_status ON inventory(status);
CREATE INDEX idx_inventory_po ON inventory(purchase_order_id);
CREATE INDEX idx_inventory_article_number ON inventory(article_number);

-- Stock entries indexes
CREATE INDEX idx_stock_entries_inventory ON stock_entries(inventory_id);
CREATE INDEX idx_stock_entries_created_by ON stock_entries(created_by);

-- Stock exits indexes
CREATE INDEX idx_stock_exits_inventory ON stock_exits(inventory_id);
CREATE INDEX idx_stock_exits_ticket ON stock_exits(ticket_number);

-- =====================================================
-- STEP 4: CREATE TRIGGERS FOR UPDATED_AT
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic updated_at updates
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_purchase_orders_updated_at 
    BEFORE UPDATE ON purchase_orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- STEP 5: INSERT SAMPLE DATA
-- =====================================================

-- Sample users for testing
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@stockit.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewDw8GTw/0.lRztS', 'admin'),
('technician1', 'tech1@stockit.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewDw8GTw/0.lRztS', 'technician');

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Show all tables (should be exactly 6)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Show enhanced schema for key tables
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name IN ('documents', 'purchase_orders')
ORDER BY table_name, ordinal_position;