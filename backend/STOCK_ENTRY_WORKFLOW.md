# Stock Entry Workflow Guide

## Overview
The Stock Entry workflow manages stock reception into inventory with strict support for SERIALIZED and BULK tracking modes.

## Step-by-Step Workflow

1. **STEP 1 — Scan Product**: YOLO11 detects equipment category (`Laptop`, `Mouse`, `Keyboard`, `Monitor`, `Headset`).
2. **STEP 2 — Scan Document**: Camera captures invoice image, backend processes with Azure OCR to extract invoice/delivery note text.
3. **STEP 3 — Select Purchase Order**: Technician selects PO.
4. **STEP 4 — Scan Package Label**: Azure Computer Vision OCR extracts article number, serials, and quantities.
5. **STEP 5 — Save**:
   - **SERIALIZED** (`Laptop`, `Monitor`):
     - Validates serial numbers.
     - Creates 1 inventory row per physical item (`quantity_available = 1`, `tracking_type = SERIALIZED`).
     - Creates 1 `stock_entries` row per asset.
     - Increments `products.stock_on_hand` by received quantity.
   - **BULK** (`Headset`, `Mouse`, `Keyboard`):
     - Creates or updates matching bulk row (`quantity_available += quantity`, `tracking_type = BULK`).
     - Creates 1 `stock_entries` row with `quantity_received = quantity`.
     - Increments `products.stock_on_hand` by received quantity.