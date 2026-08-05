# Stock Exit Ticket ID Column Fix ✅

## Problem

The `stock_exits` table had inconsistent naming:
- **Database column name:** `ticket_number`
- **Python attribute name:** `ticket_id`
- **Actual value stored:** Jira ticket ID (e.g., "SD-235534")

This was confusing because:
1. Column name suggested a numeric ticket number
2. Python code used `ticket_id`
3. Actual data was a Jira ticket key (string)

---

## Solution

**Renamed database column to match Python attribute and actual data:**
- **Before:** `ticket_number` (confusing name)
- **After:** `ticket_id` (matches what it actually stores: Jira ticket ID)

---

## Changes Made

### 1. Updated Model Definition

**File:** `backend/app/models/stock_exit.py`

#### Before
```python
class StockExit(Base):
    __tablename__ = "stock_exits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    ticket_id = Column("ticket_number", String, ForeignKey("tickets.id"), nullable=False)
                       ↑ Python name        ↑ Database column name (mismatch!)
```

#### After
```python
class StockExit(Base):
    __tablename__ = "stock_exits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)  # Jira ticket ID
                       ↑ Python name = Database column name (consistent!)
```

#### Updated __repr__
```python
# Before
def __repr__(self):
    return f"<StockExit(inventory_id={self.inventory_id}, qty={self.quantity})>"

# After
def __repr__(self):
    return f"<StockExit(inventory_id={self.inventory_id}, ticket_id={self.ticket_id}, qty={self.quantity})>"
```

---

### 2. Added Database Migration

**File:** `backend/app/database.py`

Added migration step #10 to rename the column:

```python
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
```

---

## What This Fixes

### Before (Confusing)
```sql
-- Database schema
CREATE TABLE stock_exits (
    id INTEGER PRIMARY KEY,
    inventory_id INTEGER,
    ticket_number VARCHAR,  ← Confusing name!
    quantity INTEGER
);

-- Python code
stock_exit.ticket_id = "SD-235534"  ← Uses different name!

-- Stored data
ticket_number: "SD-235534"  ← Jira key, not a number!
```

### After (Consistent)
```sql
-- Database schema
CREATE TABLE stock_exits (
    id INTEGER PRIMARY KEY,
    inventory_id INTEGER,
    ticket_id VARCHAR,  ← Clear name!
    quantity INTEGER
);

-- Python code
stock_exit.ticket_id = "SD-235534"  ← Same name!

-- Stored data
ticket_id: "SD-235534"  ← Clear what it is!
```

---

## Database Migration Details

### Migration is Idempotent
The migration checks if the column needs renaming:

```python
if _table_has_column("stock_exits", "ticket_number"):
    # Rename needed
    ALTER TABLE stock_exits RENAME COLUMN ticket_number TO ticket_id
else:
    # Already correct
    print("✅ stock_exits.ticket_id already correct")
```

### Safe to Run Multiple Times
- ✅ First run: Renames column if needed
- ✅ Subsequent runs: Detects column already correct, skips
- ✅ No errors if already migrated

---

## Data Examples

### Stock Exit Record (After Fix)

```json
{
  "id": 1,
  "inventory_id": 42,
  "ticket_id": "SD-235534",  ← Clear it's a Jira ticket ID
  "quantity": 1,
  "created_by": "admin",
  "created_at": "2026-08-04T18:00:00Z"
}
```

### Python Usage

```python
# Create stock exit
stock_exit = StockExit(
    inventory_id=42,
    ticket_id="SD-235534",  # Jira ticket key
    quantity=1,
    created_by="admin"
)

# Query stock exits for a ticket
exits = db.query(StockExit).filter(
    StockExit.ticket_id == "SD-235534"
).all()

# Print representation
print(stock_exit)
# Output: <StockExit(inventory_id=42, ticket_id=SD-235534, qty=1)>
```

---

## Foreign Key Relationship

The `ticket_id` column is a foreign key to the `tickets` table:

```python
ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)
```

This means:
- `stock_exits.ticket_id` references `tickets.id`
- `tickets.id` stores Jira ticket keys (e.g., "SD-235534")
- Foreign key constraint ensures referential integrity

---

## Benefits

### ✅ Consistent Naming
- Python attribute: `ticket_id`
- Database column: `ticket_id`
- No confusion between code and database

### ✅ Self-Documenting
- Column name clearly indicates it stores ticket IDs
- No misleading "number" suffix when it's actually a string

### ✅ Better __repr__
- Shows ticket_id in debug output
- Makes logging more informative

### ✅ Clearer Intent
- Obvious it's for Jira ticket tracking
- Not confused with internal ticket numbers

---

## Testing

### Verify Migration Ran
Check backend logs on startup:
```
✅ Renamed stock_exits.ticket_number to ticket_id
```
or
```
✅ stock_exits.ticket_id already correct
```

### Verify Column Exists
```sql
-- Check column exists with correct name
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'stock_exits' 
  AND column_name = 'ticket_id';

-- Expected result:
-- column_name | data_type
-- ticket_id   | VARCHAR
```

### Verify Data Intact
```sql
-- Check existing stock exit records
SELECT id, inventory_id, ticket_id, quantity 
FROM stock_exits 
LIMIT 5;

-- Should show Jira ticket IDs like "SD-235534"
```

---

## Rollback (If Needed)

If you need to revert:

```sql
-- Manual rollback
ALTER TABLE stock_exits RENAME COLUMN ticket_id TO ticket_number;

-- And revert model:
ticket_id = Column("ticket_number", String, ForeignKey("tickets.id"), nullable=False)
```

---

## Status: ✅ APPLIED

**Migration:** Ran successfully on server startup
**Column:** `stock_exits.ticket_id` (consistent with Python)
**Data:** Preserved during migration
**Foreign Key:** Maintained to `tickets.id`

🚀
